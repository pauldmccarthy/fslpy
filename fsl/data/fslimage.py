#!/usr/bin/env python
#
# fslimage.py - Classes for representing 3D images, display
# properties of 3D images, and collections of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging
import traceback
import collections

import os.path            as op

import numpy              as np
import numpy.linalg       as linalg
import nibabel            as nib
import matplotlib.cm      as mplcm

import fsl.props            as props
import fsl.data.imagefile   as imagefile


log = logging.getLogger(__name__)


class Image(object):
    """
    Class which represents a 3D image. Internally, the image is loaded/stored
    using nibabel.
    """

    def __init__(self, image):
        """
        Initialise an Image object with the given image data or file name.
        """

        # The image parameter may be the name of an image file
        if isinstance(image, basestring):
            image = nib.load(imagefile.addExt(image))
            
        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):
            image = nib.nifti1.Nifti1Image(image, np.identity(4))

        # otherwise, we assume that it is a nibabel image
        self.nibImage = image
        self.data     = image.get_data()
        self.name     = op.basename(image.get_filename())

        self.shape         = self.nibImage.get_shape()
        self.pixdim        = self.nibImage.get_header().get_zooms()
        self.voxToWorldMat = image.get_affine().transpose()
        self.worldToVoxMat = linalg.inv(self.voxToWorldMat)

        # ImageDisplay instance used to describe
        # how this image is to be displayed
        self.display = ImageDisplay(self)

        # This dictionary may be used to store
        # arbitrary data associated with this image.
        self._attributes = {}


    def imageBounds(self, axis):
        """
        Return the bounds (min, max) of the image, in real world
        coordinates, along the specified axis.
        """

        points = np.zeros((2, 3), dtype=np.float32)
        points[1, axis] = self.shape[axis] - 1
        
        tx = self.voxToWorld(points)

        lo, hi = sorted(tx[:, axis])

        lo = float(lo - self.pixdim[axis] * 0.5)
        hi = float(hi + self.pixdim[axis] * 0.5)

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

        if voxp.size == 1: return int(voxp[0])
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

    This class doesn't have any functionality (apart from updating its own
    colour map when necessary) - it is up to things which actually display
    an Image to adhere to the properties stored in the associated
    ImageDisplay object.
    """

    def updateColourMap(self, newVal, valid):
        """
        When a colour property changes, this method is called -
        it reconfigures the colour map accordingly.
        """

        try: cmap = mplcm.get_cmap(self.cmap)
        except: return

        if self.rangeClip:
            cmap.set_under(cmap(0.0), alpha=0.0)
            cmap.set_over( cmap(1.0), alpha=0.0)
        else:
            cmap.set_under(cmap(0.0), alpha=1.0)
            cmap.set_over( cmap(1.0), alpha=1.0) 

            
    enabled      = props.Boolean(default=True)
    alpha        = props.Double(minval=0.0, maxval=1.0, default=1.0)
    displayMin   = props.Double()
    displayMax   = props.Double()
    samplingRate = props.Int(minval=1, maxval=16, default=1, clamped=True)
    rangeClip    = props.Boolean(default=False,
                                 preNotifyFunc=updateColourMap)

    cmap         = props.ColourMap(default=mplcm.Greys_r,
                                   preNotifyFunc=updateColourMap)
    
    volume       = props.Int(minval=0, maxval=0, default=0, clamped=True)


    def volumeEnabled(self):
        return len(self.image.shape) > 3 and self.image.shape[3] > 1
    
    _view = props.VGroup(('enabled',
                          props.Widget('volume',
                                       enabledWhen=volumeEnabled),
                          'displayMin',
                          'displayMax',
                          'alpha',
                          'rangeClip',
                          'samplingRate',
                          'cmap'))
    _labels = {
        'enabled'      : 'Enabled',
        'displayMin'   : 'Min.',
        'displayMax'   : 'Max.',
        'alpha'        : 'Opacity',
        'rangeClip'    : 'Clipping',
        'samplingRate' : 'Sampling rate',
        'cmap'         : 'Colour map',
        'volume'       : 'Volume'
    }


    def __init__(self, image):
        """
        Create an ImageDisplay for the specified image. The image
        parameter should be an Image object (defined above).
        """

        self.image = image


        # Attributes controlling image display. Only
        # determine the real min/max for in-memory
        # images - if it's memory mapped, we have no
        # idea how big it may be! So we calculate
        # the min/max of a sample (either a slice or
        # an image, depending on whether the image
        # is 3D or 4D)
        if np.prod(image.shape) > 2 ** 30:
            sample = image.data[..., image.shape[-1] / 2]
            self.dataMin = sample.min()
            self.dataMax = sample.max()
        else:
            self.dataMin = image.data.min()
            self.dataMax = image.data.max()

        self.displayMin = self.dataMin
        self.displayMax = self.dataMax

        self.setConstraint('displayMin', 'minval', self.dataMin)
        self.setConstraint('displayMin', 'maxval', self.dataMax)
        self.setConstraint('displayMax', 'minval', self.dataMin)
        self.setConstraint('displayMax', 'maxval', self.dataMax)

        # is this a 4D volume?
        if len(image.shape) > 3:
            self.setConstraint('volume', 'maxval', image.shape[3] - 1)
            

        
class ImageList(object):
    """
    Class representing a collection of images to be displayed together.
    Provides basic list-like functionality, and a listener interface
    allowing callback functions to be notified when the image collection
    changes (e.g. an image is added or removed).
    """


    def __init__(self, images=None):
        """
        Create an ImageList object from the given sequence of Image objects.
        """
        
        if images is None: images = []

        if not isinstance(images, collections.Iterable):
            raise TypeError('images must be a sequence of images')

        map(self._validate, images)

        self._items     = images
        self._listeners = []

        self._updateImageAttributes()

        
    def _updateImageAttributes(self):
        """
        Called whenever an item is added or removed from the list.
        Updates the xyz bounds.
        """

        if len(self._items) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]            
        
        for img in self._items:

            for ax in range(3):

                lo, hi = img.imageBounds(ax)

                if lo < minBounds[ax]: minBounds[ax] = lo
                if hi > maxBounds[ax]: maxBounds[ax] = hi

        self.minBounds = minBounds
        self.maxBounds = maxBounds

        
    def _validate(self, img):
        """
        Called whenever an item is added to the list. Raises
        a TypeError if said item is not an Image object.
        """
        if not isinstance(img, Image):
            raise TypeError('item must be a fsl.data.fslimage.Image') 

            
    def __len__(     self):        return self._items.__len__()
    def __getitem__( self, key):   return self._items.__getitem__(key)
    def __iter__(    self):        return self._items.__iter__()
    def __contains__(self, item):  return self._items.__contains__(item)
    def __eq__(      self, other): return self._items.__eq__(other)
    def __str__(     self):        return self._items.__str__()
    def __repr__(    self):        return self._items.__repr__()

 
    def append(self, item):
        self._validate(item)
        log.debug('Item appended: {}'.format(item))
        self._items.append(item)
        self._updateImageAttributes()
        self._notify()

        
    def pop(self, index=-1):
        item = self._items.pop(index)
        log.debug('Item popped: {} (index {})'.format(item, index))
        self._updateImageAttributes()
        self._notify()
        return item

        
    def insert(self, index, item):
        self._validate(item)
        self._items.insert(index, item)
        log.debug('Item inserted: {} (index {})'.format(item, index))
        self._updateImageAttributes()
        self._notify()


    def extend(self, items):
        map(self._validate, items)
        self._items.extend(items)
        log.debug('List extended: {}'.format(
            ', '.join([str(i) for i in items])))
        self._updateImageAttributes()
        self._notify()


    def move(self, from_, to):
        """
        Move the item from 'from_' to 'to'. 
        """

        item = self._items.pop(from_)
        self._items.insert(to, item)
        log.debug('Image moved: {} (from: {} to: {})'.format(item, from_, to))
        self._notify()

        
    def addListener(   self, listener): self._listeners.append(listener)
    def removeListener(self, listener): self._listeners.remove(listener)
    def _notify(       self):
        for listener in self._listeners:
            try:
                listener(self)
            except Exception as e:
                log.debug('Listener raised exception: {}'.format(e.message))
                traceback.print_exc()
