#!/usr/bin/env python
#
# lookuptabletexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL as gl
import numpy     as np

import texture


log = logging.getLogger(__name__)


class LookupTableTexture(texture.Texture):

    def __init__(self, name):
        
        texture.Texture.__init__(self, name, 1)
        
        self.__lut    = None
        self.__alpha  = None
        self.__interp = None
        self.__border = None


    def set(self, **kwargs):

        lut    = kwargs.get('lut',    self)
        alpha  = kwargs.get('alpha',  self)
        border = kwargs.get('border', self)
        interp = kwargs.get('interp', self)

        if lut    is not self: self.__lut    = lut
        if alpha  is not self: self.__alpha  = alpha
        if border is not self: self.__border = border
        if interp is not self: self.__interp = interp

        self.__refresh()


    def refresh(self):
        self.__refresh()

        
    def __refresh(self):

        alpha  = self.__alpha
        border = self.__border
        interp = self.__interp

        # TODO check maximum lut label value,
        #      and use corresponding number 
        #      of slots in colour map
        data   = np.zeros((64, 4), dtype=np.uint8)

        if self.__lut is not None:
            values  = self.__lut.values()
            colours = self.__lut.colours()

            for value, colour in zip(values, colours):

                data[value, :3] = [np.floor(c * 255) for c in colour]

                if alpha is not None: data[value, 3] = alpha * 255
                else:                 data[value, 3] = 255


        data = data.ravel('C')

        self.bindTexture()

        if border is not None:
            if alpha is not None:
                border[3] = alpha * 255
                
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
                        64,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        data)
        self.unbindTexture()
