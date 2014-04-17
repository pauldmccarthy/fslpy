#!/usr/bin/env python
#
# fslimage.py - Object representing a 3D image.
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

    def __init__(self, image):

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

        xdim,ydim,zdim = self.nibImage.get_shape()
        xlen,ylen,zlen = self.nibImage.get_header().get_zooms()
        
        self.xdim  = xdim
        self.ydim  = ydim
        self.zdim  = zdim

        self.xlen  = xlen
        self.ylen  = ylen
        self.zlen  = zlen


        
class ImageDisplay(props.HasProperties):
    """
    """

    alpha      = props.Double(minval=0.0, maxval=1.0, default=1.0)
    displayMin = props.Double()
    displayMax = props.Double()
    rangeClip  = props.Boolean(default=False)

    _view   = props.VGroup(('displayMin', 'displayMax', 'alpha', 'rangeClip'))
    _labels = {
        'displayMin' : 'Min.',
        'displayMax' : 'Max.',
        'alpha'      : 'Opacity',
        'rangeClip'  : 'Clipping'
        }


    def __init__(self, image):

        self.image = image

        # Attributes controlling image display
        self.cmap       = mplcm.Greys_r
        self.alpha      = 1.0
        self.dataMin    = self.image.data.min()
        self.dataMax    = self.image.data.max() 
        self.displayMin = self.dataMin    # use cal_min/cal_max instead?
        self.displayMax = self.dataMax

        self.addListener(
            'rangeClip',
            'ImageRangeClip_{}'.format(id(self)),
            self.updateColourMap)

    def updateColourMap(self, *a):

        if self.rangeClip:
            self.cmap.set_under(self.cmap(0.0), alpha=0.0)
            self.cmap.set_over( self.cmap(1.0), alpha=0.0)
        else:
            self.cmap.set_under(self.cmap(0.0), alpha=1.0)
            self.cmap.set_over( self.cmap(1.0), alpha=1.0)   

