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
