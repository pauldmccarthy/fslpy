#!/usr/bin/env python
#
# atlases.py - API which provides access to the atlas image files contained 
#              in $FSLDIR/data/atlases/
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides access to the atlas images which are contained in
``$FSLDIR/data/atlases/``. This directory contains XML files which describe
all of the available atlases.  An XML atlas description file is assumed to
have a structure that looks like the following:

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
                            # below)

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


This module reads in all of these XML files, and builds a list of
:class:`AtlasDescription` instances, each of which contains information about
one atlas. Each atlas is assigned an identifier, which is simply the XML file
name describing the atlas, sans-suffix, and converted to lower case.  For
exmaple, the atlas described by:

    ``$FSLDIR/data/atlases/HarvardOxford-Cortical.xml``

is given the identifier

    ``harvardoxford-cortical``


The following functions provide access to the available
:class:`AtlasDescription` instances:

.. autosummary::
   :nosignatures:

   listAtlases
   getAtlasDescription


The :func:`loadAtlas` function allows you to load an atlas image, which will
be one of the following  atlas-specific :class:`.Image` sub-classes:

.. autosummary::
   :nosignatures:

   LabelAtlas
   ProbabilisticAtlas
"""


import                          os
import xml.etree.ElementTree as et
import os.path               as op
import                          glob
import                          collections
import                          threading
import                          logging

import numpy                 as np

import fsl.data.image        as fslimage
import fsl.data.constants    as constants
import fsl.utils.transform   as transform


log = logging.getLogger(__name__)


def listAtlases(refresh=False):
    """Returns a list containing :class:`AtlasDescription` objects for
    all available atlases.

    :arg refresh: If ``True``, or if the atlas desriptions have not
                  previously been loaded, atlas descriptions are
                  loaded from the atlas files. Otherwise, previously
                  loaded descriptions are returned (see 
                  :attr:`ATLAS_DESCRIPTIONS`).

    .. note:: This function is thread-safe, because *FSLeyes* calls it
              in a multi-threaded manner (to avoid blocking the GUI).
    """

    _setAtlasDir()

    if ATLAS_DIR is None:
        return []
    
    # Make sure the atlas description
    # refresh is only performed by one
    # thread. If a thread is loading
    # the descriptions, any other thread
    # which enters the function will
    # block here until the descriptions
    # are loaded. When it continues,
    # it will see a populated
    # ATLAS_DESCRIPTIONS list.
    LOAD_ATLAS_LOCK.acquire()

    if len(ATLAS_DESCRIPTIONS) == 0:
        refresh = True

    try:
        if refresh:

            log.debug('Loading atlas descriptions')
            
            atlasFiles = glob.glob(op.join(ATLAS_DIR, '*.xml'))
            atlasDescs = map(AtlasDescription, atlasFiles)
            atlasDescs = sorted(atlasDescs, key=lambda d: d.name)

            ATLAS_DESCRIPTIONS.clear()

            for i, desc in enumerate(atlasDescs):
                desc.index                       = i
                ATLAS_DESCRIPTIONS[desc.atlasID] = desc
        else:
            atlasDescs = list(ATLAS_DESCRIPTIONS.values())

    finally:
        LOAD_ATLAS_LOCK.release()

    return list(atlasDescs)


def getAtlasDescription(atlasID):
    """Returns an :class:`AtlasDescription` instance describing the
    atlas with the given ``atlasID``.
    """

    _setAtlasDir()

    if ATLAS_DIR is None:
        return None
    
    if len(ATLAS_DESCRIPTIONS) == 0:
        listAtlases()

    return ATLAS_DESCRIPTIONS[atlasID]


def loadAtlas(atlasID, loadSummary=False):
    """Loads and returns an :class:`Atlas` instance for the atlas
    with the given  ``atlasID``. 

    :arg loadSummary: If ``True``, a 3D :class:`LabelAtlas` image is
                      loaded. Otherwise, if the atlas is probabilistic,
                      a 4D :class:`ProbabilisticAtlas` image is loaded.
    """

    _setAtlasDir()

    if ATLAS_DIR is None:
        return None
    
    if len(ATLAS_DESCRIPTIONS) == 0:
        listAtlases()

    atlasDesc = ATLAS_DESCRIPTIONS[atlasID]

    # label atlases are only
    # available in 'summary' form
    if atlasDesc.atlasType == 'label':
        loadSummary = True

    if loadSummary: atlas = LabelAtlas(        atlasDesc)
    else:           atlas = ProbabilisticAtlas(atlasDesc)

    return atlas


class AtlasDescription(object):
    """An ``AtlasDescription`` instance parses and stores the information
    stored in the XML file that describes one atlas.

    The following attributes are available on an ``AtlasDescription`` instance:

    ================= ======================================================
    ``atlasID``       The atlas ID, as described above.
    
    ``name``          Name of the atlas.
    
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
    
    ``labels``        A list of ``AtlasLabel`` objects, describing each
                      region / label in the atlas.
    ================= ======================================================

    Each ``AtlasLabel`` instance in the ``labels`` list contains the
    following attributes:

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
              matrix for the first image in the ``images`` list.(typically
              MNI152 space).
    """

    
    def __init__(self, filename):
        """Create an ``AtlasDescription`` instance.

        :arg filename: Name of the XML file describing the atlas.
        """

        log.debug('Loading atlas description from {}'.format(filename))

        root   = et.parse(filename)
        header = root.find('header')
        data   = root.find('data')

        self.atlasID   = op.splitext(op.basename(filename))[0].lower()
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
        

        for image in images:
            imagefile        = image.find('imagefile')       .text
            summaryimagefile = image.find('summaryimagefile').text

            imagefile        = op.join(ATLAS_DIR, '.' + imagefile)
            summaryimagefile = op.join(ATLAS_DIR, '.' + summaryimagefile)

            i = fslimage.Image(imagefile, loadData=False)

            self.images       .append(imagefile)
            self.summaryImages.append(summaryimagefile)
            self.pixdims      .append(i.pixdim[:3])
            self.xforms       .append(i.voxToWorldMat)

        # A container object used for
        # storing atlas label information
        class AtlasLabel(object):
            pass

        labels      = data.findall('label')
        self.labels = []

        # The xyz coordinates for each label are in terms
        # of the voxel space of the first images element
        # in the header. For convenience, we're going to
        # transform all of these voxel coordinates into
        # MNI152 space coordinates.
        coords = np.zeros((len(labels), 3), dtype=np.float32)

        for i, label in enumerate(labels):
            
            al        = AtlasLabel()
            al.name   = label.text
            al.index  = int(  label.attrib['index'])
            al.x      = float(label.attrib['x'])
            al.y      = float(label.attrib['y'])
            al.z      = float(label.attrib['z'])

            coords[i] = (al.x, al.y, al.z)

            self.labels.append(al)

        # Load the appropriate transformation matrix
        # and transform all those voxel coordinates
        # into world coordinates
        coords = transform.transform(coords, self.xforms[0].T)

        # Update the coordinates 
        # in our label objects
        for i, label in enumerate(self.labels):

            label.x, label.y, label.z = coords[i]


class Atlas(fslimage.Image):
    """This is the base class for the :class:`LabelAtlas` and
    :class:`ProbabilisticAtlas` classes. It contains some initialisation
    logic common to both.
    """

    
    def __init__(self, atlasDesc, isLabel=False):
        """Initialise an ``Atlas``.

        :arg atlasDesc: The :class:`AtlasDescription` instance which describes
                        the atlas.

        :arg isLabel:   Pass in ``True`` for label atlases, ``False`` for
                        probabilistic atlases.
        """

        # Choose the atlas image
        # with the highest resolution 
        minImageRes = 2 ** 32
        imageIdx    = 0

        for i, image in enumerate(atlasDesc.images):
            imgRes = max(fslimage.Image(image, loadData=False).pixdim)

            if imgRes < minImageRes:
                minImageRes = imgRes
                imageIdx    = i

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

    def __init__(self, atlasDesc):
        """Create a ``LabelAtlas`` instance.

        :arg atlasDesc: The :class:`AtlasDescription` instance describing
                        the atlas.
        """
        Atlas.__init__(self, atlasDesc, isLabel=True)

        
    def label(self, worldLoc):
        """Looks up and returns the label of the region at the given world
        location, or ``np.nan`` if the location is out of bounds.
        """

        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat.T)[0]
        voxelLoc = voxelLoc.round()

        if voxelLoc[0] <  0             or \
           voxelLoc[1] <  0             or \
           voxelLoc[2] <  0             or \
           voxelLoc[0] >= self.shape[0] or \
           voxelLoc[1] >= self.shape[1] or \
           voxelLoc[2] >= self.shape[2]:
            return np.nan        
        
        val = self.data[voxelLoc[0], voxelLoc[1], voxelLoc[2]]

        if self.desc.atlasType == 'label':
            return val
        
        elif self.desc.atlasType == 'probabilistic':
            return val - 1

    
class ProbabilisticAtlas(Atlas):
    """A 4D atlas which contains one volume for each region.

    The ``ProbabilisticAtlas`` provides the :meth`proportions` method,
    which makes looking up region probabilities easy.
    """

    def __init__(self, atlasDesc):
        """Create a ``ProbabilisticAtlas`` instance.

        :arg atlasDesc: The :class:`AtlasDescription` instance describing
                        the atlas.
        """ 
        Atlas.__init__(self, atlasDesc, isLabel=False)

        
    def proportions(self, worldLoc):
        """Looks up the region probabilities for the given location.

        :arg worldLoc: Location in the world coordinate system.

        :returns: a list of values, one per region, which represent
                  the probability of each region for the specified
                  location. Returns an empty list if the given
                  location is out of bounds.
        """
        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat.T)[0]
        voxelLoc = [int(v) for v in voxelLoc.round()]

        if voxelLoc[0] <  0             or \
           voxelLoc[1] <  0             or \
           voxelLoc[2] <  0             or \
           voxelLoc[0] >= self.shape[0] or \
           voxelLoc[1] >= self.shape[1] or \
           voxelLoc[2] >= self.shape[2]:
            return []
        
        return self.data[voxelLoc[0], voxelLoc[1], voxelLoc[2], :]



ATLAS_DIR = None
"""This attribute stores the absolute path to ``$FSLDIR/data/atlases/``. It is
``None`` if ``$FSLDIR`` is not set. See :func:`_setAtlasDir`.
"""


ATLAS_DESCRIPTIONS = collections.OrderedDict()
"""This dictionary contains an ``{atlasID : AtlasDescription}`` mapping for
all atlases contained in ``$FSLDIR/data/atlases/``.
"""


LOAD_ATLAS_LOCK = threading.Lock()
"""This is used as a mutual-exclusion lock by the :func:`listAtlases`
function, to make it thread-safe.
"""


def _setAtlasDir():
    """Called by the :func:`listAtlases`, :func:`getAtlasDescription` and
    :func:`loadAtlas` functions.

    Sets the :data:`ATLAS_DIR` attribute if it has not already been set, and
    if the ``$FSLDIR`` environment variable is set.
    """
    global ATLAS_DIR

    if ATLAS_DIR is not None:
        return
    
    if os.environ.get('FSLDIR', None) is None:
        log.warn('$FSLDIR is not set - atlases are not available')
    else:
        ATLAS_DIR = op.join(os.environ['FSLDIR'], 'data', 'atlases')
