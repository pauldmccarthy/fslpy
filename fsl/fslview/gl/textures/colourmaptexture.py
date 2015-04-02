#!/usr/bin/env python
#
# colourmaptexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import numpy     as np
import OpenGL.GL as gl

import texture


log = logging.getLogger(__name__)


class ColourMapTexture(texture.Texture):


    def __init__(self, name, resolution=256):
        
        texture.Texture.__init__(self, name, 1)
        
        self.__resolution   = resolution
        self.__cmap         = None
        self.__invert       = False
        self.__alpha        = 1.0
        self.__displayRange = [0.0, 1.0]
        self.__coordXform   = None

        
    def setColourMap(   self, cmap):   self.set(cmap=cmap)
    def setAlpha(       self, alpha):  self.set(alpha=alpha)
    def setInvert(      self, invert): self.set(invert=invert)
    def setDisplayRange(self, drange): self.set(displayRange=drange)


    def getCoordinateTransform(self):
        return self.__coordXform

    
    def set(self, **kwargs):
        
        cmap         = kwargs.get('cmap',         None)
        invert       = kwargs.get('invert',       None)
        alpha        = kwargs.get('alpha',        None)
        displayRange = kwargs.get('displayRange', None)

        if cmap         is not None: self.__cmap         = cmap
        if invert       is not None: self.__invert       = invert
        if alpha        is not None: self.__alpha        = alpha
        if displayRange is not None: self.__displayRange = displayRange

        self.__refresh()

    
    def __refresh(self):

        imin       = self.__displayRange[0]
        imax       = self.__displayRange[1]
        invert     = self.__invert
        resolution = self.__resolution
        cmap       = self.__cmap
        alpha      = self.__alpha

        # This transformation is used to transform input values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
        if imax == imin: scale = 1
        else:            scale = imax - imin
        
        coordXform = np.identity(4, dtype=np.float32)
        coordXform[0, 0] = 1.0 / scale
        coordXform[3, 0] = -imin * coordXform[0, 0]

        self.__coordXform = coordXform

        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map
        if invert: colourRange = np.linspace(1.0, 0.0, resolution)
        else:      colourRange = np.linspace(0.0, 1.0, resolution)
        
        colourmap = cmap(colourRange)

        # Apply global transparency
        colourmap[:, 3] = alpha / 100.0
        
        # The colour data is stored on
        # the GPU as 8 bit rgba tuples
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        self.bindTexture()
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)

        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        resolution,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        colourmap)
        self.unbindTexture()
