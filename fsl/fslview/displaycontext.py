#!/usr/bin/env python
#
# displaycontext.py - Classes which define how images should be displayed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import collections
from   collections import OrderedDict

import numpy         as np

import props

import fsl.data.image         as fslimage
import fsl.utils.transform    as transform
import fsl.fslview.colourmaps as fslcm

class ImageDisplay(props.SyncableHasProperties):
    """A class which describes how an :class:`~fsl.data.image.Image` should
    be displayed.

    This class doesn't have much functionality - it is up to things which
    actually display an :class:`~fsl.data.image.Image` to adhere to the
    properties stored in the associated :class:`ImageDisplay` object.
    """

    
    enabled = props.Boolean(default=True)
    """Should this image be displayed at all?"""

    
    alpha = props.Real(minval=0.0, maxval=1.0, default=1.0)
    """Transparency - 1.0 is fully opaque, and 0.0 is fully transparent."""

    
    displayRange = props.Bounds(ndims=1,
                                editLimits=True,
                                labels=['Min.', 'Max.'])
    """Image values which map to the minimum and maximum colour map colours."""

    
    resolution = props.Real(maxval=10,
                            default=1,
                            clamped=True,
                            editLimits=False)
    """Data resolution in world space. The minimum value is set in __init__.""" 
                              
    
    clipLow  = props.Boolean(default=False)
    """If ``True``, don't display voxel values which are lower than
    the :attr:`displayRange`.
    """

    
    clipHigh = props.Boolean(default=False)
    """If ``True``, don't display voxel values which are higher than
    the :attr:`displayRange`.
    """ 

    
    cmap = props.ColourMap(default=fslcm.default, cmapNames=fslcm.cmapNames)
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""

    
    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If a 4D image, the current volume to display."""

    
    transform = props.Choice(
        collections.OrderedDict([
            ('affine', 'Use qform/sform transformation matrix'),
            ('pixdim', 'Use pixdims only'),
            ('id',     'Do not use qform/sform or pixdims')]),
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


    interpolation = props.Choice(OrderedDict([
        ('none',   'No interpolation'),
        ('linear', 'Linear interpolation'),
        ('spline', 'Spline interpolation')]))
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


    def __eq__(self, other):
        """
        Returns true if the given object is an :class:`ImageDisplay`, and
        has the same display values as this one.
        """
        if not isinstance(other, ImageDisplay):
            return False
            
        return (self.enabled       == other.enabled      and
                self.alpha         == other.alpha        and
                self.displayRange  == other.displayRange and
                self.clipLow       == other.clipLow      and
                self.clipHigh      == other.clipHigh     and
                self.cmap.name     == other.cmap.name    and
                self.volume        == other.volume       and
                self.resolution    == other.resolution   and
                self.transform     == other.transform    and
                self.interpolation == other.interpolation)

        
    def __hash__(self):
        """
        Returns a hash value based upon the display properties of this
        :class:`ImageDisplay` object.
        """
        return (hash(self.enabled)      ^
                hash(self.alpha)        ^
                hash(self.displayRange) ^
                hash(self.clipLow)      ^
                hash(self.clipHigh)     ^
                hash(self.cmap.name)    ^
                hash(self.volume)       ^
                hash(self.resolution)   ^
                hash(self.transform)    ^
                hash(self.interpolation))

        
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()

        
    _view = props.VGroup((
        'name',
        'enabled',
        'displayRange',
        'alpha',
        props.HGroup(('clipLow', 'clipHigh', 'interpolation')),
        'resolution',
        'transform',
        'imageType',
        'cmap'))

    
    _labels = {
        'name'           : 'Image name',
        'enabled'        : 'Enabled',
        'displayRange'   : 'Display range',
        'alpha'          : 'Opacity',
        'clipLow'        : 'Low clipping',
        'clipHigh'       : 'High clipping',
        'interpolation'  : 'Interpolation',
        'Resolution'     : 'Resolution',
        'transform'      : 'Image transform',
        'imageType'      : 'Image data type',
        'cmap'           : 'Colour map'}

    
    _tooltips = {
        'name'          : 'The name of this image',
        'enabled'       : 'Enable/disable this image',
        'alpha'         : 'Opacity, between 0.0 (transparent) '
                          'and 1.0 (opaque)',
        'displayRange'  : 'Minimum/maximum display values',
        'clipLow'       : 'Do not show image values which are '
                          'lower than the display range',
        'clipHigh'      : 'Do not show image values which are '
                          'higher than the display range', 
        'interpolation' : 'Interpolate between voxel values at '
                          'each displayed real world location',
        'resolution'    : 'Data resolution in voxels',
        'transform'     : 'The transformation matrix which specifies the '
                          'conversion from voxel coordinates to a real '
                          'world location',
        'imageType'     : 'the type of data contained in the image',
        'cmap'          : 'Colour map'}

    
    _propHelp = _tooltips


    _cliProps = ['alpha',
                 'displayRange',
                 'clipLow',
                 'clipHigh',
                 'resolution',
                 'transform',
                 'interpolation',
                 'imageType',
                 'cmap',
                 'name',
                 'volume']

    _shortArgs = {
        'alpha'         : 'alpha',
        'displayRange'  : 'dr',
        'clipLow'       : 'cl',
        'clipHigh'      : 'ch',
        'interpolation' : 'interp',
        'resolution'    : 'vr',
        'transform'     : 'trans',
        'imageType'     : 'it',
        'cmap'          : 'cmap',
        'name'          : 'name',
        'volume'        : 'vol'}


    def __init__(self, image, parent=None):
        """Create an :class:`ImageDisplay` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.

        :arg parent: 
        """

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

        self.image = image

        # bind self.name to # image.name, so changes
        # in one are propagated to the other
        self.bindProps('name', image)

        # Attributes controlling image display. Only
        # determine the real min/max for small images -
        # if it's memory mapped, we have no idea how big
        # it may be! So we calculate the min/max of a
        # sample (either a slice or an image, depending
        # on whether the image is 3D or 4D)
        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(image.data.min())
            self.dataMax = float(image.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        self.displayRange.setMin(0, self.dataMin - 0.5 * dRangeLen)
        self.displayRange.setMax(0, self.dataMax + 0.5 * dRangeLen)
        self.displayRange.setRange(0, self.dataMin, self.dataMax)
        self.setConstraint('displayRange', 'minDistance', dMinDistance)

        self.resolution = min(image.pixdim[:3])
        self.setConstraint('resolution',   'minval', self.resolution)
        

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

        
    def _transformChanged(self, *a):
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


class DisplayContext(props.SyncableHasProperties):
    """Contains a number of properties defining how an
    :class:`~fsl.dat.aimage.ImageList` is to be displayed.
    """

    
    selectedImage = props.Int(minval=0, default=0, clamped=True)
    """Index of the currently 'selected' image.

    This value is used as an index into the :attr:`imageOrder` list, which
    defines the order in which images are to be displayed. The value stored at
    this index in the :attr:`imageOrder` list gives the index of the the
    actual image (i.e. into the :cass:`~fsl.data.image.ImageList`).  Rather
    than accessing this value directly, and performing this necessary
    transformation manually, it is easier to use the :meth:`getSelectedImage`
    and :meth:`getSelectedImageIndex` methods.
    
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
    list, defining the order in which the images are to be displayed. See
    comments for the :attr:`selectedImage` property for useful information.
    """


    def __init__(self, imageList, parent=None):
        """Create a :class:`DisplayContext` object.

        :arg imageList: A :class:`~fsl.data.image.ImageList` instance.

        :arg parent: 
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
        """
        if isinstance(image, int):
            image = self._imageList[image]
        return self._imageDisplays[image]

    
    def getSelectedImageIndex(self):
        return self.imageOrder[self.selectedImage]

    
    def getSelectedImage(self):
        return self._imageList[self.getSelectedImageIndex()]

    
    def getImageOrder(self, image):
        if isinstance(image, fslimage.Image):
            image = self._imageList.index(image)
        return self.imageOrder.index(image)


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
            try:
                display = self._imageDisplays[image]
                
            except KeyError:
                
                if self.getParent() is None:
                    dParent = None
                else:
                    dParent = self.getParent().getDisplayProperties(image)

                display = ImageDisplay(image, dParent)
                self._imageDisplays[image] = display

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


    def _transformChanged(self, xform, valid, display):
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
            xform   = display.voxToDisplayMat

            for ax in range(3):

                lo, hi = transform.axisBounds(img.shape[:3], xform, ax)

                if lo < minBounds[ax]: minBounds[ax] = lo
                if hi > maxBounds[ax]: maxBounds[ax] = hi

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]] 
 
    
    def _volumeChanged(self, *a):
        """Called when the :attr:`volume` property changes.

        Propagates the change on to the :attr:`ImageDisplay.volume` property
        for each image in the :class:`~fsl.data.image.ImageList`.
        """
        for image in self._imageList:
            
            # The volume property for each image should
            # be clamped to the possible value for that
            # image, so we don't need to check if the
            # current volume value is valid for each image
            self._imageDisplays[image].volume = self.volume

            
    def _boundsChanged(self, *a):
        """Called when the :attr:`bounds` property changes.

        Updates the constraints on the :attr:`location` property.
        """

        self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
        self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
        self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)
