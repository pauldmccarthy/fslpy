#!/usr/bin/env python
#
# featdesign.py - The FEATFSFDesign class, and a few other things.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FEATFSFDesign` class, which encapsulates
a FEAT design matrix.


The :class:`FEATFSFDesign` class is intended to be used to access the design
matrix for a FEAT analysis. The main reason for using the ``FEATFSFDesign``
class, instead of just using the design matrix loaded directly from the
``[analysis].feat/design.mat`` file, is because FEAT supports voxelwise EVs,
where the contents of the design matrix will differ for each voxel in the
analysis. For all voxelwise EVs (confound or otherwise), the design matrix (in
``design.mat``) contains a dummy column which contains the mean across all
voxels.  The :meth:`FEATFSFDesign.getDesign` method will return an
appropriate design matrix for a specific voxel.


.. note:: Interaction EVs are not currently supported.


Explanatory variables in a FEAT design
--------------------------------------


A FEAT design matrix may contain the following types of explanatory variables:

 - *Normal* EVs. This is simply a column in the design matrix, defined by the
   user.

 - *Temporal derivative* of normal EVs. A column in the design matrix
   containing the derivative of a normal EV. The presence of a temporal
   derivative EV for a given normal EV can be determined by the ``deriv_yn``
   flag in the ``design.fsf`` file.

 - *Basis function* EV. One or more columns derived from a normal EV. A normal
   EV with the ``convolve`` value set to ``4``, ``5``, or ``6`` will be
   followed by a set of basis function EVs (the number of additional EVs can
   be determined by the ``basisfnum`` flag).

 - *Voxelwise* EVs. An EV with different values for each voxel. An EV with the
   ``shape`` value set to ``9`` is a voxelwise EV. The voxel data will be
   stored in a file in the FEAT directory called ``designVoxelwiseEVN.nii.gz``
   (where ``N`` is the EV number, relative to the order in which the EVs were
   set up by the user).

A FEAT design matrix will contain EVs of the above types, followed by the
following types of *confound* EVs:

 - *Voxelwise confound* EVs. These are confound EVs with different values for
   each voxel. If the design matrix contains confound EVs, two additional
   files will be present in the FEAT directory, ``vef.dat`` and
   ``ven.dat``. The ``vef.dat`` file contains a list of comma separated file
   names, which are paths to the confound images (these should be in the FEAT
   directory, and called ``InputConfoundEVN.nii.gz``). ``ven.dat`` is a list
   of comma separated integers, specifying the column number (starting from 1)
   of each voxelwise confound EV in the final design matrix.

 - *Motion parameter* EVs. The user can choose to add 6 or 24 motion
   parameters as regressors to the design matrix. If the ``motionevs`` value
   in ``design.fsf`` is set to ``1``, then 6 motion EVs are added; if
   ``motionevs`` is ``2``, then 24 motion EVs are added.

 - *Confound* EVs. These are any other EVs added by the user.


Module contents
---------------


In addition to the :class:`FEATFSFDesign` class, this module contains a few
other functions and classes that may be useful to advanced users.


The :func:`loadDesignMat` function loads the ``design.mat`` file from a
FEAT directory, and returns it as a numpy array.


The following functions, defined in this module, will analyse a FEAT analysis
to determine the contents of its design matrix (these functions are called by
the :meth:`FEATFSFDesign.__init__` method, but may be called directly):

.. autosummary::
   :nosignatures:

   getFirstLevelEVs
   getHigherLevelEVs


These functions return a list containing one instance of the following classes
for each column in the design matrix:

.. autosummary::
   :nosignatures:

   NormalEV
   TemporalDerivativeEV
   BasisFunctionEV
   VoxelwiseEV
   ConfoundEV
   MotionParameterEV
   VoxelwiseConfoundEV
"""


import            logging
import            collections
import os.path as op
import numpy   as np

from . import image as fslimage


log = logging.getLogger(__name__)


class FSFError(Exception):
    """Exception raised by various things in this module, primarily when the
    contents of the FEAT directory are not valid.
    """
    pass


class FEATFSFDesign(object):
    """The ``FEATFSFDesign`` class encapsulates the design matrix from a FEAT
    analysis. This class is intended to be used for FEAT analyses generated
    with FSL 5.0.9 and older.
    """

    def __init__(self, featDir, settings=None, loadVoxelwiseEVs=True):
        """Create a ``FEATFSFDesign``.

        :arg featDir:          Path to the FEAT directory.

        :arg settings:         A dictionary containing the FEAT analysis
                               settings from its ``design.fsf``. If not
                               provided, is loaded via
                               :func:`.featanalysis.loadSettings`.

        :arg loadVoxelwiseEVs: If ``True`` (the default), image files
                               for all voxelwise EVs are loaded. Otherwise
                               they are not loaded, and all calls to
                               meth:`getDesign` will contain the mean
                               data for any voxelwise EV columns.
        """

        if settings is None:
            from .featanalysis import loadSettings
            settings = loadSettings(featDir)

        # Get the design matrix, and some
        # information about the analysis
        designMatrix = loadDesignMat(op.join(featDir, 'design.mat'))
        version      = float(settings['version'])
        level        = int(  settings['level'])

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

        if len(self.__evs) != self.__numEVs:
            raise FSFError('Number of EVs does not match design.mat')

        # Load the voxelwise images now,
        # so they're ready to be used by
        # the getDesign method.
        for ev in self.__evs:

            if not isinstance(ev, (VoxelwiseEV, VoxelwiseConfoundEV)):
                continue

            ev.image = None

            # The path to some voxelwise
            # EVs may not be present -
            # see the VoxelwisEV class.
            if loadVoxelwiseEVs and (ev.filename is not None):
                ev.image = fslimage.Image(ev.filename)


    def getEVs(self):
        """Returns a list containing the :class:`EV` instances that represent
        each column of this ``FEATFSFDesign``.
        """
        return list(self.__evs)


    def getDesign(self, voxel=None):
        """Returns the design matrix for the specified voxel.

        :arg voxel: A tuple containing the ``(x, y, z)`` voxel coordinates of
                    interest. If ``None`` (the default), or if this
                    ``FEATFSFDesign`` was created with
                    ``loadVoxelwiseEVs=False``, the design matrix is returned,
                    with any voxelwise EV columns containing the mean
                    voxelwise EV data.
        """

        design = np.array(self.__design)

        if voxel is None:
            return design

        x, y, z = voxel

        for ev in self.__evs:

            if not isinstance(ev, (VoxelwiseEV, VoxelwiseConfoundEV)):
                continue

            if ev.image is None:
                log.warning('Voxel EV image missing '
                            'for ev {}'.format(ev.index))
                continue

            design[:, ev.index] = ev.image[x, y, z, :]

        return design


class EV(object):
    """Class representing an explanatory variable in a FEAT design matrix.

    ``EV`` instances contain the following attributes:

    ========= ============================================================
    ``index`` Index of this ``EV`` (starting from 0) in the design matrix.
    ``title`` Name of this ``EV``.
    ========= ============================================================
    """
    def __init__(self, index, title):
        """Create an ``EV``.

        :arg index: Index (starting from 0) of this ``EV`` in the design
                    matrix.
        :arg title: Name of this ``EV``.
        """
        self.index = index
        self.title = title


class NormalEV(EV):
    """Class representing a *normal* EV in a FEAT design matrix, i.e. one
    which has been explicitly provided by the user.

    ``NormalEV`` instances contain the following attributes (in addition
    to the :class:`EV` attributes):

    ============= ============================================================
    ``origIndex`` Index (starting from 0) of this ``NormalEV``, as it was when
                  the user set up the design matrix (i.e. not taking into
                  account temporal derivative or basis function EVs).
    ============= ============================================================
    """
    def __init__(self, realIdx, origIdx, title):
        """Create a ``NormalEV``.

        :arg realIdx: Index (starting from 0) of this ``NormalEV`` in the
                      design matrix.
        :arg origIdx: Original index (starting from 0) of this ``NormalEV``.
        :arg title:   Name of this ``NormalEV``.
        """
        EV.__init__(self, realIdx, title)
        self.origIndex = origIdx


class TemporalDerivativeEV(NormalEV):
    """Class representing a temporal derivative EV, derived from a normal EV.
    """
    pass


class BasisFunctionEV(NormalEV):
    """Class representing a basis function EV, derived from a normal EV. """
    pass


class VoxelwiseEV(NormalEV):
    """Class representing an EV with different values for each voxel in the
    analysis.

    ``VoxelwiseEV`` instances contain the following attributes (in addition
    to the :class:`NormalEV` attributes):

    ============ ======================================================
    ``filename`` Path to the image file containing the data for this EV
    ============ ======================================================

    .. note:: The file for voxelwise EVs in a higher level analysis are not
              copied into the FEAT directory, so if the user has removed them,
              or moved the .gfeat directory, the file path here will not be
              valid. Therefore, a ``VoxelwiseEV`` will test to see if the
              file exists, and will set the ``filename`` attribute to ``None``
              it it does not exist.
    """

    def __init__(self, realIdx, origIdx, title, filename):
        """Create a ``VoxelwiseEV``.

        :arg realIdx:  Index (starting from 0) of this ``VoxelwiseEV`` in the
                       design matrix.
        :arg origIdx:  Original index (starting from 0) of this
                       ``VoxelwiseEV``.
        :arg title:    Name of this ``VoxelwiseEV``.
        :arg filename: Path to the file containing the data for this
                       ``VoxelwiseEV``.
        """
        NormalEV.__init__(self, realIdx, origIdx, title)

        if op.exists(filename):
            self.filename = filename
        else:
            log.warning('Voxelwise EV file does not exist: '.format(filename))
            self.filename = None


class ConfoundEV(EV):
    """Class representing a confound EV.

    ``ConfoundEV`` instances contain the following attributes (in addition
    to the :class:`EV` attributes):

    ============= ==========================================================
    ``confIndex`` Index of this ``ConfoundEV`` (starting from 0) in relation
                  to all other confound EVs.
    ============= ==========================================================
    """
    def __init__(self, index, confIndex, title):
        """Create a ``ConfoundEV``.

        :arg index:     Index (starting from 0) of this ``ConfoundEV`` in the
                        design matrix.
        :arg confIndex: Index (starting from 0) of this ``ConfoundEV`` in
                        relation to all other confound EVs.
        :arg title:     Name of this ``ConfoundEV``.
        """
        EV.__init__(self, index, title)
        self.confIndex = confIndex


class MotionParameterEV(EV):
    """Class representing a motion parameter EV.

    ``MotionParameterEV`` instances contain the following attributes (in
    addition to the :class:`EV` attributes):

    =============== ========================================================
    ``motionIndex`` Index of this ``MotionParameterEV`` (starting from 0) in
                    relation to all other motion parameter EVs.
    =============== ========================================================
    """
    def __init__(self, index, motionIndex, title):
        """Create a ``MotionParameterEV``.

        :arg index:     Index (starting from 0) of this ``MotionParameterEV``
                        in the design matrix.
        :arg confIndex: Index (starting from 0) of this ``MotionParameterEV``
                        in relation to all other motion parameter EVs.
        :arg title:     Name of this ``MotionParameterEV``.
        """
        EV.__init__(self, index, title)
        self.motionIndex = motionIndex


class VoxelwiseConfoundEV(EV):
    """Class representing a voxelwise confound EV.

    ``VoxelwiseConfoundEV`` instances contain the following attributes (in
    addition to the :class:`EV` attributes):

    ============ ==========================================================
    ``voxIndex`` Index of this ``VoxelwiseConfoundEV`` (starting from 0) in
                 relation to all other voxelwise confound EVs.
    ``filename`` Path to the image file containing the data for this EV
    ============ ==========================================================
    """
    def __init__(self, index, voxIndex, title, filename):
        """Create a ``Voxelwise ConfoundEV``.

        :arg index:     Index (starting from 0) of this
                        ``VoxelwiseConfoundEV`` in the design matrix.
        :arg confIndex: Index (starting from 0) of this
                        ``VoxelwiseConfoundEV`` in relation to all other
                        voxelwise confound EVs.
        :arg title:     Name of this ``VoxelwiseConfoundEV``.
        """
        EV.__init__(self, index, title)
        self.voxIndex = voxIndex

        if op.exists(filename):
            self.filename = filename
        else:
            log.warning('Voxelwise confound EV file '
                        'does not exist: '.format(filename))
            self.filename = None


def getFirstLevelEVs(featDir, settings, designMat):
    """Derives the EVs for the given first level FEAT analysis.

    :arg featDir:   Path to the FEAT analysis.
    :arg settings:  A dictionary containing the FEAT analysis settings
                    from its ``design.fsf`` file (see
                    :func:`.featanalysis.loadSettings`).
    :arg designMat: The FEAT design matrix (a numpy array - see
                    :func:`loadDesignMat`).

    :returns: A list of :class:`EV` instances, one for each column in the
              design matrix.
    """

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

            # The addExt function will raise an
            # error if the file does not exist.
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
        if voxConfLocs != list(range(startIdx, startIdx + len(voxConfFiles))):
            raise FSFError('Unsupported voxelwise confound ordering '
                           '({} -> {})'.format(startIdx, voxConfLocs))

        # Create the voxelwise confound EVs.
        # We make a name for the EV from the
        # file name.
        for i, (f, l) in enumerate(zip(voxConfFiles, voxConfLocs)):
            title = op.basename(fslimage.removeExt(f))
            evs.append(VoxelwiseConfoundEV(len(evs), i, title, f))

    # Have motion parameters been added
    # as regressors to the design matrix?
    motion = int(settings['motionevs'])

    if   motion == 1: numMotionEVs = 6
    elif motion == 2: numMotionEVs = 24
    else:             numMotionEVs = 0

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
    """Derives the EVs for the given higher level FEAT analysis.

    :arg featDir:   Path to the FEAT analysis.
    :arg settings:  A dictionary containing the FEAT analysis settings
                    from its ``design.fsf`` file (see
                    :func:`.featanalysis.loadSettings`).
    :arg designMat: The FEAT design matrix (a numpy array - see
                    :func:`loadDesignMat`).

    :returns: A list of :class:`EV` instances, one for each column in the
              design matrix.
    """

    # TODO Maybe I can give the voxel EVs titles based on their
    # file name, for higher level (here) and first level (above).

    evs = []

    # For a higher level analysis, there
    # are only two types of EVs:
    #
    #   - Normal EVs
    #   - Voxelwise EVs
    #
    # evs_orig is the number of normal EVs
    # evs_vox is the number of voxelwise EVs
    # evs_real is the total number of EVs
    voxEVs   = int(settings['evs_vox'])
    origEVs  = int(settings['evs_orig'])
    realEVs  = int(settings['evs_real'])

    # Sanity check
    if (origEVs + voxEVs != realEVs) or (realEVs != designMat.shape[1]):
        raise FSFError('Invalid number of EVs in design.fsf')

    # The normal EVs are specified in the same
    # way as for a first level analysis
    for origIdx in range(origEVs):

        # All we need is the title
        title = settings['evtitle{}'.format(origIdx + 1)]
        evs.append(NormalEV(len(evs), origIdx, title))

    # Only the input file is specified for
    # voxelwise EVs. We can create a title
    # for each voxelwise EV from its file
    # name.
    for origIdx in range(voxEVs):

        filename = settings['evs_vox_{}'.format(origIdx + 1)]
        title    = op.basename(fslimage.removeExt(filename))
        evs.append(VoxelwiseEV(len(evs), origIdx, title, filename))

    return evs


def loadDesignMat(designmat):
    """Loads the specified design matrix.

    Returns a ``numpy`` array containing the design matrix data, where the
    first dimension corresponds to the data points, and the second to the EVs.

    :arg designmat: Path to the ``design.mat`` file.
    """

    log.debug('Loading FEAT design matrix from {}'.format(designmat))

    matrix = np.loadtxt(designmat, comments='/', ndmin=2)

    if matrix is None or matrix.size == 0 or len(matrix.shape) != 2:
        raise FSFError('{} does not appear to be a '
                       'valid design.mat file'.format(designmat))

    return matrix
