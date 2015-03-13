#!/usr/bin/env python
#
# displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging

import props

import fsl.data.image      as fslimage
import fsl.utils.transform as transform

import display as fsldisplay


log = logging.getLogger(__name__)


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
    3D location (xyz) in the current display coordinate system.
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

        if not isinstance(image, (int, fslimage.Image)):
            raise ValueError('image must be an integer or an Image object')

        if isinstance(image, int):
            image = self._imageList[image]

        try:
            display = self._imageDisplays[image]
                
        except KeyError:
                
            if self.getParent() is None:
                dParent = None
            else:
                dParent = self.getParent().getDisplayProperties(image)

            display = fsldisplay.Display(image, self._imageList, self, dParent)
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

        # This check is ugly, and is required due to
        # an ugly circular relationship which exists
        # between parent/child DCs and the transform/
        # location properties:
        # 
        # 1. When the transform property of a child DC
        #    Display object changes (this should always 
        #    be due to user input), that change is 
        #    propagated to the parent DC Display object.
        #
        # 2. This results in the DC._transformChanged
        #    method (this method) being called on the
        #    parent DC.
        #
        # 3. Said method correctly updates the DC.location
        #    property, so that the world location of the
        #    selected image is preserved.
        #
        # 4. This location update is propagated back to
        #    the child DC.location property, which is
        #    updated to have the new correct location
        #    value.
        #
        # 5. Then, the child DC._transformChanged method
        #    is called, which goes and updates the child
        #    DC.location property to contain a bogus
        #    value.
        #
        # So this test is in place to prevent this horrible
        # circular loop behaviour from occurring. If the
        # location properties are synced, and contain the
        # same value, we assume that they don't need to be
        # updated again, and escape from ths system.
        if self.getParent() is not None and self.isSyncedToParent('location'):
            if self.getParent().location == self.location:
                return

        if display.image != self.getSelectedImage():
            self._updateBounds()
            return

        # Calculate the image world location using
        # the old display<-> world transform, then
        # transform it back to the new world->display
        # transform
        
        imgWorldLoc = transform.transform(
            [self.location.xyz],
            display.getTransform(display.getLastTransform(), 'world'))[0]
        newDispLoc  = transform.transform(
            [imgWorldLoc],
            display.getTransform('world', 'display'))[0]

        # Update the display coordinate 
        # system bounds, and the location
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
