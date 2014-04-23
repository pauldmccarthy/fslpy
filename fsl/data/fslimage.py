#!/usr/bin/env python
#
# fslimage.py - Classes for representing 3D images, display
# properties of 3D images, and collections of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import collections

import os.path            as op

import numpy              as np
import nibabel            as nib
import matplotlib.cm      as mplcm
import matplotlib.colors  as mplcolors

import fsl.props          as props
import fsl.data.imagefile as imagefile


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
        if isinstance(image, str):
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

        xdim,ydim,zdim = self.nibImage.get_shape()
        xlen,ylen,zlen = self.nibImage.get_header().get_zooms()
        
        self.xdim = xdim
        self.ydim = ydim
        self.zdim = zdim

        self.xlen = xlen
        self.ylen = ylen
        self.zlen = zlen

        # ImageDisplay instance used to describe
        # how this image is to be displayed
        self.display = ImageDisplay(self)

        # This dictionary may be used to store
        # arbitrary data associated with this image.
        self._attributes = {}

        
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

        if not all(map(lambda img: isinstance(img, Image), images)):
            raise TypeError('images must be a sequence of images')
        
        self._images    = images
        self._listeners = []


    def __len__     (self):        return self._images.__len__()
    def __getitem__ (self, key):   return self._images.__getitem__(key)
    def __iter__    (self):        return self._images.__iter__()
    def __contains__(self, image): return self._images.__contains__(image)

        
    def append(self, image): 
        self._images.append(image)
        self.notify()

        
    def pop(self, index=-1):
        popped = self._images.pop(index)
        self.notify()
        return popped

        
    def insert(self, index, image):
        self._images.insert(index, image)
        self.notify()


    def extend(self, images):
        self._images.extend(images)
        self.notify()

        
    def addListener   (self, listener): self._listeners.append(listener)
    def removeListener(self, listener): self._listeners.remove(listener)
    def notify        (self):
        for listener in self._listeners:
            listener(self)
