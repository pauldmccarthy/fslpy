#!/usr/bin/env python
#
# display.py - Definitions of the Display and DisplayOpts classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging

import numpy               as np

import props

import fsl.data.image      as fslimage
import fsl.data.strings    as strings
import fsl.utils.transform as transform


log = logging.getLogger(__name__)


class DisplayOpts(props.SyncableHasProperties):

    def __init__(self, image, display, imageList, displayCtx, parent=None):
        props.SyncableHasProperties.__init__(self, parent)
        self.image      = image
        self.displayCtx = displayCtx
        self.imageList  = imageList
        self.imageType  = image.imageType


class Display(props.SyncableHasProperties):
    """
    """

    
    name = fslimage.Image.name
    """The image name.  This property is bound to the
    :attr:`~fsl.data.image.Image.name` property.
    """

    
    imageType = fslimage.Image.imageType
    """The image data type. This property is bound to the
    :attr:`~fsl.data.image.Image.imageType` property.
    """

    
    enabled = props.Boolean(default=True)
    """Should this image be displayed at all?"""

    
    alpha = props.Real(minval=0.0, maxval=1.0, default=1.0)
    """Transparency - 1.0 is fully opaque, and 0.0 is fully transparent."""

    
    resolution = props.Real(maxval=10,
                            default=1,
                            clamped=True,
                            editLimits=False)
    """Data resolution in world space. The minimum value is set in __init__.""" 
                              
    
    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If a 4D image, the current volume to display."""


    syncVolume = props.Boolean(default=True)

    
    transform = props.Choice(
        ('affine', 'pixdim', 'id'),
        labels=[strings.choices['Display.transform.affine'],
                strings.choices['Display.transform.pixdim'],
                strings.choices['Display.transform.id']],
        default='pixdim')
    """This property defines how the image should be transformd into the display
    coordinate system.
    
      - ``affine``: Use the affine transformation matrix stored in the image
        (the ``qform``/``sform`` fields in NIFTI1 headers).
                    
      - ``pixdim``: Scale voxel sizes by the ``pixdim`` fields in the image
        header.
    
      - ``id``: Perform no scaling or transformation - voxels will be
        interpreted as :math:`1mm^3` isotropic, with the origin at voxel
        (0,0,0).
    """


    interpolation = props.Choice(
        ('none', 'linear', 'spline'),
        labels=[strings.choices['Display.interpolation.none'],
                strings.choices['Display.interpolation.linear'],
                strings.choices['Display.interpolation.spline']])
    """How the value shown at a real world location is derived from the
    corresponding voxel value(s). 'No interpolation' is equivalent to nearest
    neighbour interpolation.
    """

        
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()


    def __init__(self, image, imageList, displayCtx, parent=None):
        """Create a :class:`Display` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.

        :arg parent: 
        """
        self.image      = image
        self.imageList  = image
        self.displayCtx = displayCtx

        # bind self.name to image.name, so changes
        # in one are propagated to the other
        self.bindProps('name',      image)
        self.bindProps('imageType', image)

        # The display<->* transformation matrices
        # are created in the _transformChanged method
        self.voxToWorldMat     = image.voxToWorldMat.transpose()
        self.worldToVoxMat     = image.worldToVoxMat.transpose()
        self.voxToDisplayMat   = None
        self.displayToVoxMat   = None
        self.worldToDisplayMat = None
        self.displayToWorldMat = None

        # is this a 4D volume?
        if image.is4DImage():
            self.setConstraint('volume', 'maxval', image.shape[3] - 1)

        # Update transformation matrices when
        # the transform property changes
        self.addListener(
            'transform',
            'Display_{}'.format(id(self)),
            self.__transformChanged)

        self.addListener(
            'imageType',
            'Display_{}'.format(id(self)),
            self.__imageTypeChanged) 

        self.__transformChanged()
        
        # When the transform property changes,
        # the display<->* transformation matrices
        # are recalculated. References to the
        # previous matrices are stored here, just
        # in case anything (hint the DisplayContext
        # object) needs them for any particular
        # reason (hint: so the DisplayContext can
        # preserve the current display location,
        # in terms of image world space, when the
        # transform of the selected changes)
        self._oldVoxToDisplayMat   = self.voxToDisplayMat
        self._oldDisplayToVoxMat   = self.displayToVoxMat
        self._oldWorldToDisplayMat = self.worldToDisplayMat
        self._oldDisplayToWorldMat = self.displayToWorldMat

        # limit resolution to the image dimensions
        self.resolution = min(image.pixdim[:3])
        self.setConstraint('resolution',   'minval', self.resolution)

        # Call the super constructor after our own
        # initialisation, in case the provided parent
        # has different property values to our own,
        # and our values need to be updated
        props.SyncableHasProperties.__init__(
            self,
            parent,
            
            # The name property is implicitly bound
            # through the image object so it doesn't
            # need to be linked between ImageDisplays 
            nobind=['name'],
            
            # These properties cannot be unbound, as
            # they affect the OpenGL representation
            nounbind=['interpolation',
                      'volume',
                      'resolution',
                      'transform',
                      'imageType'])

        self.__displayOpts = None
        self.__imageTypeChanged()

        
    def getDisplayBounds(self):
        """Calculates and returns the min/max values of a 3D bounding box,
        in the display coordinate system, which is big enough to contain
        the image associated with this :class:`ImageDisplay` instance.

        The coordinate system in which the bounding box is defined is
        determined by the current value of the :attr:`transform` property.

        A tuple containing two values is returned, with the first value
        a sequence of three low bounds, and the second value a sequence
        of three high bounds.
        """
        return transform.axisBounds(self.image.shape[:3], self.voxToDisplayMat)

    
    def getDisplayOpts(self):
        """
        """

        if (self.__displayOpts           is None) or \
           (self.__displayOpts.imageType != self.imageType):
            
            self.__displayOpts = self.__makeDisplayOpts()
            
        return self.__displayOpts


    def __makeDisplayOpts(self):
        """
        """

        import volumeopts
        import tensoropts
        import maskopts        
        
        if self.getParent() is None:
            oParent = None
        else:
            oParent = self.getParent().getDisplayOpts()

        optsMap = {
            'volume' : volumeopts.VolumeOpts,
            'tensor' : tensoropts.TensorOpts,
            'mask'   : maskopts.  MaskOpts
        }

        optType = optsMap[self.imageType]
        log.debug('Creating DisplayOpts for image {}: {}'.format(
            self.name,
            optType.__name__))
        
        return optType(self.image,
                       self,
                       self.imageList,
                       self.displayCtx,
                       oParent)

    
    def __imageTypeChanged(self, *a):
        """
        """

        # make sure that the display
        # options instance is up to date
        self.getDisplayOpts()

        
    def __transformChanged(self, *a):
        """Called when the :attr:`transform` property is changed.

        Generates transformation matrices for transforming between voxel and
        display coordinate space.

        If :attr:`transform` is set to ``affine``, the :attr:`interpolation`
        property is changed to ``spline. Otherwise, it is set to ``none``.
        """

        # Store references to the previous display related
        # transformation matrices (see comments in __init__)
        self._oldVoxToDisplayMat   = self.voxToDisplayMat
        self._oldDisplayToVoxMat   = self.displayToVoxMat
        self._oldWorldToDisplayMat = self.worldToDisplayMat
        self._oldDisplayToWorldMat = self.displayToWorldMat

        # The transform property defines the way
        # in which image voxel coordinates map
        # to the display coordinate system
        if self.transform == 'id':
            pixdim          = [1.0, 1.0, 1.0]
            voxToDisplayMat = np.eye(4)
            
        elif self.transform == 'pixdim':
            pixdim          = self.image.pixdim
            voxToDisplayMat = np.diag([pixdim[0], pixdim[1], pixdim[2], 1.0])
            
        elif self.transform == 'affine':
            voxToDisplayMat = self.voxToWorldMat

        # for pixdim/identity transformations, we want the world
        # location (0, 0, 0) to map to voxel location (0, 0, 0)
        if self.transform in ('id', 'pixdim'):
            for i in range(3):
                voxToDisplayMat[3, i] =  pixdim[i] * 0.5

        # Transformation matrices for moving between the voxel
        # coordinate system and the display coordinate system
        self.voxToDisplayMat = np.array(voxToDisplayMat, dtype=np.float32)
        self.displayToVoxMat = transform.invert(self.voxToDisplayMat)

        # Matrices for moving between the display coordinate
        # system, and the image world coordinate system
        self.displayToWorldMat = transform.concat(self.displayToVoxMat,
                                                  self.voxToWorldMat)
        self.worldToDisplayMat = transform.invert(self.displayToWorldMat)

        # When transform is changed to 'affine', enable interpolation
        # and, when changed to 'pixdim' or 'id', disable interpolation
        if self.transform == 'affine': self.interpolation = 'spline'
        else:                          self.interpolation = 'none'
