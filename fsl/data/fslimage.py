#!/usr/bin/env python
#
# fslimage.py - Classes for representing 3D images, display
# properties of 3D images, and collections of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging
import collections

import os.path            as op

import numpy              as np
import numpy.linalg       as linalg
import nibabel            as nib
import matplotlib.cm      as mplcm
import matplotlib.colors  as mplcolors

import fsl.props            as props
import fsl.data.imagefile   as imagefile


log = logging.getLogger(__name__)


class Image(object):
    """
    Class which represents a 3D image. Interally, the image is loaded/stored
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
        """

        points = np.zeros((2,3), dtype=np.float32)
        points[1,axis] = self.shape[axis]-1
        
        tx = self.voxToWorld(points)

        lo,hi = sorted(tx[:,axis])

        lo = lo - self.pixdim[axis]*0.5
        hi = hi + self.pixdim[axis]*0.5

        return (lo, hi)


    def worldToVox(self, p):
        return self._transform(p, self.worldToVoxMat)


    def voxToWorld(self, p):
        return self._transform(p, self.voxToWorldMat)

        
    def _transform(self, p, a):
        """
        Parameters:
          - p: N*3 numpy array of (x,y,z) coordinates.
          - a: 4*4 affine transformation matrix.
        """

        t = np.zeros(p.shape, dtype=p.dtype)

        x = p[:,0]
        y = p[:,1]
        z = p[:,2]

        t[:,0] = x * a[0,0] + y * a[1,0] + z * a[2,0] + a[3,0]
        t[:,1] = x * a[0,1] + y * a[1,1] + z * a[2,1] + a[3,1]
        t[:,2] = x * a[0,2] + y * a[1,2] + z * a[2,2] + a[3,2]

        return t

        
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
    """

    def updateColourMap(self, newVal):
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

            
    enabled    = props.Boolean(default=True)
    alpha      = props.Double(minval=0.0, maxval=1.0, default=1.0)
    displayMin = props.Double()
    displayMax = props.Double()
    rangeClip  = props.Boolean(default=False,
                               preNotifyFunc=updateColourMap)

    cmap       = props.ColourMap(default=mplcm.Greys_r,
                                 preNotifyFunc=updateColourMap)
    
    _view   = props.VGroup(('enabled',
                            'displayMin',
                            'displayMax',
                            'alpha',
                            'rangeClip',
                            'cmap'))
    _labels = {
        'enabled'    : 'Enabled',
        'displayMin' : 'Min.',
        'displayMax' : 'Max.',
        'alpha'      : 'Opacity',
        'rangeClip'  : 'Clipping',
        'cmap'       : 'Colour map'
        }


    def __init__(self, image):
        """
        Create an ImageDisplay for the specified image. The image
        parameter should be an Image object (defined above).
        """

        self.image = image

        # Attributes controlling image display
        self.dataMin    = self.image.data.min()
        self.dataMax    = self.image.data.max() 
        self.displayMin = self.dataMin    # use cal_min/cal_max instead?
        self.displayMax = self.dataMax

        
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

            
    def __len__     (self):        return self._items.__len__()
    def __getitem__ (self, key):   return self._items.__getitem__(key)
    def __iter__    (self):        return self._items.__iter__()
    def __contains__(self, item):  return self._items.__contains__(item)
    def __eq__      (self, other): return self._items.__eq__(other)
    def __str__     (self):        return self._items.__str__()
    def __repr__    (self):        return self._items.__repr__()

 
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
        log.debug('List extended: {}'.format(', '.join([str(i) for i in item])))
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

        
    def addListener   (self, listener): self._listeners.append(listener)
    def removeListener(self, listener): self._listeners.remove(listener)
    def _notify       (self):
        for listener in self._listeners:
            try:
                listener(self)
            except e:
                log.debug('Listener raised exception: {}'.format(e.message))
 
