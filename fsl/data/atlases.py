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
   StatisticAtlas
   ProbabilisticAtlas
"""


from __future__ import division

import xml.etree.ElementTree    as et
import os.path                  as op
import                             glob
import                             bisect
import                             logging

import numpy                    as np

import fsl.data.image           as fslimage
import fsl.data.constants       as constants
from   fsl.utils.platform import   platform
import fsl.utils.image.resample as resample
import fsl.transform.affine     as affine
import fsl.utils.notifier       as notifier
import fsl.utils.settings       as fslsettings


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
                except Exception:
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


    def loadAtlas(self, atlasID, loadSummary=False, resolution=None, **kwargs):
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

        if loadSummary: atype = LabelAtlas
        else:           atype = ProbabilisticAtlas

        return atype(atlasDesc, resolution, **kwargs)


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

        remove = None

        for i, desc in enumerate(self.__atlasDescs):
            if desc.atlasID == atlasID:

                log.debug('Removing atlas from registry: {} / {}'.format(
                    desc.atlasID,
                    desc.specPath))

                self.__atlasDescs.pop(i)
                remove = desc
                break

        self.__saveKnownAtlases()

        if remove is not None:
            self.notify(topic='remove', value=remove)


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

        except Exception:
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

    ========= ================================================================
    ``name``  Region name
    ``index`` The index of this label into the list of all labels in the
              ``AtlasDescription`` that owns it. For statistic/probabilistic
              atlases, this is also the index into the 4D atlas image of the
              volume that corresponds to this region.
    ``value`` For label atlases and summary images, the value of voxels that
              are in this region.
    ``x``     X coordinate of the region in world space
    ``y``     Y coordinate of the region in world space
    ``z``     Z coordinate of the region in world space
    ========= ================================================================

    .. note:: The ``x``, ``y`` and ``z`` label coordinates are pre-calculated
              centre-of-gravity coordinates, as listed in the atlas xml file.
              They are in the coordinate system defined by the transformation
              matrix for the first image in the ``images`` list of the atlas
              XML file (typically MNI152 space).
    """

    def __init__(self, name, index, value, x, y, z):
        self.name  = name
        self.index = index
        self.value = value
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

    def __repr__(self):
        """
        Represents AtlasLabel as string
        """
        return '{}({}, index={}, value={})'.format(
                self.__class__.__name__, self.name,
                self.index, self.value,
        )


class AtlasDescription(object):
    """An ``AtlasDescription`` instance parses and stores the information
    stored in the FSL XML file that describes a single FSL atlas.  An XML
    atlas specification file is assumed to have a structure that looks like
    the following:

    .. code-block:: xml

       <atlas>
         <header>
           <name></name>           # Atlas name
           <type></type>           # 'Statistic', 'Probabilistic' or 'Label'
           <statistic></statistic> # Optional. Type of statistic
           <units></units>         # Optional. Units of measurement
           <precision></precision> # Optional. Decimal precision to report
           <upper></upper>         # Optional. Upper threshold
           <lower></lower>         # Optional. Lower threshold
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

            <summaryimagefile>  # Path to 3D label summary file,
            </summaryimagefile> # Every <image> must be accompanied
                                # by a <summaryimage> - for label
                                # atlases, they will typically refer
                                # to the same image file.

           </images>
           ...                  # More images - generally both
                                # 1mm and 2mm  versions (in
                                # MNI152 space) are available
         </header>
        <data>

         # index - For statistic/probabilistic atlases, index of corresponding
         #         volume in 4D image file. For label images, the value of
         #         voxels which are in the corresponding region. For
         #         statistic/probabilistic atlases, it is assumed that the
         #         value for each region in the summary image(s) are equal to
         #         ``index + 1``.
         #
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

    ``atlasType``     Atlas type - either *statistic*, *probabilistic* or
                      *label*.

    ``statistic``     Type of statistic, for statistic atlases.

    ``units``         Unit of measurement, for statistic atlases.

    ``precision``     Reporting precision, for statistic atlases.

    ``upper``         Upper threshold, for statistic atlases.

    ``lower``         Lower threshold, for statistic atlases.

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
        self.name      = header.find('name').text.strip()
        self.atlasType = header.find('type').text.strip().lower()

        # Spelling error in some of the atlas.xml files.
        if self.atlasType == 'probabalistic':
            self.atlasType = 'probabilistic'

        if self.atlasType == 'statistic':

            fields = ['statistic', 'units', 'lower', 'upper', 'precision']
            values = {}

            for field in fields:
                elem = header.find(field)
                if elem is not None and elem.text is not None:
                    values[field] = elem.text.strip()

            self.statistic =       values.get('statistic', '')
            self.units     =       values.get('units',     '')
            self.lower     = float(values.get('lower',     0))
            self.upper     = float(values.get('upper',     100))
            self.precision = int(  values.get('precision', 2))

        elif self.atlasType == 'probabilistic':
            self.statistic = ''
            self.units     = '%'
            self.lower     = 5
            self.upper     = 100
            self.precision = 0

        images             = header.findall('images')
        self.images        = []
        self.summaryImages = []
        self.pixdims       = []
        self.xforms        = []

        atlasDir = op.dirname(self.specPath)

        for image in images:

            # Every image must also have a summary image
            imagefile        = image.find('imagefile')       .text.strip()
            summaryimagefile = image.find('summaryimagefile').text.strip()

            # Assuming that the path
            # names begin with a slash
            imagefile        = op.normpath(atlasDir + imagefile)
            summaryimagefile = op.normpath(atlasDir + summaryimagefile)

            i = fslimage.Image(imagefile, loadData=False, calcRange=False)

            self.images       .append(imagefile)
            self.summaryImages.append(summaryimagefile)
            self.pixdims      .append(i.pixdim[:3])
            self.xforms       .append(i.voxToWorldMat)

        labels      = data.findall('label')
        self.labels = []

        # Refs to AtlasLabel objects
        # indexed by their value.
        # Used by the find method.
        self.__labelsByValue = {}

        # The xyz coordinates for each label are in terms
        # of the voxel space of the first images element
        # in the header. For convenience, we're going to
        # transform all of these voxel coordinates into
        # MNI152 space coordinates.
        coords = np.zeros((len(labels), 3), dtype=np.float32)

        for i, label in enumerate(labels):

            name  = label.text.strip()
            index = int(  label.attrib['index'])
            x     = float(label.attrib['x'])
            y     = float(label.attrib['y'])
            z     = float(label.attrib['z'])

            # For label images, the index field
            # contains the region value
            if self.atlasType == 'label':
                value = index
                index = i

            # For probablistic images, the index
            # field specifies the volume in the
            # 4D atlas corresponding to the region.
            # It is assumed that the summary value
            # for each region is index + 1
            else:
                value = index + 1

            al        = AtlasLabel(name, index, value, x, y, z)
            coords[i] = (x, y, z)

            self.labels.append(al)
            self.__labelsByValue[value] = al

        # Load the appropriate transformation matrix
        # and transform all those voxel coordinates
        # into world coordinates
        coords = affine.transform(coords, self.xforms[0])

        # Update the coordinates
        # in our label objects
        for i, label in enumerate(self.labels):
            label.x, label.y, label.z = coords[i]

        # Make sure the labels are sorted by index
        self.labels = list(sorted(self.labels))


    def find(self, index=None, value=None, name=None):
        """Find an :class:`.AtlasLabel` either by ``index``, or by ``value``.

        Exactly one of ``index``, ``value``, or ``name`` may be specified - a
        ``ValueError`` is raised otherwise. If an invalid ``index``, ``name``, or
        ``value`` is specified, an ``IndexError`` or ``KeyError`` will be
        raised.

        .. note:: A 4D ``ProbabilisticAtlas`` may have more volumes than
                  labels, and a 3D ``LabelAtlas`` may have more values
                  than labels.
        """
        if ((index is not None) + (value is not None) + (name is not None)) != 1:
            raise ValueError('Only one of index, value, or name may be specified')
        if index is not None:   return self.labels[         index]
        elif value is not None: return self.__labelsByValue[int(value)]
        else:
            matches = [l for l in self.labels if l.name == name]
            if len(matches) == 0:
                # look for partial matches only if there are no full matches
                matches = [l for l in self.labels if l.name[:len(name)] == name]
            if len(matches) == 0:
                raise IndexError('No match for {} found in labels {}'.format(
                    name, tuple(l.name for l in self.labels)
                ))
            elif len(matches) > 1:
                raise IndexError('Multiple matches for {} found in labels {}'.format(
                    name, tuple(l.name for l in self.labels)
                ))
            return matches[0]



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

    def __repr__(self, ):
        """
        String representation of AtlasDescription
        """
        return '{}({})'.format(self.__class__.__name__, self.atlasID)


class Atlas(fslimage.Image):
    """This is the base class for the :class:`LabelAtlas` and
    :class:`ProbabilisticAtlas` classes. It contains some initialisation
    logic common to both.
    """


    def __init__(self,
                 atlasDesc,
                 resolution=None,
                 isLabel=False,
                 **kwargs):
        """Initialise an ``Atlas``.

        :arg atlasDesc:  The :class:`AtlasDescription` instance which
                         describes the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.

        :arg isLabel:    Pass in ``True`` for label atlases, ``False`` for
                         statistic/probabilistic atlases.

        All other arguments are passed to :meth:`.Image.__init__`.
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

        fslimage.Image.__init__(self, imageFile, **kwargs)

        # Even though all the FSL atlases
        # are in MNI152 space, not all of
        # their sform_codes are correctly set
        self.nibImage.header.set_sform(
            None, code=constants.NIFTI_XFORM_MNI_152)

        self.desc = atlasDesc


    def find(self, *args, **kwargs):
        """Find an ``AtlasLabel`` - see the :meth:`AtlasDescription.find`
        method.
        """
        return self.desc.find(*args, **kwargs)


    def prepareMask(self, mask):
        """Makes sure that the given mask has the same resolution as this
        atlas, so it can be used for querying. Used by the
        :meth:`.LabelAtlas.maskLabels` and
        :meth:`.StatisticAtlas.maskValues` methods.

        :arg mask: A :class:`.Image`

        :returns:  A ``numpy`` array containing the resampled mask data.

        :raises:   A :exc:`MaskError` if the mask is not in the same space as
                   this atlas, or does not have three dimensions.
        """

        # Make sure that the mask has the same
        # number of voxels as the atlas image.
        # Use nearest neighbour interpolation
        # for resampling, as it is most likely
        # that the mask is binary.
        try:
            mask, xform = resample.resample(
                mask, self.shape[:3], dtype=np.float32, order=0)

        except ValueError:
            raise MaskError('Mask has wrong number of dimensions')

        # TODO allow non-aligned mask - as long as it overlaps
        #      in world coordinates, it should be allowed
        if not fslimage.Image(mask, xform=xform).sameSpace(self):
            raise MaskError('Mask is not in the same space as atlas')

        return mask


class MaskError(Exception):
    """Exception raised by the :meth:`LabelAtlas.maskLabel` and
    :meth:`StatisticAtlas.maskValues` when a mask is provided which
    does not match the atlas space.
    """


class LabelAtlas(Atlas):
    """A 3D atlas which contains integer labels for each region.

    The ``LabelAtlas`` class provides the :meth:`label` method, which
    makes looking up the label at a location easy.
    """

    def __init__(self, atlasDesc, resolution=None, **kwargs):
        """Create a ``LabelAtlas`` instance.

        :arg atlasDesc:  The :class:`AtlasDescription` instance describing
                         the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.
        """
        Atlas.__init__(self, atlasDesc, resolution, True, **kwargs)


    def label(self, location, *args, **kwargs):
        """Looks up and returns the label of the region at the given
        location.

        :arg location: Can be one of the following:

                        - A sequence of three values, interpreted as
                          atlas coordinates. In this case, :meth:`coordLabel`
                          is called.

                        - An :class:`.Image` which is interpreted as a
                          weighted mask. In this case, :meth:`maskLabel` is
                          called.

        All other arguments are passed through to the :meth:`coordLabel` or
        :meth:`maskLabel` methods.


        :returns: The return value of either :meth:`coordLabel` or
                  :meth:`maskLabel`.
        """

        if isinstance(location, fslimage.Image):
            return self.maskLabel(location, *args, **kwargs)
        else:
            return self.coordLabel(location, *args, **kwargs)


    def coordLabel(self, loc, voxel=False):
        """Looks up and returns the label at the given location.

        :arg loc:   A sequence of three values, interpreted as atlas
                    coordinates. In this case, :meth:`coordLabel` is called.

        :arg voxel: Defaults to ``False``. If ``True``, the ``location``
                    is interpreted as voxel coordinates.

        :returns:   The label at the given coordinates, or ``None`` if the
                    coordinates are out of bounds.

        .. note:: Use the :meth:`find` method to retrieve the ``AtlasLabel``
                  associated with each returned value.
        """

        if not voxel:
            loc = affine.transform([loc], self.worldToVoxMat)[0]
            loc = [int(v) for v in loc.round()]

        if loc[0] <  0             or \
           loc[1] <  0             or \
           loc[2] <  0             or \
           loc[0] >= self.shape[0] or \
           loc[1] >= self.shape[1] or \
           loc[2] >= self.shape[2]:
            return None

        return self[loc[0], loc[1], loc[2]]


    def maskLabel(self, mask):
        """Looks up and returns the proportions of all regions that are present
        in the given ``mask``.

        :arg mask: A 3D :class:`.Image`` which is interpreted as a weighted
                   mask. If the ``mask`` shape does not match that of this
                   ``LabelAtlas``, it is resampled using
                   :meth:`.Image.resample`, with nearest-neighbour
                   interpolation.

        :returns:  A tuple containing:

                     - A sequence of all values  which are present in the mask
                     - A sequence containing the proportion, within the mask,
                       of each present value. The proportions are returned as
                       values between 0 and 100.

        .. note:: Use the :meth:`find` method to retrieve the ``AtlasLabel``
                  associated with each returned value.
        """

        # Extract the values that are in
        # the mask, and their corresponding
        # mask weights
        mask      = self.prepareMask(mask)
        boolmask  = mask > 0
        vals      = self[boolmask]
        weights   = mask[boolmask]
        weightsum = weights.sum()
        gotValues = np.unique(vals)
        values    = []
        props     = []

        # Only consider labels that
        # this atlas is aware of
        for label in self.desc.labels:
            if label.value in gotValues:

                # Figure out the number of all voxels
                # in the mask with this value, weighted
                # by the mask.
                prop = weights[vals == label.value].sum()

                # Normalise it to be a proportion
                # of all voxels in the mask. We
                # multiply by 100 because the FSL
                # probabilistic atlases store their
                # probabilities as percentages.
                values.append(label.value)
                props .append(100 * prop / weightsum)

        return values, props


    def get(self, label=None, index=None, value=None, name=None, binary=True):
        """Returns the binary image for the given label.

        Only one of the arguments should be used to define the label

        :arg label:  :class:`AtlasLabel` contained within this atlas
        :arg index:  index of the label
        :arg value:  value of the label
        :arg name:   string of the label
        :arg binary: If ``True`` (the default), the image will contain 1s in
                     the label region. Otherwise the image will contain the
                     label value.
        :return:     :class:`.Image` with the mask
        """
        if ((label is not None) + (index is not None) +
            (value is not None) + (name is not None)) != 1:
            raise ValueError('Only one of label, index, value, or name may be specified')
        if label is None:
            label = self.find(index=index, name=name, value=value)
        elif label not in self.desc.labels:
            raise ValueError("Unknown label provided")

        arr = (self.data == label.value).astype(np.int32)

        if not binary:
            arr[arr > 0] = label.value

        return fslimage.Image(arr, name=label.name, header=self.header)


class StatisticAtlas(Atlas):
    """A ``StatisticAtlas`` is a 4D image which contains one volume for
    each region in the atlas; each volume contains some statistic value
    for the corresponding region.

    The :class:`ProbabilisticAtlas` is a specialisation of the
    ``StatisticAtlas``
    """


    def __init__(self, atlasDesc, resolution=None, **kwargs):
        """Create a ``StatisticAtlas`` instance.

        :arg atlasDesc:  The :class:`AtlasDescription` instance describing
                         the atlas.

        :arg resolution: Desired isotropic resolution in millimetres.
        """
        Atlas.__init__(self, atlasDesc, resolution, False, **kwargs)


    def get(self, label=None, index=None, value=None, name=None):
        """Returns the statistic image at the given label.

        Only one of the arguments should be used to define the label

        :arg label: :class:`AtlasLabel` contained within this atlas
        :arg index: index of the label
        :arg value: value of the label
        :arg name:  string of the label
        :return:    :class:`.Image` with the statistic values for the
                    specified label.
        """
        if ((label is not None) + (index is not None) +
            (value is not None) + (name is not None)) != 1:
            raise ValueError('Only one of label, index, value, or name may be specified')
        if label is None:
            label = self.find(index=index, value=value, name=name)
        elif label not in self.desc.labels:
            raise ValueError("Unknown label provided")
        arr = self[..., label.index]
        return fslimage.Image(arr, name=label.name, header=self.header)


    def values(self, location, *args, **kwargs):
        """Looks up and returns the values of of all regions at the given
        location.

        :arg location: Can be one of the following:

                        - A sequence of three values, interpreted as atlas
                          coordinates. In this case, :meth:`coordValues`
                          is called.

                        - An :class:`.Image` which is interpreted as a
                          weighted mask. In this case, :meth:`maskValues`
                          is called.

        All other arguments are passed through to the :meth:`coordValues`
        or :meth:`maskValues` methods.


        :returns: The return value of either :meth:`coordValues` or
                  :meth:`maskValues`.
        """

        if isinstance(location, fslimage.Image):
            return self.maskValues(location, *args, **kwargs)
        else:
            return self.coordValues(location, *args, **kwargs)


    def coordValues(self, loc, voxel=False):
        """Looks up the region values for the given location.

        :arg loc:   A sequence of three values, interpreted as atlas
                    world or voxel coordinates.

        :arg voxel: Defaults to ``False``. If ``True``, the ``loc``
                    argument is interpreted as voxel coordinates.

        :returns: a list of values, one per region.  Returns an empty
                  list if the given location is out of bounds.
        """

        if not voxel:
            loc = affine.transform([loc], self.worldToVoxMat)[0]
            loc = [int(v) for v in loc.round()]

        if loc[0] <  0             or \
           loc[1] <  0             or \
           loc[2] <  0             or \
           loc[0] >= self.shape[0] or \
           loc[1] >= self.shape[1] or \
           loc[2] >= self.shape[2]:
            return []

        vals = self[loc[0], loc[1], loc[2], :]

        # We only return labels for this atlas -
        # the underlying image may have more
        # volumes than this atlas has labels.
        return [vals[l.index] for l in self.desc.labels]


    def maskValues(self, mask):
        """Looks up the average values of all regions in the given ``mask``.

        :arg mask: A 3D :class:`.Image`` which is interpreted as a weighted
                   mask. If the ``mask`` shape does not match that of this
                   ``StatisticAtlas``, it is resampled using
                   :meth:`Atlas.prepareMask`.

        :returns:  A sequence containing the average value, within the mask,
                   of all regions in the atlas.
        """

        avgvals   = []
        mask      = self.prepareMask(mask)
        boolmask  = mask > 0
        weights   = mask[boolmask]
        weightsum = weights.sum()

        if weightsum == 0:
            return [0.0] * len(self.desc.labels)

        for label in self.desc.labels:

            vals  = self[..., label.index]
            vals  = vals[boolmask] * weights
            val   = vals.sum() / weightsum

            avgvals.append(val)

        return avgvals


class ProbabilisticAtlas(StatisticAtlas):
    """A 4D atlas which contains one volume for each region. Each volume
    contains probabiliy values for one region, between 0 and 100.
    """


registry            = AtlasRegistry()
rescanAtlases       = registry.rescanAtlases
listAtlases         = registry.listAtlases
hasAtlas            = registry.hasAtlas
getAtlasDescription = registry.getAtlasDescription
loadAtlas           = registry.loadAtlas
addAtlas            = registry.addAtlas
removeAtlas         = registry.removeAtlas
rescanAtlases       = registry.rescanAtlases
