#!/usr/bin/env python
#
# featdesign.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FEATFSFDesign` class, which encapsulates
a FEAT design matrix.


The FEAT design matrix
----------------------


A FEAT design matrix may contain the following types of explanatory variables:

 - *Normal* EVs. This is simply a column in the design matrix, defined by the
   user.

 - Temporal derivative of normal EVs. A column in the design matrix  containing
   the derivative of the previous normal EV. The presence of a temporal
   derivative EV for a given normal EV can be determined by the ``deriv_yn``
   flag in the ``design.fsf`` file.

 - Basis function EV. One or more columns derived from a normal EV
   (``basisfnumN``)

 - Voxelwise EVs (``designVoxelwiseEV<N>.nii.gz``, EV number must be offset by
   temporal derivative EVs)

 - Confound EVs (... ?)

 - Voxelwise confound EVs (``vef.dat`` and ``ven.dat``)

 - Motion parameter EVs (``design.fsf:motionevs``, the last 6 or 24 columns of
   the design matrix [i think])

For each voxelwise EV, the design matrix (in ``design.mat``) contains a
'dummy' column which contains the mean across all voxels.


For voxelwise EVs, the column number (1-indexed) is conatined in the file name
(``<N>`` in the above list entry).  But this number does not take into account
the temporal derivative EVs of regular evs, so you need to offset this number
by the number of TD EVs in the design matrix, which come before the voxelwise
EV.


For voxelwise confound EVs, the column number mappings (1-indexed) are
contained in ``vef.dat`` and ``ven.dat``.


*Original* EV: An EV defined by the user
*Real* EV: A derived EV (either temporal derivative, or derived with
           basis functions).
"""


import            logging
import            collections
import os.path as op
import numpy   as np

from . import          featanalysis
from . import image as fslimage


log = logging.getLogger(__name__)


class FSFError(Exception):
    pass


class EV(object):
    def __init__(self, index, title):
        self.index = index
        self.title = title

        
class NormalEV(EV):
    def __init__(self, realIdx, origIdx, title):
        EV.__init__(self, realIdx, title)
        self.origIndex = origIdx


class TemporalDerivativeEV(NormalEV):
    pass
                          

class BasisFunctionEV(NormalEV):
    pass


class VoxelwiseEV(NormalEV):
    def __init__(self, realIdx, origIdx, title, filename):
        NormalEV.__init__(self, realIdx, origIdx, title)
        self.filename = filename


class ConfoundEV(EV):
    def __init__(self, index, confIndex, title):
        EV.__init__(self, index, title)
        self.confIndex = confIndex
 

class MotionParameterEV(EV):
    def __init__(self, index, motionIndex, title):
        EV.__init__(self, index, title)
        self.motionIndex = motionIndex 


class VoxelwiseConfoundEV(EV):
    def __init__(self, index, voxIndex, title, filename):
        EV.__init__(self, index, title)
        self.voxIndex = voxIndex
        self.filename = filename


class FEATFSFDesign(object):
    """
    """

    
    def __init__(self, featDir, settings, designMatrix):

        # Get some information about the analysis
        version = float(settings['version'])
        level   = int(  settings['level'])

        # Print a warning if we're 
        # using an old version of FEAT
        if version < 6:
            log.warning('Unsupported FEAT version: {}'.format(version))

        # We need to parse the EVS a bit
        # differently depending on whether
        # this is a first level or higher
        # level analysis.
        if level == 1: getEVs = getFirstLevelEVs
        else:          getEVs = getHigherLevelEVs

        self.__settings = collections.OrderedDict(settings.items())
        self.__design   = np.array(designMatrix)
        self.__numEVs   = self.__design.shape[1]
        self.__evs      = getEVs(featDir, self.__settings, self.__design)

        for i, ev in enumerate(self.__evs):

            print 'EV{}: {} [{}]'.format(
                ev.index + 1,
                ev.title,
                type(ev).__name__)

        if len(self.__evs) != self.__numEVs:
            raise FSFError('Number of EVs does not match design.mat')
 
 
    
    def getDesign(self, x, y, z):
        """Returns the design matrix for the specified voxel.
        """

        # if no vox EVs, just
        # return the design
        pass


    def getVoxelEVFile(self, idx):
        return self.__evs[idx].filename

    
    def getVoxelConfoundFile(self, idx):
        return self.__evs[idx].filename



def getFirstLevelEVs(featDir, settings, designMat):

    evs     = []
    origEVs = int(settings['evs_orig'])

    # First, we loop through the EVs that
    # are explicitly defined in design.fsf.
    # This includes 
    #   - normal EVs
    #   - temporal derivative EVs
    #   - basis function EVs
    #   - voxelwise EVs
    for origIdx in range(origEVs):
            
        title    = settings[        'evtitle{}'  .format(origIdx + 1)]
        shape    = int(settings[    'shape{}'    .format(origIdx + 1)])
        convolve = int(settings[    'convolve{}' .format(origIdx + 1)])
        deriv    = int(settings[    'deriv_yn{}' .format(origIdx + 1)])
        basis    = int(settings.get('basisfnum{}'.format(origIdx + 1), -1))

        # Normal EV. This is just a column
        # in the design matrix, defined by
        # the user. 
        if shape != 9:
            evs.append(NormalEV(len(evs), origIdx, title))

        # Voxelwise EV. This is a 'normal' EV
        # defined by the user, with different
        # values for each voxel. The voxelwise
        # values should be contained in the
        # feat directory, in an image called
        # designVoxelwiseEVN, where N is the
        # original EV index.
        else:

            # The addExt function will
            # raise an error if the
            # file does not exist.
            filename = op.join(
                featDir, 'designVoxelwiseEV{}'.format(origIdx + 1))
            filename = fslimage.addExt(filename, True)
            
            evs.append(VoxelwiseEV(len(evs), origIdx, title, filename)) 

        # This EV has been convolved with a set of basis
        # functions. A set of N additional EVs have been
        # added to the design matrix, immediately after
        # the EV, where N is specified by the basisfnumN
        # parameter in design.fsf.
        if convolve in (4, 5, 6):

            if basis == -1:
                raise FSFError('Number of EVs is not specified '
                               'for basis function EV')

            for i in range(basis - 1):
                evs.append(BasisFunctionEV(len(evs), origIdx, title))

        # A temporal derivative EV has been
        # added for this EV - in the design
        # matrix, it is the column immediately
        # after this EV.
        if deriv == 1:
            evs.append(TemporalDerivativeEV(len(evs), origIdx, title))

    # In the design matrix, after all EVs which
    # have been explicilty defined, the rest of
    # the EVs in the design matrix are confounds,
    # in the following order:
    # 
    #   1. Voxelwise confounds
    #   2. Motion parameters
    #   3. Other confounds

    # Any voxelwise confounds are specified
    # in two plain text files - vef.dat
    # contains a comma-separated list of
    # files, and ven.dat contains the column
    # index of this confound in the design
    # matrix (1-indexed). If these files
    # don't exist, then it means that there
    # are no voxelwise confounds.
    #
    # n.b. Even though the indices into the
    # final design matrix are stored in ven.dat,
    # I'm just assuming that the voxelwise
    # confound columns are immediately after
    # the 'real' EVs procesed above, in the
    # order defined in vef.dat.
    voxConfFiles = op.join(featDir, 'vef.dat')
    voxConfLocs  = op.join(featDir, 'ven.dat')
    
    if op.exists(voxConfFiles) and op.exists(voxConfLocs):

        with open(voxConfFiles, 'rt') as vcff:
            voxConfFiles = vcff.read()

        with open(voxConfLocs, 'rt') as vclf:
            voxConfLocs = vclf.read()

        voxConfFiles = voxConfFiles.strip().split(',')
        voxConfLocs  = voxConfLocs .strip().split(',')

        if len(voxConfFiles) != len(voxConfLocs):
            raise FSFError('vef.dat does not match ven.dat')

        # An error will be raised if any of
        # the files in vef.dat do not exist,
        # or if any of the indices in
        # ven.dat are not integers.
        voxConfFiles = [op.join(featDir, f)      for f in voxConfFiles]
        voxConfFiles = [fslimage.addExt(f, True) for f in voxConfFiles]
        voxConfLocs  = [int(i) for i in voxConfLocs]

        # Check to see if my assumption
        # above, about the voxelwise
        # confound EV locations, holds
        startIdx = len(evs) + 1
        if voxConfLocs != range(startIdx, startIdx + len(voxConfFiles)):
            raise FSFError('Unsupported voxelwise confound ordering '
                           '({} -> {})'.format(startIdx, voxConfLocs))

        # Create the voxelwise confound EVs
        for i, (f, l) in enumerate(zip(voxConfFiles, voxConfLocs)):
            evs.append(VoxelwiseConfoundEV(len(evs), i, 'voxconf', f))

    # Have motion parameters been added
    # as regressors to the design matrix?
    motion = int(settings['motionevs'])

    if   motion == 0: numMotionEVs = 0
    elif motion == 1: numMotionEVs = 6
    elif motion == 2: numMotionEVs = 24

    for i in range(numMotionEVs):
        evs.append(MotionParameterEV(len(evs), i, 'motion'))
        
    # Last step - any columns in the design
    # matrix which have not yet been accounted
    # for are other confounds, specified by
    # the user with a text file.
    numConfoundEVs = designMat.shape[1] - len(evs)
    for i in range(numConfoundEVs):
        evs.append(ConfoundEV(len(evs), i, 'confound'))

    # Phew.
    return evs


def getHigherLevelEVs(featDir, settings, designMat):

    titleKeys = [s for s in settings.keys() if s.startswith('evtitle')]
    evs       = []
    
    return evs 
