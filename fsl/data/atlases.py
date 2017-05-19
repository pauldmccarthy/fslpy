#!/usr/bin/env python
#
# atlases.py - API which provides access to the atlas image files contained
#              in $FSLDIR/data/atlases/
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides access to FSL atlas images, typically contained in
``$FSLDIR/data/atlases/``. The :class:`AtlasRegistry` class provides access
to these atlases, and allows the user to load atlases stored in other
locations. A single :class:`.AtlasRegistry` instance is created when this
module is first imported - it is available as a module level attribute called
:attr:`registry`, and some of its methods are available as module-level
functions:


.. autosummary::
   :nosignatures:

   rescanAtlases
   listAtlases
   hasAtlas
   getAtlasDescription
   loadAtlas
   addAtlas
   removeAtlas
   rescanAtlases


You must call the :meth:`.AtlasRegistry.rescanAtlases` function before any of
the other functions will work.  The :func:`loadAtlas` function allows you to
load an atlas image, which will be one of the following atlas-specific
:class:`.Image` sub-classes:

.. autosummary::
   :nosignatures:

   LabelAtlas
   ProbabilisticAtlas
"""


from __future__ import division

import xml.etree.ElementTree              as et
import os.path                            as op
import                                       glob
import                                       bisect
import                                       logging

import numpy                              as np

import fsl.data.image                     as fslimage
import fsl.data.constants                 as constants
from   fsl.utils.platform import platform as platform
import fsl.utils.transform                as transform
import fsl.utils.notifier                 as notifier
import fsl.utils.settings                 as fslsettings


log = logging.getLogger(__name__)


class AtlasRegistry(notifier.Notifier):
    """The ``AtlasRegistry`` maintains a list of all known atlases.


    When the :meth:`rescanAtlases` method is called, the ``AtlasRegistry``
    loads all of the FSL XML atlas specification files in
    ``$FSLDIR/data/atlases``, and builds a list of :class:`AtlasDescription`
    instances, each of which contains information about one atlas.


    The :meth:`addAtlas` method allows other atlases to be added to the
    registry. Whenever a new atlas is added, the ``AtlasRegistry`` notifies
    any registered listeners via the :class:`.Notifier` interface with the
    topic ``'add'``, passing it the newly loaded class:`AtlasDecsription`.
    Similarly, the :meth:`removeAtlas` method allows individual atlases to be
    removed. When this occurs, registered listeners on the ``'remove'`` topic
    are notified, and passed the ``AtlasDescription`` instance of the removed
    atlas.


    The ``AtlasRegistry`` stores a list of all known atlases via the
    :mod:`.settings` module. When an ``AtlasRegistry`` is created, it loads
    in any previously known atlases. Whenever a new atlas is added, this
    list is updated. See the :meth:`__getKnownAtlases` and
    :meth:`_saveKnownAtlases` methods.
    """


    def __init__(self):
        """Create an ``AtlasRegistry``. """

        # A list of all AtlasDescription
        # instances in existence, sorted
        # by AtlasDescription.name.
        self.__atlasDescs = []


    def rescanAtlases(self):
        """Causes the ``AtlasRegistry`` to rescan available atlases from
        ``$FSLDIR``. Atlases are loaded from the ``fsl.data.atlases`` setting
        (via the :mod:`.settings` module), and from ``$FSLDIR/data/atlases/``.
        """

        log.debug('Initialising atlas registry')
        self.__atlasDescs = []

        # Get $FSLDIR atlases
        fslPaths = []
        if platform.fsldir is not None:
            fsldir   = op.join(platform.fsldir, 'data', 'atlases')
            fslPaths = sorted(glob.glob(op.join(fsldir, '*.xml')))

        # Any extra atlases that have
        # been loaded in the past
        extraIDs, extraPaths = self.__getKnownAtlases()

        # FSLDIR atlases first, any
        # other atlases second.
        atlasPaths = list(fslPaths)         + extraPaths
        atlasIDs   = [None] * len(fslPaths) + extraIDs

        with self.skipAll():
            for atlasID, atlasPath in zip(atlasIDs, atlasPaths):

                # The FSLDIR atlases are probably
                # listed twice - from the above glob,
                # and from the saved extraPaths. So
                # we remove any duplicates.
                if atlasID is not None and self.hasAtlas(atlasID):
                    continue

                try:
                    self.addAtlas(atlasPath, atlasID, save=False)
                except:
                    log.warning('Failed to load atlas '
                                'specification {}'.format(atlasPath),
                                exc_info=True)


    def listAtlases(self):
        """Returns a list containing :class:`AtlasDescription` objects for
        all available atlases. The atlases are ordered in terms of the
        ``AtlasDescription.name`` attribute (converted to lower case).
        """
        return list(self.__atlasDescs)


    def hasAtlas(self, atlasID):
        """Returns ``True`` if this ``AtlasRegistry`` has an atlas with the
        specified ``atlasID``.
        """
        return atlasID in [d.atlasID for d in self.__atlasDescs]


    def getAtlasDescription(self, atlasID):
        """Returns an :class:`AtlasDescription` instance describing the
        atlas with the given ``atlasID``.
        """

        for desc in self.__atlasDescs:
            if desc.atlasID == atlasID:
                return desc

        raise KeyError('Unknown atlas ID: {}'.format(atlasID))


    def loadAtlas(self, atlasID, loadSummary=False, resolution=None):
        """Loads and returns an :class:`Atlas` instance for the atlas
        with the given  ``atlasID``.

        :arg loadSummary: If ``True``, a 3D :class:`LabelAtlas` image is
                          loaded. Otherwise, if the atlas is probabilistic,
                          a 4D :class:`ProbabilisticAtlas` image is loaded.

        :arg resolution: Optional. Desired isotropic atlas resolution in
                         millimetres, e.g. ``1.0`` or ``2.0``. The available
                         atlas with the nearest resolution to this value
                         will be returned. If not provided, the highest
                         resolution atlas will be loaded.
        """

        atlasDesc = self.getAtlasDescription(atlasID)

        # label atlases are only
        # available in 'summary' form
        if atlasDesc.atlasType == 'label':
            loadSummary = True

        if loadSummary: atlas = LabelAtlas(        atlasDesc, resolution)
        else:           atlas = ProbabilisticAtlas(atlasDesc, resolution)

        return atlas


    def addAtlas(self, filename, atlasID=None, save=True):
        """Add an atlas from the given XML specification file to the registry.

        :arg filename: Path to a FSL XML atlas specification file.

        :arg atlasID:  ID to give this atlas. If not provided, the file
                       base name (converted to lower-case) is used. If an
                       atlas with the given ID already exists, this new atlas
                       is given a unique id.

        :arg save:     If ``True`` (the default), this atlas will be saved
                       so that it will be available in future instantiations.
        """

        filename = op.abspath(filename)

        if atlasID is None:
            atlasIDBase = op.splitext(op.basename(filename))[0].lower()
            atlasID     = atlasIDBase
        else:
            atlasIDBase = atlasID

        # If an atlas with the same ID/path
        # already exists, raise an error
        if self.hasAtlas(atlasID):
            raise KeyError('An atlas with ID "{}" already '
                           'exists'.format(atlasID))

        desc = AtlasDescription(filename, atlasID)

        log.debug('Adding atlas to registry: {} / {}'.format(
            desc.atlasID,
            desc.specPath))

        bisect.insort_left(self.__atlasDescs, desc)

        if save:
            self.__saveKnownAtlases()

        self.notify(topic='add', value=desc)

        return desc


    def removeAtlas(self, atlasID):
        """Removes the atlas with the specified ``atlasID`` from this
        ``AtlasRegistry``.
        """

        for i, desc in enumerate(self.__atlasDescs):
            if desc.atlasID == atlasID:

                log.debug('Removing atlas from registry: {} / {}'.format(
                    desc.atlasID,
                    desc.specPath))

                self.__atlasDescs.pop(i)
                break

        self.__saveKnownAtlases()

        self.notify(topic='remove', value=desc)


    def __getKnownAtlases(self):
        """Returns a list of tuples containing the IDs and paths of all known
        atlases .

        The atlases are retrieved via the :mod:`.settings` module - a setting
        with the name ``fsl.data.atlases`` is assumed to contain a string of
        ``atlasID=specPath`` pairs, separated with the operating system file
        path separator (``:`` on Unix/Linux).
        See also :meth:`__saveKnownAtlases`.
        """
        try:
            atlases = fslsettings.read('fsl.data.atlases')

            if atlases is None: atlases = []
            else:               atlases = atlases.split(op.pathsep)

            atlases = [e.split('=') for e in atlases]
            atlases = [(name.strip(), path.strip())
                       for name, path in atlases
                       if op.exists(path)]

            names = [e[0] for e in atlases]
            paths = [e[1] for e in atlases]

            return names, paths

        except:
            return [], []


    def __saveKnownAtlases(self):
        """Saves the IDs and paths of all atlases which are currently in
        the registry. The atlases are saved via the :mod:`.settings` module.
        """

        if self.__atlasDescs is None:
            return

        atlases = []

        for desc in self.__atlasDescs:
            atlases.append((desc.atlasID, desc.specPath))

        atlases = ['{}={}'.format(name, path) for name, path in atlases]
        atlases = op.pathsep.join(atlases)

        fslsettings.write('fsl.data.atlases', atlases)


class AtlasLabel(object):
    """The ``AtlasLabel`` class is used by the :class:`AtlasDescription` class
    as a container object used for storing atlas label information.

    An ``AtlasLabel`` instance contains the following attributes:

    ========= ==============================================================
    ``name``  Region name
    ``index`` For probabilistic atlases, the volume index into the 4D atlas
              image that corresponds to this region. For label atlases, the
              value of voxels that are in this region. For summary images of
              probabilistic atlases, add 1 to this value to get the
              corresponding voxel values.
    ``x``     X coordinate of the region in world space
    ``y``     Y coordinate of the region in world space
    ``z``     Z coordinate of the region in world space
    ========= ==============================================================

    .. note:: The ``x``, ``y`` and ``z`` label coordinates are pre-calculated
              centre-of-gravity coordinates, as listed in the atlas xml file.
              They are in the coordinate system defined by the transformation
              matrix for the first image in the ``images`` list of the atlas
              XML file (typically MNI152 space).
    """

    def __init__(self, name, index, x, y, z):
        self.name  = name
        self.index = index
        self.x     = x
        self.y     = y
        self.z     = z


    def __eq__(self, other):
        """Compares the ``index`` of this ``AtlasLabel`` with another.
        """
        return self.index == other.index


    def __neq__(self, other):
        """Compares the ``index`` of this ``AtlasLabel`` with another.
        """
        return self.index != other.index


    def __lt__(self, other):
        """Compares this ``AtlasLabel`` with another by their ``index``
        attribute.
        """
        return self.index < other.index


class AtlasDescription(object):
    """An ``AtlasDescription`` instance parses and stores the information
    stored in the FSL XML file that describes a single FSL atlas.  An XML
    atlas specification file is assumed to have a structure that looks like
    the following:

    .. code-block:: xml

       <atlas>
         <header>
           <name></name>        # Atlas name
           <type></type>        # 'Probabilistic' or 'Label'
           <images>
            <imagefile>
            </imagefile>        # If type is Probabilistic, path
                                # to 4D image file, one volume per
                                # label, Otherwise, if type is
                                # Label, path to 3D label file
                                # (identical to the summaryimagefile
                                # below). The path must be specified
                                # as relative to the location of this
                                # XML file.

            <summaryimagefile>  # Path to 3D summary file, with each
            </summaryimagefile> # region having value (index + 1)

           </images>
           ...                  # More images - generally both
                                # 1mm and 2mm  versions (in
                                # MNI152 space) are available
         </header>
        <data>

         # index - For probabilistic atlases, index of corresponding volume in
         #         4D image file. For label images, the value of voxels which
         #         are in the corresponding region.
         #
         # x    |
         # y    |- XYZ *voxel* coordinates into the first image of the <images>
         #      |  list
         # z    |
         <label index="0" x="0" y="0" z="0">Name</label>
         ...
        </data>
       </atlas>


    Each ``AtlasDescription`` is assigned an identifier, which is simply the
    XML file name describing the atlas, sans-suffix, and converted to lower
    case.  For exmaple, the atlas described by:

        ``$FSLDIR/data/atlases/HarvardOxford-Cortical.xml``

    is given the identifier

        ``harvardoxford-cortical``


    This identifier is intended to be unique.


    The following attributes are available on an ``AtlasDescription`` instance:

    ================= ======================================================
    ``atlasID``       The atlas ID, as described above.

    ``name``          Name of the atlas.

    ``specPath``      Path to the atlas XML specification file.

    ``atlasType``     Atlas type - either *probabilistic* or *label*.

    ``images``        A list of images available for this atlas - usually
                      :math:`1mm^3` and :math:`2mm^3` images are present.

    ``summaryImages`` For probabilistic atlases, a list of *summary* images,
                      which are just 3D labelled variants of the atlas.

    ``pixdims``       A list of ``(x, y, z)`` pixdim tuples in mm, one for
                      each image in ``images``.

    ``xforms``        A list of affine transformation matrices (as ``4*4``
                      ``numpy`` arrays), one for each image in ``images``,
                      defining the voxel to world coordinate transformations.

    ``labels``        A list of :class`AtlasLabel` objects, describing each
                      region / label in the atlas.
    ================= ======================================================
    """


    def __init__(self, filename, atlasID=None):
        """Create an ``AtlasDescription`` instance.

        :arg filename: Name of the XML file describing the atlas.

        :arg atlasID:  ID to use for this atlas. If not provided, the file
                       base name is used.
        """

        log.debug('Loading atlas description from {}'.format(filename))

        root   = et.parse(filename)
        header = root.find('header')
        data   = root.find('data')

        if atlasID is None:
            atlasID = op.splitext(op.basename(filename))[0].lower()

        self.atlasID   = atlasID
        self.specPath  = op.abspath(filename)
        self.name      = header.find('name').text
        self.atlasType = header.find('type').text.lower()

        # Spelling error in some of the atlas.xml files.
        if self.atlasType == 'probabalistic':
            self.atlasType = 'probabilistic'

        images             = header.findall('images')
        self.images        = []
        self.summaryImages = []
        self.pixdims       = []
        self.xforms        = []

        atlasDir = op.dirname(self.specPath)

        for image in images:
            imagefile        = image.find('imagefile')       .text
            summaryimagefile = image.find('summaryimagefile').text

            # Assuming that the path
            # names begin with a slash
            imagefile        = op.join(atlasDir, '.' + imagefile)
            summaryimagefile = op.join(atlasDir, '.' + summaryimagefile)

            i = fslimage.Image(imagefile, loadData=False, calcRange=False)

            self.images       .append(imagefile)
            self.summaryImages.append(summaryimagefile)
            self.pixdims      .append(i.pixdim[:3])
            self.xforms       .append(i.voxToWorldMat)

        labels      = data.findall('label')
        self.labels = []

        # The xyz coordinates for each label are in terms
        # of the voxel space of the first images element
        # in the header. For convenience, we're going to
        # transform all of these voxel coordinates into
        # MNI152 space coordinates.
        coords = np.zeros((len(labels), 3), dtype=np.float32)

        for i, label in enumerate(labels):

            name  = label.text
            index = int(  label.attrib['index'])
            x     = float(label.attrib['x'])
            y     = float(label.attrib['y'])
            z     = float(label.attrib['z'])
            al    = AtlasLabel(name, index, x, y, z)

            coords[i] = (x, y, z)

            self.labels.append(al)

        # Load the appropriate transformation matrix
        # and transform all those voxel coordinates
        # into world coordinates
        coords = transform.transform(coords, self.xforms[0])

        # Update the coordinates
        # in our label objects
        for i, label in enumerate(self.labels):
            label.x, label.y, label.z = coords[i]


    def __eq__(self, other):
        """Compares the ``atlasID`` of this ``AtlasDescription`` with another.
        """
        return self.atlasID == other.atlasID


    def __neq__(self, other):
        """Compares the ``atlasID`` of this ``AtlasDescription`` with another.
        """
        return self.atlasID != other.atlasID


    def __lt__(self, other):
        """Compares this ``AtlasDescription`` with another by their ``name``
        attribute.
        """
        return self.name.lower() < other.name.lower()


class Atlas(fslimage.Image):
    """This is the base class for the :class:`LabelAtlas` and
    :class:`ProbabilisticAtlas` classes. It contains some initialisation
    logic common to both.
    """


    def __init__(self, atlasDesc, resolution=None, isLabel=False):
        """Initialise an ``Atlas``.

        :arg atlasDesc:  The :class:`AtlasDescription` instance which
                         describes the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.

        :arg isLabel:    Pass in ``True`` for label atlases, ``False`` for
                         probabilistic atlases.
        """

        # Get the index of the atlas with the
        # nearest resolution to that provided.
        # If a reslution has not been provided,
        # choose the atlas image with the
        # highest resolution.
        #
        # We divide by three to get the atlas
        # image index because there are three
        # pixdim values for each atlas.
        res   = resolution
        reses = np.concatenate(atlasDesc.pixdims)

        if resolution is None: imageIdx = np.argmin(reses)
        else:                  imageIdx = np.argmin(np.abs(reses - res))

        imageIdx = imageIdx // 3

        if isLabel: imageFile = atlasDesc.summaryImages[imageIdx]
        else:       imageFile = atlasDesc.images[       imageIdx]

        fslimage.Image.__init__(self, imageFile)

        # Even though all the FSL atlases
        # are in MNI152 space, not all of
        # their sform_codes are correctly set
        self.nibImage.get_header().set_sform(
            None, code=constants.NIFTI_XFORM_MNI_152)

        self.desc = atlasDesc


class LabelAtlas(Atlas):
    """A 3D atlas which contains integer labels for each region.

    The ``LabelAtlas`` class provides the :meth:`label` method, which
    makes looking up the label at a location easy.
    """

    def __init__(self, atlasDesc, resolution=None):
        """Create a ``LabelAtlas`` instance.

        :arg atlasDesc:  The :class:`AtlasDescription` instance describing
                         the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.
        """
        Atlas.__init__(self, atlasDesc, resolution, True)


    def label(self, worldLoc):
        """Looks up and returns the label of the region at the given world
        location, or ``None`` if the location is out of bounds.
        """

        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat)[0]
        voxelLoc = [int(v) for v in voxelLoc.round()]

        if voxelLoc[0] <  0             or \
           voxelLoc[1] <  0             or \
           voxelLoc[2] <  0             or \
           voxelLoc[0] >= self.shape[0] or \
           voxelLoc[1] >= self.shape[1] or \
           voxelLoc[2] >= self.shape[2]:
            return None

        val = self[voxelLoc[0], voxelLoc[1], voxelLoc[2]]

        if self.desc.atlasType == 'label':
            return val

        elif self.desc.atlasType == 'probabilistic':
            return val - 1


class ProbabilisticAtlas(Atlas):
    """A 4D atlas which contains one volume for each region.

    The ``ProbabilisticAtlas`` provides the :meth`proportions` method,
    which makes looking up region probabilities easy.
    """

    def __init__(self, atlasDesc, resolution=None):
        """Create a ``ProbabilisticAtlas`` instance.

        :arg atlasDesc:  The :class:`AtlasDescription` instance describing
                         the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.
        """
        Atlas.__init__(self, atlasDesc, resolution, False)


    def proportions(self, worldLoc):
        """Looks up the region probabilities for the given location.

        :arg worldLoc: Location in the world coordinate system.

        :returns: a list of values, one per region, which represent
                  the probability of each region for the specified
                  location. Returns an empty list if the given
                  location is out of bounds.
        """
        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat)[0]
        voxelLoc = [int(v) for v in voxelLoc.round()]

        if voxelLoc[0] <  0             or \
           voxelLoc[1] <  0             or \
           voxelLoc[2] <  0             or \
           voxelLoc[0] >= self.shape[0] or \
           voxelLoc[1] >= self.shape[1] or \
           voxelLoc[2] >= self.shape[2]:
            return []

        return self[voxelLoc[0], voxelLoc[1], voxelLoc[2], :]


registry            = AtlasRegistry()
rescanAtlases       = registry.rescanAtlases
listAtlases         = registry.listAtlases
hasAtlas            = registry.hasAtlas
getAtlasDescription = registry.getAtlasDescription
loadAtlas           = registry.loadAtlas
addAtlas            = registry.addAtlas
removeAtlas         = registry.removeAtlas
rescanAtlases       = registry.rescanAtlases
