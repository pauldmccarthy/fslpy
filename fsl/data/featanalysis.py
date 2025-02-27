#!/usr/bin/env python
#
# featanalysis.py - Utility functions for loading/querying the contents of
# a FEAT analysis directory.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a few utility functions for loading/querying the
contents of a FEAT analysis directory. They are primarily for use by the
:class:`.FEATImage` class, but are available for other uses if needed. The
following functions are provided:

.. autosummary::
   :nosignatures:

   isFEATImage
   isFEATDir
   hasStats
   hasMelodicDir
   getAnalysisDir
   getTopLevelAnalysisDir
   isFirstLevelAnalysis
   loadDesign
   loadContrasts
   loadFTests
   loadFsf
   loadSettings
   getThresholds
   loadClusterResults
   loadFEATDesignFile


The following functions return the names of various files of interest:

.. autosummary::
   :nosignatures:

   getDataFile
   getResidualFile
   getMelodicFile
   getPEFile
   getCOPEFile
   getZStatFile
   getZFStatFile
   getClusterMaskFile
   getFClusterMaskFile
"""


import                   collections
import                   io
import                   logging
import os.path        as op
import numpy          as np

import fsl.utils.path       as fslpath
import fsl.transform.affine as affine
from . import image         as fslimage
from . import                  featdesign


log = logging.getLogger(__name__)


def isFEATImage(path):
    """Returns ``True`` if the given path looks like it is the input data to
    a FEAT analysis, ``False`` otherwise.
    """

    try:
        path = fslimage.addExt(path, mustExist=True)
    except fslimage.PathError:
        return False

    dirname  = op.dirname( path)
    filename = op.basename(path)

    return filename.startswith('filtered_func_data') and isFEATDir(dirname)


def isFEATDir(path):
    """Returns ``True`` if the given path looks like a FEAT directory, or
    looks like the input data for a FEAT analysis, ``False`` otherwise.  A
    FEAT directory:

     - Must be named ``*.feat``.
     - Must contain a file called ``filtered_func_data.nii.gz``.
     - Must contain a file called ``design.fsf``.
     - Must contain a file called ``design.mat``.
     - Must contain a file called ``design.con``.

    :arg path: A file / directory path.
    """

    path = op.abspath(path)

    if op.isdir(path): dirname = path
    else:              dirname = op.dirname(path)

    if not dirname.endswith('.feat'):
        return False

    try:
        fslimage.addExt(op.join(dirname, 'filtered_func_data'), mustExist=True)
    except fslimage.PathError:
        return False

    if not op.exists(op.join(dirname, 'design.fsf')): return False
    if not op.exists(op.join(dirname, 'design.mat')): return False
    if not op.exists(op.join(dirname, 'design.con')): return False

    return True


def hasStats(featdir):
    """Returns ``True`` if it looks like statistics have been calculated
    for the given FEAT analysis, ``False`` otherwise.
    """

    try:
        getZStatFile(featdir, 0)
        return True
    except fslimage.PathError:
        return False


def hasMelodicDir(featdir):
    """Returns ``True`` if the data for the given FEAT directory has had
    MELODIC run on it, ``False`` otherwise.
    """
    return op.exists(getMelodicFile(featdir))


def getAnalysisDir(path):
    """If the given path is contained within a FEAT directory, the path
    to that FEAT directory is returned. Otherwise, ``None`` is returned.
    """
    featdir = fslpath.deepest(path, ['.feat'])

    if featdir is not None and isFEATDir(featdir):
        return featdir

    return None


def getTopLevelAnalysisDir(path):
    """If the given path is contained within a hierarchy of FEAT or MELODIC
    directories, the path to the highest-level (i.e. the shallowest in the
    file system) directory is returned. Otherwise, ``None`` is returned.
    """
    return fslpath.shallowest(path, ['.ica', '.gica', '.feat', '.gfeat'])


def getReportFile(featdir):
    """Returns the path to the FEAT report index file, or ``None`` if there
    is no report.
    """

    report = op.join(featdir, 'report.html')
    if op.exists(report): return report
    else:                 return None


def loadContrasts(featdir):
    """Loads the contrasts from a FEAT directory. Returns a tuple containing:

      - A list of names, one for each contrast.

      - A list of contrast vectors (each of which is a list itself).

    :arg featdir: A FEAT directory.
    """

    filename = op.join(featdir, 'design.con')

    log.debug('Loading FEAT contrasts from %s', filename)

    try:
        designcon    = loadFEATDesignFile(filename)
        contrasts    = np.genfromtxt(io.StringIO(designcon['Matrix']), ndmin=2)
        numContrasts = int(designcon['NumContrasts'])
        names        = []

        if numContrasts != contrasts.shape[0]:
            raise RuntimeError(f'Matrix shape {contrasts.shape} does not '
                               f'match number of contrasts {numContrasts}')

        contrasts = [list(row) for row in contrasts]

        for i in range(numContrasts):
            cname = designcon.get(f'ContrastName{i + 1}', '')
            if cname == '':
                cname = f'{i + 1}'
            names.append(cname)

    except Exception as e:
        log.debug('Error reading %s: %s', filename, e, exc_info=True)
        raise RuntimeError(f'{filename} does not appear '
                           'to be a valid design.con file') from e

    return names, contrasts


def loadFTests(featdir):
    """Loads F-tests from a FEAT directory. Returns a list of f-test vectors
    (each of which is a list itself), where each vector contains a 1 or a 0
    denoting the contrasts included in the F-test.

    :arg featdir: A FEAT directory.
    """

    filename = op.join(featdir, 'design.fts')

    if not op.exists(filename):
        return []

    log.debug('Loading FEAT F-tests from %s', filename)

    try:
        desfts = loadFEATDesignFile(filename)
        ftests = np.genfromtxt(io.StringIO(desfts['Matrix']), ndmin=2)
        ncols  = int(desfts['NumWaves'])
        nrows  = int(desfts['NumContrasts'])

        if ftests.shape != (nrows, ncols):
            raise RuntimeError(f'Matrix shape {ftests.shape} does not match '
                               f'number of EVs/FTests ({ncols}, {nrows})')

        ftests = [list(row) for row in ftests]

    except Exception as e:
        log.debug('Error reading %s: %s', filename, e, exc_info=True)
        raise RuntimeError(f'{filename} does not appear '
                           'to be a valid design.fts file') from e

    return ftests


def loadFsf(designfsf):
    """Loads the analysis settings from a text file (.fsf) used to configure
    FEAT.

    Returns a dict containing the settings specified in the file

    :arg designfsf: A .fsf file.
    """

    settings  = collections.OrderedDict()

    log.debug('Loading FEAT settings from %s', designfsf)

    with open(designfsf, 'rt') as f:

        for line in f.readlines():
            line = line.strip()

            if not line.startswith('set '):
                continue

            tkns = line.split(None, 2)

            key = tkns[1].strip()
            val = tkns[2].strip(' \'"')

            if key.startswith('fmri(') and key.endswith(')'):
                key = key[5:-1]

            settings[key] = val

    return settings


def loadSettings(featdir):
    """Loads the analysis settings from a FEAT directory.

    Returns a dict containing the settings specified in the ``design.fsf``
    file within the directory

    :arg featdir: A FEAT directory.
    """

    designfsf = op.join(featdir, 'design.fsf')

    return loadFsf(designfsf)


def loadDesign(featdir, settings):
    """Loads the design matrix from a FEAT directory.

    :arg featdir:  A FEAT directory.

    :arg settings: Dictionary containing FEAT settings (see
                   :func:`loadSettings`).

    :returns:      a :class:`.FEATFSFDesign` instance which represents the
                   design matrix.
    """
    return featdesign.FEATFSFDesign(featdir, settings)


def getThresholds(settings):
    """Given a FEAT settings dictionary, returns a dictionary of
    ``{stat : threshold}`` mappings, containing the thresholds used
    in the FEAT statistical analysis.

    The following keys will be present. Threshold values will be ``None``
    if the respective statistical thresholding was not carried out:

      - ``p``: P-value thresholding
      - ``z``: Z-statistic thresholding

    :arg settings: A FEAT settings dictionary (see :func:`loadSettings`).
    """
    p = settings.get('prob_thresh', None)
    z = settings.get('z_thresh',    None)

    if p is not None: p = float(p)
    if z is not None: z = float(z)

    return {'p' : p, 'z' : z}


def isFirstLevelAnalysis(settings):
    """Returns ``True`` if the FEAT analysis described by ``settings``
    is a first level analysis, ``False`` otherwise.

    :arg settings: A FEAT settings dictionary (see :func:`loadSettings`).
    """
    return settings['level'] == '1'


def loadClusterResults(featdir, settings, contrast, ftest=False):
    """If cluster thresholding was used in the FEAT analysis, this function
    will load and return the cluster results for the specified (0-indexed)
    contrast or f-test.

    If there are no cluster results for the given contrast/f-test, ``None``
    is returned.

    An error will be raised if the cluster file cannot be parsed.

    :arg featdir:  A FEAT directory.
    :arg settings: A FEAT settings dictionary.
    :arg contrast: 0-indexed contrast or f-test number.
    :arg ftest:    If ``False`` (default), return cluster results for
                   the contrast numbered ``contrast``. Otherwise, return
                   cluster results for the f-test numbered ``contrast``.

    :returns:      A list of ``Cluster`` instances, each of which contains
                   information about one cluster. A ``Cluster`` object has the
                   following attributes:

                     ============ =========================================
                     ``index``    Cluster index.
                     ``nvoxels``  Number of voxels in cluster.
                     ``p``        Cluster p value.
                     ``logp``     :math:`-log_{10}` of the cluster P value.
                     ``zmax``     Maximum Z value in cluster.
                     ``zmaxx``    X voxel coordinate of maximum Z value.
                     ``zmaxy``    Y voxel coordinate of maximum Z value.
                     ``zmaxz``    Z voxel coordinate of maximum Z value.
                     ``zcogx``    X voxel coordinate of cluster centre of
                                  gravity.
                     ``zcogy``    Y voxel coordinate of cluster centre of
                                  gravity.
                     ``zcogz``    Z voxel coordinate of cluster centre of
                                  gravity.
                     ``copemax``  Maximum COPE value in cluster (not
                                  present for f-tests).
                     ``copemaxx`` X voxel coordinate of maximum COPE value
                                  (not present for f-tests).
                     ``copemaxy`` Y voxel coordinate of maximum COPE value.
                                  (not present for f-tests).
                     ``copemaxz`` Z voxel coordinate of maximum COPE value.
                                  (not present for f-tests).
                     ``copemean`` Mean COPE of all voxels in the cluster.
                                  (not present for f-tests).
                     ============ =========================================
    """

    # Cluster files are named like
    # 'cluster_zstatX.txt', where
    # X is the COPE number. And
    # the ZMax/COG etc coordinates
    # are usually in voxel coordinates
    coordXform  = np.eye(4)

    if ftest: prefix = 'cluster_zfstat'
    else:     prefix = 'cluster_zstat'

    clusterFile = op.join(featdir, f'{prefix}{contrast + 1}.txt')

    if not op.exists(clusterFile):

        # If the analysis was performed in standard
        # space (e.g. a higher level group analysis),
        # the cluster file will instead be called
        # 'cluster_zstatX_std.txt', so we'd better
        # check for that too.
        clusterFile = op.join(featdir, f'{prefix}{contrast + 1}_std.txt')

        if not op.exists(clusterFile):
            return None

        # In higher level analysis run in some standard
        # space, the cluster coordinates are in standard
        # space. We transform them to voxel coordinates.
        # later on.
        coordXform = fslimage.Image(getDataFile(featdir)).worldToVoxMat

    # The cluster.txt file is converted
    # into a list of Cluster objects,
    # each of which encapsulates
    # information about one cluster.
    class Cluster(object):
        def __init__(self, **kwargs):
            for name, val in kwargs.items():

                attrName = colmap[name]
                if val is not None:
                    val = float(val)

                setattr(self, attrName, val)

            # if cluster thresholding was not used,
            # the cluster table will not contain
            # P values.
            if not hasattr(self, 'p'):    self.p    = 1.0
            if not hasattr(self, 'logp'): self.logp = 0.0

            # F-test cluster results will not have
            # COPE-* results
            if not hasattr(self, 'copemax'):  self.copemax  = np.nan
            if not hasattr(self, 'copemaxx'): self.copemaxx = np.nan
            if not hasattr(self, 'copemaxy'): self.copemaxy = np.nan
            if not hasattr(self, 'copemaxz'): self.copemaxz = np.nan
            if not hasattr(self, 'copemean'): self.copemean = np.nan

    # This dict provides a mapping between
    # Cluster object attribute names, and
    # the corresponding column name in the
    # cluster.txt file.
    colmap = {
        'Cluster Index'    : 'index',
        'Voxels'           : 'nvoxels',
        'P'                : 'p',
        '-log10(P)'        : 'logp',
        'Z-MAX'            : 'zmax',
        'Z-MAX X (vox)'    : 'zmaxx',
        'Z-MAX Y (vox)'    : 'zmaxy',
        'Z-MAX Z (vox)'    : 'zmaxz',
        'Z-COG X (vox)'    : 'zcogx',
        'Z-COG Y (vox)'    : 'zcogy',
        'Z-COG Z (vox)'    : 'zcogz',
        'Z-MAX X (mm)'     : 'zmaxx',
        'Z-MAX Y (mm)'     : 'zmaxy',
        'Z-MAX Z (mm)'     : 'zmaxz',
        'Z-COG X (mm)'     : 'zcogx',
        'Z-COG Y (mm)'     : 'zcogy',
        'Z-COG Z (mm)'     : 'zcogz',
        'COPE-MAX'         : 'copemax',
        'COPE-MAX X (vox)' : 'copemaxx',
        'COPE-MAX Y (vox)' : 'copemaxy',
        'COPE-MAX Z (vox)' : 'copemaxz',
        'COPE-MAX X (mm)'  : 'copemaxx',
        'COPE-MAX Y (mm)'  : 'copemaxy',
        'COPE-MAX Z (mm)'  : 'copemaxz',
        'COPE-MEAN'        : 'copemean'}

    log.debug('Loading cluster results for contrast %s from %s',
              contrast, clusterFile)

    with open(clusterFile, 'rt') as f:

        # Get every line in the file,
        # removing leading/trailing
        # whitespace, and discarding
        # empty lines
        lines = f.readlines()

    lines = [line.strip() for line in lines]
    lines = [line         for line in lines if line != '']

    # the first line should contain column
    # names, and each other line should
    # contain the data for one cluster
    colNames     = lines[0]
    clusterLines = lines[1:]

    # each line should be tab-separated
    colNames     =  colNames.split('\t')
    clusterLines = [cl      .split('\t') for cl in clusterLines]

    # Turn each cluster line into a Cluster
    # instance. An error will be raised if the
    # columm names are unrecognised (i.e. not
    # in the colmap above), or if the file is
    # poorly formed.
    clusters = [Cluster(**dict(zip(colNames, cl))) for cl in clusterLines]

    # Make sure all coordinates are in voxels -
    # for first level analyses, the coordXform
    # will be an identity transform (the coords
    # are already in voxels). But for higher
    # level, the coords are in mm, and need to
    # be transformed to voxels.
    for c in clusters:

        zmax    = [c.zmaxx,    c.zmaxy,    c.zmaxz]
        zcog    = [c.zcogx,    c.zcogy,    c.zcogz]
        copemax = [c.copemaxx, c.copemaxy, c.copemaxz]

        zmax    = affine.transform([zmax],    coordXform)[0]
        zcog    = affine.transform([zcog],    coordXform)[0]
        copemax = affine.transform([copemax], coordXform)[0]

        c.zmaxx,    c.zmaxy,    c.zmaxz    = zmax
        c.zcogx,    c.zcogy,    c.zcogz    = zcog
        c.copemaxx, c.copemaxy, c.copemaxz = copemax

    return clusters


def loadFEATDesignFile(filename):
    """Load a FEAT design file, e.g. ``design.mat``, ``design.con``, ``design.fts``.

    These files contain key-value pairs, and are formatted according to an
    undocumented structure where each key is of the form "/KeyName", and is
    followed immediately by a whitespace character, and then the value.

    :arg filename: File to load
    :returns:      A dictionary of key-value pairs. The values are all left
                   as strings.
    """

    fields = {}

    with open(filename, 'rt') as f:
        content = f.read()

    content = content.split('/')
    for line in content:
        line = line.strip()
        if line == '':
            continue

        tokens = line.split(maxsplit=1)
        if len(tokens) == 1:
            name, value = tokens[0], ''
        else:
            name, value = tokens

        fields[name] = value

    return fields


def getDataFile(featdir):
    """Returns the name of the file in the FEAT directory which contains
    the model input data (typically called ``filtered_func_data.nii.gz``).

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir: A FEAT directory.
    """
    datafile = op.join(featdir, 'filtered_func_data')
    return fslimage.addExt(datafile, mustExist=True)


def getMelodicFile(featdir):
    """Returns the name of the file in the FEAT results which contains the
    melodic components (if melodic ICA was performed as part of the FEAT
    analysis). This file can be loaded as a :class:`.MelodicImage`.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.
    """
    melfile = op.join(featdir, 'filtered_func_data.ica', 'melodic_IC')
    return fslimage.addExt(melfile, mustExist=True)


def getResidualFile(featdir):
    """Returns the name of the file in the FEAT results which contains
    the model fit residuals (typically called ``res4d.nii.gz``).

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir: A FEAT directory.
    """
    resfile = op.join(featdir, 'stats', 'res4d')
    return fslimage.addExt(resfile, mustExist=True)


def getPEFile(featdir, ev):
    """Returns the path of the PE file for the specified EV.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir: A FEAT directory.
    :arg ev:      The EV number (0-indexed).
    """
    pefile = op.join(featdir, 'stats', f'pe{ev + 1}')
    return fslimage.addExt(pefile, mustExist=True)


def getCOPEFile(featdir, contrast):
    """Returns the path of the COPE file for the specified contrast.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir:  A FEAT directory.
    :arg contrast: The contrast number (0-indexed).
    """
    copefile = op.join(featdir, 'stats', f'cope{contrast + 1}')
    return fslimage.addExt(copefile, mustExist=True)


def getZStatFile(featdir, contrast):
    """Returns the path of the Z-statistic file for the specified contrast.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir:  A FEAT directory.
    :arg contrast: The contrast number (0-indexed).
    """
    zfile = op.join(featdir, 'stats', f'zstat{contrast + 1}')
    return fslimage.addExt(zfile, mustExist=True)


def getZFStatFile(featdir, ftest):
    """Returns the path of the Z-statistic file for the specified F-test.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir: A FEAT directory.
    :arg ftest:   The F-test number (0-indexed).
    """
    zffile = op.join(featdir, 'stats', f'zfstat{ftest + 1}')
    return fslimage.addExt(zffile, mustExist=True)


def getClusterMaskFile(featdir, contrast):
    """Returns the path of the cluster mask file for the specified contrast.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir:  A FEAT directory.
    :arg contrast: The contrast number (0-indexed).
    """
    mfile = op.join(featdir, f'cluster_mask_zstat{contrast + 1}')
    return fslimage.addExt(mfile, mustExist=True)


def getFClusterMaskFile(featdir, ftest):
    """Returns the path of the cluster mask file for the specified f-test.

    Raises a :exc:`~fsl.utils.path.PathError` if the file does not exist.

    :arg featdir:  A FEAT directory.
    :arg contrast: The f-test number (0-indexed).
    """
    mfile = op.join(featdir, f'cluster_mask_zfstat{ftest + 1}')
    return fslimage.addExt(mfile, mustExist=True)
