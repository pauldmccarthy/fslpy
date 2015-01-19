#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

import props

import fsl.data.image      as fslimage
import fsl.data.strings    as strings
import fsl.utils.transform as transform


def _makeDisplay(image, parent):
    
    import imagedisplay
    # import maskdisplay
    
    if image.imageType == 'volume':
        return imagedisplay.ImageDisplay(image, parent)
    # elif image.type == 'mask': return maskdisplay.MaskDisplay(image, parent)


class Display(props.SyncableHasProperties):
    """
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
        labels=[strings.choices['ImageDisplay.transform.affine'],
                strings.choices['ImageDisplay.transform.pixdim'],
                strings.choices['ImageDisplay.transform.id']],
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
        labels=[strings.choices['ImageDisplay.interpolation.none'],
                strings.choices['ImageDisplay.interpolation.linear'],
                strings.choices['ImageDisplay.interpolation.spline']])
    """How the value shown at a real world location is derived from the
    corresponding voxel value(s). 'No interpolation' is equivalent to nearest
    neighbour interpolation.
    """

    
    name = fslimage.Image.name
    """The image name.  This property is bound to the
    :attr:`~fsl.data.image.Image.name` property.
    """

    
    imageType = fslimage.Image.imageType
    """The image data type. This property is bound to the
    :attr:`~fsl.data.image.Image.imageType` property.
    """

        
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()


    def __init__(self, image, parent=None):
        """Create an :class:`ImageDisplay` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.

        :arg parent: 
        """
        self.image = image

        # bind self.name to # image.name, so changes
        # in one are propagated to the other
        self.bindProps('name', image)

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
            'ImageDisplay_{}'.format(id(self)),
            self._transformChanged)

        self._transformChanged()
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
        

class DisplayContext(props.SyncableHasProperties):
    """Contains a number of properties defining how an
    :class:`~fsl.dat.aimage.ImageList` is to be displayed.
    """

    
    selectedImage = props.Int(minval=0, default=0, clamped=True)
    """Index of the currently 'selected' image.

    Note that this index is in relation to the
    :class:`~fsl.data.image.ImageList`, rather than to the :attr:`imageOrder`
    list.

    If you're interested in the currently selected image, you must also listen
    for changes to the :attr:`fsl.data.image.ImageList.images` list as, if the
    list changes, the :attr:`selectedImage` index may not change, but the
    image to which it points may be different.
    """


    location = props.Point(ndims=3, labels=('X', 'Y', 'Z'))
    """The location property contains the currently selected
    3D location (xyz) in the image list space. 
    """

    
    bounds = props.Bounds(ndims=3)
    """This property contains the min/max values of a bounding box (in display
    coordinates) which is big enough to contain all of the images in the
    :attr:`images` list. This property shouid be read-only, but I don't have a
    way to enforce it (yet).
    """


    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """The volume property contains the currently selected volume
    across the 4D images in the :class:`~fsl.data.image/ImageList`.
    This property may not be relevant to all images in the image list
    (i.e. it is meaningless for 3D images).
    """


    imageOrder = props.List(props.Int())
    """A list of indices into the :attr:`~fsl.data.image.ImageList.images`
    list, defining the order in which the images are to be displayed.

    See the :meth:`getOrderedImages` method.
    """


    def __init__(self, imageList, parent=None):
        """Create a :class:`DisplayContext` object.

        :arg imageList: A :class:`~fsl.data.image.ImageList` instance.

        :arg parent: Another :class`DisplayContext` instance to be used
        as the parent of this instance.
        """

        props.SyncableHasProperties.__init__(self, parent, nounbind=('volume'))
        
        self._imageList = imageList
        self._name = '{}_{}'.format(self.__class__.__name__, id(self))

        # Keep track of the image list length
        # so we can do some things in the
        # _imageListChanged method
        self._prevImageListLen = 0

        # Ensure that an ImageDisplay object exists for
        # every image, and that the display bounds
        # property is initialised

        self._imageDisplays = {}
        self._imageListChanged()

        imageList.addListener('images',
                              self._name,
                              self._imageListChanged)
        self.addListener(     'bounds',
                              self._name,
                              self._boundsChanged)
        self.addListener(     'volume',
                              self._name,
                              self._volumeChanged)


    def getDisplayProperties(self, image):
        """Returns the display property object (e.g. an :class:`ImageDisplay`
        object) for the specified image (or image index).

        If an :class:`ImageDisplay` object does not exist for the given image,
        one is created.
        """
        if isinstance(image, int):
            image = self._imageList[image]

        try:
            display = self._imageDisplays[image]
                
        except KeyError:
                
            if self.getParent() is None:
                dParent = None
            else:
                dParent = self.getParent().getDisplayProperties(image)

            display = _makeDisplay(image, dParent)
            self._imageDisplays[image] = display
        
        return display

    
    def selectImage(self, image):
        self.selectedImage = self._imageList.index(image)

    
    def getSelectedImage(self):
        """Returns the currently selected :class:`~fsl.data.image.Image`
        object, or ``None`` if there are no images.
        """
        if len(self._imageList) == 0: return None
        return self._imageList[self.selectedImage]

    
    def getImageOrder(self, image):
        """Returns the order in which the given image (or an index into
        the :class:`~fsl.data.image.ImageList` list) should be displayed
        (see the :attr:`imageOrder property).
        """
        if isinstance(image, fslimage.Image):
            image = self._imageList.index(image)
        return self.imageOrder.index(image)

    
    def getOrderedImages(self):
        """Returns a list of :class:`~fsl.data.image.Image` objects from
        the :class:`~fsl.data.image.ImageList` list, sorted into the order
        that they are to be displayed.
        """
        return [self._imageList[idx] for idx in self.imageOrder]


    def _imageListChanged(self, *a):
        """Called when the :attr:`fsl.data.image.ImageList.images` property
        changes.

        Ensures that an :class:`ImageDisplay` object exists for every image,
        and updates the constraints on the :attr:`selectedImage` and
        :attr:`volume` properties.
        """

        nimages = len(self._imageList)

        # Ensure that an ImageDisplay
        # object exists for every image
        for image in self._imageList:

            # The getDisplayProperties method
            # will create an ImageDisplay object
            # if one does not already exist
            display = self.getDisplayProperties(image)

            # Register a listener with the transform property
            # of every image display so that when they change,
            # we can update the display bounds, and preserve
            # the current display location so that it is in
            # terms of the world location of the currently
            # selected image
            # 
            # This may be called multiple times on each image,
            # but it doesn't matter, as any listener which has
            # previously been registered with an image will
            # just be replaced by the new one here.
            display.addListener(
                'transform',
                self.__class__.__name__,
                self._transformChanged,
                overwrite=True)


        # Ensure that the imageOrder
        # property is valid ...
        # 
        # If images have been added to
        # the image list, add indices
        # for them to the imageOrder list
        if len(self.imageOrder) < len(self._imageList):
            self.imageOrder.extend(range(len(self.imageOrder),
                                         len(self._imageList)))

        # Otherwise, if images have been removed
        # from the image list, remove the corresponding
        # indices from the imageOrder list
        elif len(self.imageOrder) > len(self._imageList):
            for idx in range(len(self._imageList),
                             len(self.imageOrder)):
                self.imageOrder.remove(idx)

        # Ensure that the bounds property is accurate
        self._updateBounds()

        # If the image list was empty,
        # and is now non-empty, centre
        # the currently selected location
        if (self._prevImageListLen == 0) and (len(self._imageList) > 0):
            
            # initialise the location to be
            # the centre of the image world
            b = self.bounds
            self.location.xyz = [
                b.xlo + b.xlen / 2.0,
                b.ylo + b.ylen / 2.0,
                b.zlo + b.zlen / 2.0]
            
        self._prevImageListLen = len(self._imageList)
 
        # Limit the selectedImage property
        # so it cannot take a value greater
        # than len(imageList)-1
        if nimages > 0:
            self.setConstraint('selectedImage', 'maxval', nimages - 1)
        else:
            self.setConstraint('selectedImage', 'maxval', 0)

        # Limit the volume property so it
        # cannot take a value greater than
        # the longest 4D volume in the
        # image list
        maxvols = 0

        for image in self._imageList:

            if not image.is4DImage(): continue

            if image.shape[3] > maxvols:
                maxvols = image.shape[3]

        if maxvols > 0:
            self.setConstraint('volume', 'maxval', maxvols - 1)
        else:
            self.setConstraint('volume', 'maxval', 0)


    def _transformChanged(self, xform, valid, display, propName):
        """Called when the
        :attr:`~fsl.fslview.displaycontext.ImageDisplay.transform property
        changes on any image in the :attr:`images` list. Sets the 
        :attr:`location` property, so that the selected image world location
        is preserved, in the new display coordinate system.
        """

        if display.image != self.getSelectedImage():
            self._updateBounds()
            return

        # Calculate the image world location using
        # the old display<-> world transform, then
        # transform it back to the new world->display
        # transform
        imgWorldLoc = transform.transform([self.location.xyz],
                                          display._oldDisplayToWorldMat)[0]
        newDispLoc  = transform.transform([imgWorldLoc],
                                          display.worldToDisplayMat)[0]

        # Update the display coordinate system bounds -
        # this will also update the constraints on the
        # location property, so we have to do this first
        # before setting said location property.
        self._updateBounds()
        
        self.location.xyz = newDispLoc


    def _updateBounds(self, *a):
        """Called when the image list changes, or when any image display
        transform is changed. Updates the :attr:`bounds` property.
        """

        if len(self._imageList) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]

        for img in self._imageList.images:

            display = self._imageDisplays[img]
            lo, hi  = display.getDisplayBounds()

            for ax in range(3):

                if lo[ax] < minBounds[ax]: minBounds[ax] = lo[ax]
                if hi[ax] > maxBounds[ax]: maxBounds[ax] = hi[ax]

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]] 
 
    
    def _volumeChanged(self, *a):
        """Called when the :attr:`volume` property changes.

        Propagates the change on to the :attr:`ImageDisplay.volume` property
        for each image in the :class:`~fsl.data.image.ImageList`.
        """

        for image in self._imageList:

            display = self._imageDisplays[image]
            
            # The volume property for each image should
            # be clamped to the possible value for that
            # image, so we don't need to check if the
            # current volume value is valid for each image
            if display.syncVolume:
                display.volume = self.volume

            
    def _boundsChanged(self, *a):
        """Called when the :attr:`bounds` property changes.

        Updates the constraints on the :attr:`location` property.
        """

        self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
        self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
        self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)
