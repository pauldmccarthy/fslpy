#!/usr/bin/env python
#
# fslimage.py - Classes for representing 3D images, display
# properties of 3D images, and collections of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

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
        self.name     = image.get_filename()

        xdim,ydim,zdim = self.nibImage.get_shape()
        xlen,ylen,zlen = self.nibImage.get_header().get_zooms()
        
        self.xdim  = xdim
        self.ydim  = ydim
        self.zdim  = zdim

        self.xlen  = xlen
        self.ylen  = ylen
        self.zlen  = zlen

        # This attribute may be used to point to an OpenGL
        # buffer which is to be shared between multiple users
        # (e.g. two SliceCanvas instances which are displaying
        # a different view of the same image)
        self.glBuffer = None


class ImageDisplay(props.HasProperties):
    """
    A class which describes how an image should be displayed.
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

    # The display properties of an image
    enabled    = props.Boolean()
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
    """

    def __init__(self, images=None, displays=None):
        
        if images   is None: images   = []
        if displays is None: displays = []
        
        self.images   = images
        self.displays = displays

