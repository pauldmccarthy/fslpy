#!/usr/bin/env python
#
# texture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging


import OpenGL.GL as gl


log = logging.getLogger(__name__)


class Texture(object):

    def __init__(self, name, ndims):

        self.__texture     = gl.glGenTextures(1)
        self.__name        = name
        self.__ndims       = ndims
        
        self.__textureUnit = None

        if   ndims == 1: self.__ttype = gl.GL_TEXTURE_1D
        elif ndims == 2: self.__ttype = gl.GL_TEXTURE_2D
        elif ndims == 3: self.__ttype = gl.GL_TEXTURE_3D
        
        else:            raise ValueError('Invalid number of dimensions')

        log.debug('Created GL texture for {}: {}'.format(self.__name,
                                                         self.__texture))

    def getTextureName(self):
        return self.__name

        
    def getTextureHandle(self):
        return self.__texture


    def destroy(self):

        log.debug('Deleting GL texture for {}: {}'.format(self.__name,
                                                          self.__texture))
 
        gl.glDeleteTextures(self.__texture)
        self.__texture = None


    def bindTexture(self, textureUnit=None):

        if textureUnit is not None:
            gl.glActiveTexture(textureUnit)
            gl.glEnable(self.__ttype)
            
        gl.glBindTexture(self.__ttype, self.__texture)

        self.__textureUnit = textureUnit


    def unbindTexture(self):

        if self.__textureUnit is not None:
            gl.glActiveTexture(self.__textureUnit)
            gl.glDisable(self.__ttype)
            
        gl.glBindTexture(self.__ttype, 0)

        self.__textureUnit = None
