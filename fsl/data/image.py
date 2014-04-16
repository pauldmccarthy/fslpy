#!/usr/bin/env python
#
# image.py - Object representing a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy             as np
import nibabel           as nib
import matplotlib.colors as colors
import matplotlib.cm     as cm

import fsl.data.filename as filename

class Image(object):

    def __init__(self, image):

        if isinstance(image, str):
            image = nib.load(filename.addExt(image))

        self.image     = image
        self.imageData = image.get_data()

        xdim,ydim,zdim = self.image.get_shape()
        xlen,ylen,zlen = self.image.get_header().get_zooms()
        
        self.xdim  = xdim
        self.ydim  = ydim
        self.zdim  = zdim

        self.xlen  = xlen
        self.ylen  = ylen
        self.zlen  = zlen

        # Attributes controlling image display
        self.cmap     = cm.Greys
        self.alpha    = 1.0
        self.rangemin = imageData.min() # use cal_min/cal_max instead?
        self.rangemax = imageData.max()
