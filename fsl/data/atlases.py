#!/usr/bin/env python
#
# atlases.py - API which provides access to the atlas image files contained 
#              in $FSLDIR/data/atlases/
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides access to the atlas images which are contained in
``$FSLDIR/data/atlases/``.

Instances of the :class:`Atlas` class is a

MNI152


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
  # index - index of corresponding volume in 4D image file
  # x    |
  # y    |- XYZ *voxel* coordinates into the first image of the <images> list
  # z    |
  <label index="0" x="0" y="0" z="0">Name</label>
  ...
 </data>
</atlas>
"""

import                          os
import xml.etree.ElementTree as et
import os.path               as op
import                          glob
import                          collections
import                          logging

import numpy                 as np

import fsl.data.image        as fslimage
import fsl.data.constants    as constants
import fsl.utils.transform   as transform


log = logging.getLogger(__name__)


if os.environ.get('FSLDIR', None) is None:
    log.warn('$FSLDIR is not set - atlases are not available')

    ATLAS_DIR = None
else:
    ATLAS_DIR = op.join(os.environ['FSLDIR'], 'data', 'atlases')


ATLAS_DESCRIPTIONS = collections.OrderedDict()

    
def listAtlases(refresh=False):
    """Returns a dictionary containing :class:`AtlasDescription` objects for
    all available atlases.

    :arg refresh: If ``True``, or if the atlas desriptions have not
                  previously been loaded, atlas descriptions are
                  loaded from the atlas files. Otherwise, prefviously
                  loaded descriptions are returned (see 
                  :attr:`ATLAS_DESCRIPTIONS`).
    """

    if ATLAS_DIR is None:
        return []

    if len(ATLAS_DESCRIPTIONS) == 0:
        refresh = True

    if not refresh:
        return ATLAS_DESCRIPTIONS.values()

    atlasFiles = glob.glob(op.join(ATLAS_DIR, '*.xml'))
    atlasDescs = map(AtlasDescription, atlasFiles)
    atlasDescs = sorted(atlasDescs, key=lambda d: d.name)

    ATLAS_DESCRIPTIONS.clear()

    for i, desc in enumerate(atlasDescs):
        desc.index                       = i
        ATLAS_DESCRIPTIONS[desc.atlasID] = desc
        

    return atlasDescs


def getAtlasDescription(atlasID):
    """Returns an :class:`AtlasDescription` instance describing the
    atlas with the given ``atlasID``.
    """

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
    """Loads the data stored in an Atlas XML description, and makes said
    information accessible via instance attributes.
    """

    
    def __init__(self, filename):

        log.debug('Loading atlas description from {}'.format(filename))

        root   = et.parse(filename)
        header = root.find('header')
        data   = root.find('data')

        self.atlasID   = op.splitext(op.basename(filename))[0]
        self.name      = header.find('name').text
        self.atlasType = header.find('type').text.lower()
 
        # Spelling error in some of the atlas.xml files.
        if self.atlasType == 'probabalistic':
            self.atlasType = 'probabilistic'

        images             = header.findall('images')
        self.images        = []
        self.summaryImages = []

        for image in images:
            imagefile        = image.find('imagefile')       .text
            summaryimagefile = image.find('summaryimagefile').text

            imagefile        = op.join(ATLAS_DIR, '.' + imagefile)
            summaryimagefile = op.join(ATLAS_DIR, '.' + summaryimagefile)

            self.images       .append(imagefile)
            self.summaryImages.append(summaryimagefile)

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
        xform  = fslimage.Image(self.images[0], loadData=False).voxToWorldMat
        coords = transform.transform(coords, xform.T)

        # Update the coordinates 
        # in our label objects
        for i, label in enumerate(self.labels):

            label.x, label.y, label.z = coords[i]


class Atlas(fslimage.Image):
    
    def __init__(self, atlasDesc, isLabel=False):

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

    def __init__(self, atlasDesc):
        Atlas.__init__(self, atlasDesc, isLabel=True)

    def label(self, worldLoc):

        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat.T)[0]

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

    def __init__(self, atlasDesc):
        Atlas.__init__(self, atlasDesc, isLabel=False)

        
    def proportions(self, worldLoc):
        voxelLoc = transform.transform([worldLoc], self.worldToVoxMat.T)[0]

        if voxelLoc[0] <  0             or \
           voxelLoc[1] <  0             or \
           voxelLoc[2] <  0             or \
           voxelLoc[0] >= self.shape[0] or \
           voxelLoc[1] >= self.shape[1] or \
           voxelLoc[2] >= self.shape[2]:
            return np.nan
        
        return self.data[voxelLoc[0], voxelLoc[1], voxelLoc[2], :]
