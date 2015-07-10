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


import            glob
import os.path as op
import numpy   as np


def isFEATDir(path):
    """Returns ``True`` if the given path looks like a FEAT directory, or
    looks like the input data for a FEAT analysis, ``False`` otherwise.
    """

    if op.isfile(path):

        dirname, filename = op.splitext(path)

        if not filename.startswith('filtered_func_data'):
            return False

    dirname = path
    keys    = ['.feat',
               '.gfeat',
               '.feat{}' .format(op.sep),
               '.gfeat{}'.format(op.sep)]

    isfeatdir = any([path.endswith(k) for k in keys])

    hasdesfsf = op.exists(op.join(dirname, 'design.fsf'))
    hasdesmat = op.exists(op.join(dirname, 'design.mat'))
    hasdescon = op.exists(op.join(dirname, 'design.con'))

    isfeat    = (isfeatdir and
                 hasdesmat and
                 hasdescon and
                 hasdesfsf)
    
    return isfeat


def loadDesign(featdir):
    """Loads the design matrix from a FEAT folder.

    Returns a ``numpy`` array containing the design matrix data, where the
    first dimension corresponds to the data points, and the second to the EVs.
    """

    matrix    = None 
    designmat = op.join(featdir, 'design.mat')

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


def getThresholdType(settings):
    """Returns the type of statistical thresholding used in the FEAT
    analysis described in the given settings dict (see the
    :func:`loadSettings` function).

    Returns a number describing the thresholding approach:

        -1 : Statistical analysis has not been performed
         0 : No thresholding has been performed
         1 : Uncorrected P-value thresholding
         2 : Voxel-corrected thresholding
         3 : Cluster-corrected thresholding
    """

    poststats = int(settings['poststats_yn'])
    threstype = int(settings['thresh'])

    if poststats != 1:
        return -1

    return threstype


def loadClusterResults(featdir, settings, contrast):
    """If cluster thresholding was used in the FEAT analysis, this function
    will load and return the cluster results for the specified contrast
    (which is assumed to be 0-indexed).

    If thresholding has not been performed, or cluster threhsolding was not
    used, ``None`` is returned.
    """

    # poststats_yn != 1 means that
    # stats has not been performed
    # 
    # thres=3 corresponds to
    # cluster thresholding 
    if int(settings['poststats_yn']) != 1 or \
       int(settings['thresh'])       != 3:
        return None
    
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
        'Z-COG X (vox)'    : ('zcogx',    int), 
        'Z-COG Y (vox)'    : ('zcogy',    int), 
        'Z-COG Z (vox)'    : ('zcogz',    int), 
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
            for name, val in kwargs:
                
                attrName, atype = colmap[name]
                if val is not None:
                    val = atype(val)
                    
                setattr(self, attrName, val)

    clusterFile = op.join(featdir, 'cluster_zstat{}.txt'.format(contrast + 1))

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


def getEVNames(settings):
    """Returns the names of every EV in the FEAT analysis which has the given
    ``settings`` (see the :func:`loadSettings` function).
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
