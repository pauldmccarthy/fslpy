#!/usr/bin/env python
#
# featresults.py - Utility functions for loading/querying the contents of
# a FEAT analysis directory.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a few utility functions for loading/querying the
contents of a FEAT analysis directory.
"""


import            logging
import            glob
import os.path as op
import numpy   as np


log = logging.getLogger(__name__)


def isFEATDir(path):
    """Returns ``True`` if the given path looks like a FEAT directory, or
    looks like the input data for a FEAT analysis, ``False`` otherwise.
    """


    dirname, filename = op.split(path)

    featDir   = getFEATDir(dirname)
    isfeatdir = featDir is not None

    try:
        hasdesfsf = op.exists(op.join(featDir, 'design.fsf'))
        hasdesmat = op.exists(op.join(featDir, 'design.mat'))
        hasdescon = op.exists(op.join(featDir, 'design.con'))
        
        isfeat    = (isfeatdir and
                     hasdesmat and
                     hasdescon and
                     hasdesfsf)

        return isfeat
    
    except:
        return False


def getFEATDir(path):

    sufs     = ['.feat', '.gfeat']
    idxs     = [(path.rfind(s), s) for s in sufs]
    idx, suf = max(idxs, key=lambda (i, s): i)

    if idx == -1:
        return None

    idx  += len(suf)
    path  = path[:idx]

    if path.endswith(suf) or path.endswith('{}{}'.format(suf, op.sep)):
        return path
                                           
    return None


def loadDesign(featdir):
    """Loads the design matrix from a FEAT folder.

    Returns a ``numpy`` array containing the design matrix data, where the
    first dimension corresponds to the data points, and the second to the EVs.
    """

    matrix    = None 
    designmat = op.join(featdir, 'design.mat')

    log.debug('Loading FEAT design matrix from {}'.format(designmat))

    with open(designmat, 'rt') as f:

        while True:
            line = f.readline()
            if line.strip() == '/Matrix':
                break

        matrix = np.loadtxt(f)

    if matrix is None or matrix.size == 0:
        raise RuntimeError('{} does not appear to be a '
                           'valid design.mat file'.format(designmat))

    return matrix


def loadContrasts(featdir):
    """Loads the contrasts from a FEAT folder. Returns a tuple containing:
    
      - A dictionary of ``{contrastnum : name}`` mappings
    
      - A list of contrast vectors (each of which is a list itself).
    """

    matrix       = None
    numContrasts = 0
    names        = {}
    designcon    = op.join(featdir, 'design.con')

    log.debug('Loading FEAT contrasts from {}'.format(designcon))
    
    with open(designcon, 'rt') as f:

        while True:
            line = f.readline().strip()

            if line.startswith('/ContrastName'):
                tkns       = line.split(None, 1)
                num        = [c for c in tkns[0] if c.isdigit()]
                num        = int(''.join(num))
                name       = tkns[1].strip()
                names[num] = name

            elif line.startswith('/NumContrasts'):
                numContrasts = int(line.split()[1])

            elif line == '/Matrix':
                break

        matrix = np.loadtxt(f)

    if matrix       is None             or \
       numContrasts != matrix.shape[0]:
        raise RuntimeError('{} does not appear to be a '
                           'valid design.con file'.format(designcon))

    # Fill in any missing contrast names
    if len(names) != numContrasts:
        for i in range(numContrasts):
            if i + 1 not in names:
                names[i + 1] = str(i + 1)

    names     = [names[c + 1] for c in range(numContrasts)]
    contrasts = []

    for row in matrix:
        contrasts.append(list(row))

    return names, contrasts


def loadSettings(featdir):
    """Loads the analysis settings from a a FEAT folder.

    Returns a dict containing the settings specified in the given file.
    """

    settings  = {}
    designfsf = op.join(featdir, 'design.fsf')

    log.debug('Loading FEAT settings from {}'.format(designfsf))

    with open(designfsf, 'rt') as f:

        for line in f.readlines():
            line = line.strip()

            if not line.startswith('set '):
                continue

            tkns = line.split(None, 2)

            key = tkns[1].strip()
            val = tkns[2].strip().strip("'").strip('"')

            if key.startswith('fmri(') and key.endswith(')'):
                key = key[5:-1]

            settings[key] = val
    
    return settings


def getThresholds(settings):
    return {
        'p' : settings.get('prob_thresh', None),
        'z' : settings.get('z_thresh',    None)
    }


def loadClusterResults(featdir, settings, contrast):
    """If cluster thresholding was used in the FEAT analysis, this function
    will load and return the cluster results for the specified contrast
    (which is assumed to be 0-indexed).

    If there are no cluster results for the given contrast,
    ``None`` is returned.

    An error will be raised if the cluster file cannot be parsed.
    """

    # This dict provides a mapping between 
    # Cluster object (see below) attribute
    # names, and the corresponding column
    # name in the cluster.txt file. And the
    # value type is thrown in as well, for
    # good measure.
    colmap = {
        'Cluster Index'    : ('index',    int),  
        'Voxels'           : ('nvoxels',  int), 
        'P'                : ('p',        float), 
        '-log10(P)'        : ('logp',     float), 
        'Z-MAX'            : ('zmax',     float), 
        'Z-MAX X (vox)'    : ('zmaxx',    int), 
        'Z-MAX Y (vox)'    : ('zmaxy',    int), 
        'Z-MAX Z (vox)'    : ('zmaxz',    int), 
        'Z-COG X (vox)'    : ('zcogx',    float), 
        'Z-COG Y (vox)'    : ('zcogy',    float), 
        'Z-COG Z (vox)'    : ('zcogz',    float),
        'COPE-MAX'         : ('copemax',  float),
        'COPE-MAX X (vox)' : ('copemaxx', int), 
        'COPE-MAX Y (vox)' : ('copemaxy', int), 
        'COPE-MAX Z (vox)' : ('copemaxz', int), 
        'COPE-MEAN'        : ('copemean', float)}

    # The cluster.txt file is converted
    # into a list of Cluster objects,
    # each of which encapsulates
    # information about one cluster.
    class Cluster(object):
        def __init__(self, **kwargs):
            for name, val in kwargs.items():
                
                attrName, atype = colmap[name]
                if val is not None:
                    val = atype(val)
                    
                setattr(self, attrName, val)

    clusterFile = op.join(featdir, 'cluster_zstat{}.txt'.format(contrast + 1))

    if not op.exists(clusterFile):
        return None

    log.debug('Loading cluster results for contrast {} from {}'.format(
        contrast, clusterFile))

    # An error will be raised if the
    # cluster file does not exist (e.g.
    # if the specified contrast index
    # is invalid)
    with open(clusterFile, 'rt') as f:

        # Get every line in the file,
        # removing leading/trailing
        # whitespace, and discarding
        # empty lines
        lines = f.readlines()
        lines = [l.strip() for l in lines]
        lines = filter(lambda l: l != '', lines)

        # the first line should contain column
        # names, and each other line should
        # contain the data for one cluster
        colNames     = lines[0]
        clusterLines = lines[1:]

        # each line should be tab-separated
        colNames     =  colNames.split('\t')
        clusterLines = [cl      .split('\t') for cl in clusterLines]

        # No clusters
        if len(clusterLines) == 0:
            return None

        # Turn each cluster line into a
        # Cluster instance. An error will
        # be raised if the columm names
        # are unrecognised (i.e. not in
        # the colmap above), or if the
        # file is poorly formed.
        return [Cluster(**dict(zip(colNames, cl))) for cl in clusterLines]


def getDataFile(featdir):
    """Returns the name of the file in the FEAT results which contains
    the model input data (typically called ``filtered_func_data.nii.gz``).
    """
    
    # Assuming here that there is only
    # one file called filtered_func_data.*
    return glob.glob((op.join(featdir, 'filtered_func_data.*')))[0]


def getResidualFile(featdir):
    """Returns the name of the file in the FEAT results which contains
    the model fit residuals (typically called ``res4d.nii.gz``).
    """
    
    # Assuming here that there is only
    # one file called stats/res4d.*
    return glob.glob((op.join(featdir, 'stats', 'res4d.*')))[0]

    
def getPEFile(featdir, ev):
    """Returns the path of the PE file for the specified ``ev``, which is
    assumed to be 0-indexed. 
    """

    pefile = op.join(featdir, 'stats', 'pe{}.*'.format(ev + 1))
    return glob.glob(pefile)[0]


def getCOPEFile(featdir, contrast):
    """Returns the path of the COPE file for the specified ``contrast``, which
    is assumed to be 0-indexed. 
    """
    copefile = op.join(featdir, 'stats', 'cope{}.*'.format(contrast + 1))
    return glob.glob(copefile)[0]


def getZStatFile(featdir, contrast):
    """Returns the path of the Z-statistic file for the specified
    ``contrast``, which is assumed to be 0-indexed. 
    """
    zfile = op.join(featdir, 'stats', 'zstat{}.*'.format(contrast + 1))
    return glob.glob(zfile)[0]


def getClusterMaskFile(featdir, contrast):
    """Returns the path of the cluster mask file for the specified
    ``contrast``, which is assumed to be 0-indexed. 
    """
    mfile = op.join(featdir, 'cluster_mask_zstat{}.*'.format(contrast + 1))
    return glob.glob(mfile)[0]


def getEVNames(settings):
    """Returns the names of every EV in the FEAT analysis which has the given
    ``settings`` (see the :func:`loadSettings` function).

    An error of some sort will be raised if the EV names cannot be determined
    from the FEAT settings.
    """

    numEVs = int(settings['evs_real'])

    titleKeys = filter(lambda s: s.startswith('evtitle'),  settings.keys())
    derivKeys = filter(lambda s: s.startswith('deriv_yn'), settings.keys())

    def _cmp(key1, key2):
        key1 = ''.join([c for c in key1 if c.isdigit()])
        key2 = ''.join([c for c in key2 if c.isdigit()])

        return cmp(int(key1), int(key2))

    titleKeys = sorted(titleKeys, cmp=_cmp)
    derivKeys = sorted(derivKeys, cmp=_cmp)
    evnames  = []

    for titleKey, derivKey in zip(titleKeys, derivKeys):

        # Figure out the ev number from
        # the design.fsf key - skip over
        # 'evtitle' (an offset of 7)
        evnum = int(titleKey[7:])

        # Sanity check - the evnum
        # for the deriv_yn key matches
        # that for the evtitle key
        if evnum != int(derivKey[8:]):
            raise RuntimeError('design.fsf seem to be corrupt')

        title = settings[titleKey]
        deriv = settings[derivKey]

        if deriv == '0':
            evnames.append(title)
        else:
            evnames.append(title)
            evnames.append('{} - {}'.format(title, 'temporal derivative'))

    if len(evnames) != numEVs:
        raise RuntimeError('The number of EVs in design.fsf does not '
                           'match the number of EVs in design.mat')

    return evnames
