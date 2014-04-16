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

import fsl.data.imagefile as imagefile

class Colours(object):

    def __init__(self, image):
        self.image = image

    def __getitem__(self, key):

        image = self.image
        cmap  = image.cmap

        cmap.set_under('k')
        cmap.set_over( 'k')

        norm    = mplcolors.Normalize(image.displaymin,image.displaymax)
        data    = image.data.__getitem__(key)
        colData = cmap(norm(data))

        # move the colour dimension to the front so, e.g.
        # colData[:,a,b,c] will return the colour data for
        # voxel [a,b,c]
        colData = np.rollaxis(colData, len(colData.shape)-1)

        # trim the alpha values, as we use an image wide alpha
        return colData.take(range(3), axis=0)

        
class Image(object):

    @property
    def colour(self):
        return self._colour[:]

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

        # Attributes controlling image display
        self.cmap       = mplcm.Greys_r
        self.alpha      = 1.0
        self.displaymin = self.data.min()# use cal_min/cal_max instead?
        self.displaymax = self.data.max()
        self.datamin    = self.data.min() # use cal_min/cal_max instead?
        self.datamax    = self.data.max()

        self._colour  = Colours(self)

    def __getitem__(self, key):
        return self.data.__getitem__(key)
        
