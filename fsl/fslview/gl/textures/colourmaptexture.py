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
        self.__interp       = None
        self.__alpha        = None
        self.__displayRange = None
        self.__border       = None
        self.__coordXform   = None


    # CMAP can be either a function which transforms
    # values to RGBA, or a N*4 numpy array containing
    # RGBA values
    def setColourMap(   self, cmap):   self.set(cmap=cmap)
    def setAlpha(       self, alpha):  self.set(alpha=alpha)
    def setInvert(      self, invert): self.set(invert=invert)
    def setInterp(      self, interp): self.set(interp=interp)
    def setDisplayRange(self, drange): self.set(displayRange=drange)
    def setBorder(      self, border): self.set(border=border)


    def getCoordinateTransform(self):
        return self.__coordXform

    
    def set(self, **kwargs):

        
        # None is a valid value for any attributes,
        # so we are using 'self' to test whether
        # or not an attribute value was passed in
        cmap         = kwargs.get('cmap',         self)
        invert       = kwargs.get('invert',       self)
        interp       = kwargs.get('interp',       self)
        alpha        = kwargs.get('alpha',        self)
        displayRange = kwargs.get('displayRange', self)
        border       = kwargs.get('border',       self)

        if cmap         is not self: self.__cmap         = cmap
        if invert       is not self: self.__invert       = invert
        if interp       is not self: self.__interp       = interp
        if alpha        is not self: self.__alpha        = alpha
        if displayRange is not self: self.__displayRange = displayRange
        if border       is not self: self.__border       = border

        self.__refresh()

    
    def __refresh(self):

        if self.__displayRange is None:
            imin = 0.0
            imax = 1.0
        else:
            imin = self.__displayRange[0]
            imax = self.__displayRange[1]

        if self.__cmap is None: cmap = np.zeros((4, 4), dtype=np.float32)
        else:                   cmap = self.__cmap
            
        invert     = self.__invert
        interp     = self.__interp
        resolution = self.__resolution
        alpha      = self.__alpha
        border     = self.__border

        # This transformation is used to transform input values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
        if imax == imin: scale = 0.000000000001
        else:            scale = imax - imin
        
        coordXform = np.identity(4, dtype=np.float32)
        coordXform[0, 0] = 1.0 / scale
        coordXform[3, 0] = -imin * coordXform[0, 0]

        self.__coordXform = coordXform

        # Assume that the provided cmap
        # value contains rgb values
        if isinstance(cmap, np.ndarray):
            resolution = cmap.shape[0]
            colourmap  = cmap
            
        # Create [self.colourResolution] 
        # rgb values, spanning the entire 
        # range of the image colour map            
        else:
            colourmap = cmap(np.linspace(0.0, 1.0, resolution))

        # Apply global transparency
        if alpha is not None:
            colourmap[:, 3] = alpha

        # invert if needed
        if invert:
            colourmap = colourmap[::-1, :]
        
        # The colour data is stored on
        # the GPU as 8 bit rgba tuples
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        self.bindTexture()

        if border is not None:
            if alpha is not None:
                border[3] = alpha
                
            gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_BORDER_COLOR,
                                border)
            gl.glTexParameteri( gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_WRAP_S,
                                gl.GL_CLAMP_TO_BORDER) 
        else:
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)

        if interp is None:
            interp = gl.GL_NEAREST
 
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           interp)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           interp)

        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        resolution,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        colourmap)
        self.unbindTexture()
