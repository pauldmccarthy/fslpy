#!/usr/bin/env python
#
# fslimage.py - Classes for representing 3D/4D images, display
# properties of images, and collections of images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import logging
import tempfile
import collections
import subprocess         as sp
import os.path            as op

import numpy              as np
import numpy.linalg       as linalg
import nibabel            as nib
import matplotlib.cm      as mplcm

import fsl.props            as props
import fsl.data.imagefile   as imagefile


log = logging.getLogger(__name__)


def _loadImageFile(filename):
    """
    Given the name of an image file, loads it using nibabel. If the file
    is large, and is gzipped, it is decompressed to a temporary location,
    so that it can be memory-mapped.  A tuple is returned, consisting of
    the nibabel image object, and the name of the file that it was loaded
    from (either the passed-in file name, or the name of the temporary
    decompressed file).
    """

    # If we have a GUI, we can display a dialog
    # message. Otherwise we print a log message
    haveGui = False
    try:
        import wx
        if wx.GetApp() is not None: 
            haveGui = True
    except:
        pass

    realFilename = filename

    if filename.endswith('.nii.gz'):
        
        mbytes = op.getsize(filename) / 1048576.0

        # This limit is arbitrary
        if mbytes > 512:

            unzipped, filename = tempfile.mkstemp(suffix='.nii')

            unzipped = os.fdopen(unzipped)

            msg = '{} is a large file ({} MB) - decompressing ' \
                  'to {}, to allow memory mapping...'.format(realFilename,
                                                             mbytes,
                                                             filename)

            if not haveGui:
                log.info(msg)
            else:
                busyDlg = wx.BusyInfo(msg, wx.GetTopLevelWindows()[0])

            gzip = ['gzip', '-d', '-c', realFilename]
            log.debug('Running {} > {}'.format(' '.join(gzip), filename))

            # If the gzip call fails, revert to loading from the gzipped file
            try:
                sp.call(gzip, stdout=unzipped)
                unzipped.close()

            except OSError as e:
                log.warn('gzip call failed ({}) - cannot memory '
                         'map file: {}'.format(e, realFilename),
                         exc_info=True)
                unzipped.close()
                os.remove(filename)
                filename = realFilename

            if haveGui:
                busyDlg.Destroy()

    return nib.load(filename), filename


class Image(props.HasProperties):
    """
    Class which represents a 3D/4D image. Internally, the image is
    loaded/stored using nibabel.
    """

    # How the image should be transformd into real world space.
    transform = props.Choice(
        collections.OrderedDict([
            ('affine', 'Use qform/sform transformation matrix'),
            ('pixdim', 'Use pixdims only'),
            ('id',     'Do not use qform/sform or pixdims')]),
        default='affine')

    name      = props.String()
    imageFile = props.FilePath()
    tempFile  = props.FilePath()
        
    def __init__(self, image):
        """
        Initialise an Image object with the given image data or file name.
        """

        # The image parameter may be the name of an image file
        if isinstance(image, basestring):
            
            nibImage, filename = _loadImageFile(imagefile.addExt(image))
            self.nibImage      = nibImage
            self.imageFile     = image

            # if the returned file name is not the same as
            # the provided file name, that means that the
            # image was opened from a temporary file
            if filename != image:
                self.name     = op.basename(self.imageFile)
                self.tempFile = nibImage.get_filename()
            else:
                self.name     = op.basename(self.imageFile)
                
        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):
            
            self.nibImage  = nib.nifti1.Nifti1Image(image, np.identity(4))
            self.name      = 'Numpy array'
            self.tempFile  = None
            self.imageFile = None
            
        # otherwise, we assume that it is a nibabel image
        else:
            self.nibImage  = image
            self.name      = 'Nibabel image'
            self.tempFile  = None
            self.imageFile = None 

        self.data     = self.nibImage.get_data()
        self.shape    = self.nibImage.get_shape()
        self.pixdim   = self.nibImage.get_header().get_zooms()

        self.addListener(
            'transform',
            '{}_{}'.format(self.__class__.__name__, self.name),
            self._transformChanged)

        self._transformChanged()

        if len(self.shape) < 3 or len(self.shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        # ImageDisplay instance used to describe
        # how this image is to be displayed
        self.display = ImageDisplay(self)

        # This dictionary may be used to store
        # arbitrary data associated with this image.
        self._attributes = {}


    def _transformChanged(self, *a):
        """
        """

        if self.transform == 'affine':
            voxToWorldMat = self.nibImage.get_affine().transpose()
        elif self.transform == 'pixdim':
            pixdims = [self.pixdim[0], self.pixdim[1], self.pixdim[2], 1]
            voxToWorldMat = np.diag(pixdims)
        elif self.transform == 'id':
            voxToWorldMat = np.identity(4)

        self.voxToWorldMat = np.array(voxToWorldMat, dtype=np.float32)
        self.worldToVoxMat = linalg.inv(self.voxToWorldMat)

        log.debug('Image {} transformation matrix changed: {}'.format(
            self.name, self.voxToWorldMat))


    def imageBounds(self, axis):
        """
        Return the bounds (min, max) of the image, in real world
        coordinates, along the specified axis.
        """

        x, y, z = self.shape[:3]

        points = np.zeros((8, 3), dtype=np.float32)

        points[0, :] = [0, 0, 0]
        points[1, :] = [0, 0, z]
        points[2, :] = [0, y, 0]
        points[3, :] = [0, y, z]
        points[4, :] = [x, 0, 0]
        points[5, :] = [x, 0, z]
        points[6, :] = [x, y, 0]
        points[7, :] = [x, y, z] 

        tx = self.voxToWorld(points)

        lo = tx[:, axis].min()
        hi = tx[:, axis].max()

        return (lo, hi)


    def worldToVox(self, p, axes=None):
        """
        Transforms the given set of points in voxel coordinates to
        points in world coordinates, according to the affine
        transformation specified in the image file. The returned array
        is either a numpy.float64 array, or a single integer value,
        depending on the input. Parameters:
        
          - p:    N*A array, where N is the number of points, and A
                  is the number of axes to consider (default: 3)
        
          - axes: If None, it is assumed that the input p is a N*3
                  array, with each point being specified by x,y,z
                  coordinates. If a single value in the range (0-2),
                  it is assumed that p is a 1D array. Or, if a
                  sequence of 2 or 3 values, p must be an array of
                  N*2 or N*3, respectively.
        """

        voxp = self._transform(p, self.worldToVoxMat, axes)
        voxp = np.array(voxp.round(), dtype=np.uint32)

        if voxp.size == 1: return voxp[0]
        else:              return voxp


    def voxToWorld(self, p, axes=None):
        """
        Transforms the given set of points in world coordinates to
        points in voxel coordinates, according to the affine
        transformation specified in the image file.  The returned
        array is either a numpy.float64 array, or a single float
        value, depending on the input. See the worldToVox
        docstring for more details. 
        """

        worldp = self._transform(p, self.voxToWorldMat, axes)

        if worldp.size == 1: return float(worldp)
        else:                return worldp

        
    def _transform(self, p, a, axes):
        """
        Transforms the given set of points p according to the given
        affine transformation a. The transformed points are returned
        as a numpy.float64 array. See the worldToVox docstring for
        more details. 
        """

        p = self._fillPoints(p, axes)
        t = np.zeros((len(p), 3), dtype=np.float64)

        x = p[:, 0]
        y = p[:, 1]
        z = p[:, 2]

        t[:, 0] = x * a[0, 0] + y * a[1, 0] + z * a[2, 0] + a[3, 0]
        t[:, 1] = x * a[0, 1] + y * a[1, 1] + z * a[2, 1] + a[3, 1]
        t[:, 2] = x * a[0, 2] + y * a[1, 2] + z * a[2, 2] + a[3, 2]

        if axes is None: axes = [0, 1, 2]

        return t[:, axes]


    def _fillPoints(self, p, axes):
        """
        Used by the _transform method. Turns the given array p into a N*3
        array of x,y,z coordinates. The array p may be a 1D array, or an
        N*2 or N*3 array.
        """

        if not isinstance(p, collections.Iterable): p = [p]
        
        p = np.array(p)

        if axes is None: return p

        if not isinstance(axes, collections.Iterable): axes = [axes]

        if p.ndim == 1:
            p = p.reshape((len(p), 1))

        if p.ndim != 2:
            raise ValueError('Points array must be either one or two '
                             'dimensions')

        if len(axes) != p.shape[1]:
            raise ValueError('Points array shape does not match specified '
                             'number of axes')

        newp = np.zeros((len(p), 3), dtype=p.dtype)

        for i, ax in enumerate(axes):
            newp[:, ax] = p[:, i]

        return newp

        
    def getAttribute(self, name):
        """
        Retrieve the attribute with the given name.
        """
        return self._attributes[name]

        
    def setAttribute(self, name, value):
        """
        Set an attribute with the given name and the given value.
        """
        self._attributes[name] = value
        
        log.debug('Attribute set on {}: {} = {}'.format(
            self.name, name, str(value)))


class ImageDisplay(props.HasProperties):
    """
    A class which describes how an image should be displayed. There should
    be no need to manually instantiate ImageDisplay objects - one is created
    for each Image object, and is accessed via the Image.display attribute.
    If a single image needs to be displayed in different ways, then create
    away, and manage your own ImageDisplay objects.

    This class doesn't have any functionality - it is up to things which
    actually display an Image to adhere to the properties stored in the
    associated ImageDisplay object.
    """

    enabled      = props.Boolean(default=True)
    alpha        = props.Real(minval=0.0, maxval=1.0, default=1.0)
    displayRange = props.Bounds(ndims=1, editLimits=True,
                                labels=['Min.', 'Max.'])
    samplingRate = props.Int(minval=1, maxval=16, default=1, clamped=True)
    rangeClip    = props.Boolean(default=False)
    cmap         = props.ColourMap(default=mplcm.Greys_r)
    volume       = props.Int(minval=0, maxval=0, default=0, clamped=True)


    def is4DImage(self):
        return len(self.image.shape) > 3 and self.image.shape[3] > 1
    
    _view = props.VGroup(('enabled',
                          props.Widget('volume', enabledWhen=is4DImage),
                          'displayRange',
                          'alpha',
                          'rangeClip',
                          'samplingRate',
                          'cmap'))
    _labels = {
        'enabled'      : 'Enabled',
        'displayRange' : 'Display range',
        'alpha'        : 'Opacity',
        'rangeClip'    : 'Clipping',
        'samplingRate' : 'Sampling rate',
        'cmap'         : 'Colour map',
        'volume'       : 'Volume'
    }

    _tooltips = {
        'enabled'      : 'Enable/disable this image',
        'alpha'        : 'Opacity, between 0.0 (transparent) and 1.0 (opaque)',
        'displayRange' : 'Minimum/maximum display values',
        'rangeClip'    : 'Do not show areas of the image which lie '
                         'outside of the display range',
        'samplingRate' : 'Draw every Nth voxel',
        'cmap'         : 'Colour map',
        'volume'       : 'Volume to display (zero-indexed, for 4D images)'}

    _help = _tooltips


    def __init__(self, image):
        """
        Create an ImageDisplay for the specified image. The image
        parameter should be an Image object (defined above).
        """

        self.image = image

        # Attributes controlling image display. Only
        # determine the real min/max for small images -
        # if it's memory mapped, we have no idea how big
        # it may be! So we calculate the min/max of a
        # sample (either a slice or an image, depending
        # on whether the image is 3D or 4D)
        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = sample.min()
            self.dataMax = sample.max()
        else:
            self.dataMin = image.data.min()
            self.dataMax = image.data.max()

        dRangeLen = abs(self.dataMax - self.dataMin)

        self.displayRange.setMin(0, self.dataMin - 0.5 * dRangeLen)
        self.displayRange.setMax(0, self.dataMax + 0.5 * dRangeLen)
        self.displayRange.setRange(0, self.dataMin, self.dataMax)

        # is this a 4D volume?
        if self.is4DImage():
            self.setConstraint('volume', 'maxval', image.shape[3] - 1)
            

class ImageList(props.HasProperties):
    """
    Class representing a collection of images to be displayed together.
    Contains a List property containing Image objects, and some other 
    properties on which listeners may register themselves to be notified
    when the properties of the image collection changes (e.g. image
    bounds).
    """

    def _validateImage(self, atts, images):
        return all(map(lambda img: isinstance(img, Image), images))

    # The images property contains a list of Image objects
    images = props.List(validateFunc=_validateImage, allowInvalid=False)

    # Index of the currently 'selected' image. This property
    # is not used by the ImageList, but is provided so that
    # other things can control and listen for changes to
    # the currently selected image
    selectedImage = props.Int(minval=0, clamped=True)

    # The bounds property contains the min/max values of
    # a bounding box (in real world coordinates) which
    # is big enough to contain all of the images in the
    # 'images' list. This property shouid be read-only,
    # but I don't have a way to enforce it (yet).
    bounds = props.Bounds(ndims=3)

    # The location property contains the currently 'selected'
    # 3D location in the image list space. This property
    # is not used directly by the ImageList object, but it
    # is here so that the location selection can be synchronised
    # across multiple displays.
    location = props.Point(ndims=3, labels=('X', 'Y', 'Z'))

    def __init__(self, images=None):
        """
        Create an ImageList object from the given sequence of Image objects.
        """
        
        if images is None: images = []

        self.addListener(
            'images',
            self.__class__.__name__,
            self._imageListChanged)

        self.images = images


    def _imageListChanged(self, *a):
        """
        Called whenever an item is added or removed from the list. Registers
        listeners with the properties of each image, and updates the image
        bounds
        """ 
        
        for img in self.images:

            # This may be called multiple times on each image,
            # but it doesn't matter, as any listener which has
            # previously been registered with an image will
            # just be replaced by the new one here.
            img.addListener(
                'transform',
                self.__class__.__name__,
                self._updateImageBounds) 

        self._updateImageBounds()

    
    def _updateImageBounds(self, *a):
        """
        Called whenever an item is added or removed from the list, or an
        image property changes. Updates the xyz bounds.
        """

        if len(self.images) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]

        for img in self.images:

            for ax in range(3):

                lo, hi = img.imageBounds(ax)

                if lo < minBounds[ax]: minBounds[ax] = lo
                if hi > maxBounds[ax]: maxBounds[ax] = hi

        self.bounds.all = [minBounds[0], maxBounds[0],
                           minBounds[1], maxBounds[1],
                           minBounds[2], maxBounds[2]]

        for ax in range(3):
            self.location.setLimits(ax, minBounds[ax], maxBounds[ax])

        self.setConstraint('selectedImage', 'maxval', len(self.images))


    # Wrappers around the images list property, allowing this
    # ImageList object to be used as if it is actually a list.
    def __len__(     self):            return self.images.__len__()
    def __getitem__( self, key):       return self.images.__getitem__(key)
    def __iter__(    self):            return self.images.__iter__()
    def __contains__(self, item):      return self.images.__contains__(item)
    def __setitem__( self, key, val):  return self.images.__setitem__(key, val)
    def __delitem(   self, key):       return self.images.__delitem__(key)
    def index(       self, item):      return self.images.index(item)
    def count(       self, item):      return self.images.count(item)
    def append(      self, item):      return self.images.append(item)
    def extend(      self, iterable):  return self.images.extend(iterable)
    def pop(         self, index=-1):  return self.images.pop(index)
    def move(        self, from_, to): return self.images.move(from_, to) 
