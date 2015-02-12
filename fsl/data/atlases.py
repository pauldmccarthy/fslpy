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
import                          logging

import numpy                 as np

import fsl.data.image        as fslimage
import fsl.utils.transform   as transform


log = logging.getLogger(__name__)


if os.environ.get('FSLDIR', None) is None:
    log.warn('$FSLDIR is not set - atlases are not available')

    ATLAS_DIR = None
else:
    ATLAS_DIR = op.join(os.environ['FSLDIR'], 'data', 'atlases')

    
def listAtlases():
    """Returns a dictionary containing :class:`AtlasDescription` objects for
    all available atlases.
    """


    atlasFiles = glob.glob(op.join(ATLAS_DIR, '*.xml'))
    atlasDescs = map(AtlasDescription, atlasFiles)

    return {d.key: d for d in atlasDescs}


class AtlasDescription(object):
    """Loads the data stored in an Atlas XML description, and makes said
    information accessible via instance attributes.
    """

    
    def __init__(self, filename):

        log.debug('Loading atlas description from {}'.format(filename))

        root   = et.parse(filename)
        header = root.find('header')
        data   = root.find('data')

        self.key       = op.splitext(op.basename(filename))[0]
        self.name      = header.find('name').text
        self.atlasType = header.find('type').text

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
            al.index  = label.attrib['index']
            al.x      = label.attrib['x']
            al.y      = label.attrib['y']
            al.z      = label.attrib['z']

            coords[i] = (al.x, al.y, al.z)

            self.labels.append(al)

        # Load the appropriate transformation matrix
        # and transform all those voxel coordinates
        xform  = fslimage.Image(self.images[0], loadData=False).voxToWorldMat
        coords = transform.transform(coords, xform)

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

        
class LabelAtlas(fslimage.Image):

    def __init__(self, atlasDesc):
        Atlas.__init__(self, atlasDesc, isLabel=True)

    def label(self, voxelLoc):
        val = self.data[voxelLoc[0], voxelLoc[1], voxelLoc[2]]

        if self.atlasDesc.atlasType == 'Label':
            return self.atlasDesc.label[val]
        
        elif self.atlasDesc.atlasType == 'Probabilistic':
            return self.atlasDesc.label[val - 1]

    
class ProbabilisticAtlas(fslimage.Image):

    def __init__(self, atlasDesc):
        Atlas.__init__(self, atlasDesc, isLabel=False)

        
    def proportions(self, voxelLoc):
        props = self.data[voxelLoc[0], voxelLoc[1], voxelLoc[2], :]
        return zip(self.atlasDesc.labels, props)
