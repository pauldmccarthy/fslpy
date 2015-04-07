#!/usr/bin/env python
#
# texture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy     as np
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

        log.debug('Created {} ({}) for {}: {}'.format(type(self).__name__,
                                                      id(self),
                                                      self.__name,
                                                      self.__texture))

    def getTextureName(self):
        return self.__name

        
    def getTextureHandle(self):
        return self.__texture


    def destroy(self):

        log.debug('Deleting {} ({}) for {}: {}'.format(type(self).__name__,
                                                       id(self),
                                                       self.__name,
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


class Texture2D(Texture):

    def __init__(self, name, interp=gl.GL_NEAREST):
        Texture.__init__(self, name, 2)

        self.__data   = None
        self.__width  = None
        self.__height = None
        self.__interp = interp

        
    def setInterpolation(self, interp):
        self.__interp = interp
        self.refresh()


    def setSize(self, width, height):
        """
        Sets the width/height for this texture.

        This method also clears the data for this texture, if it has been
        previously set via the :meth:`setData` method.
        """
        self.__width  = width
        self.__height = height
        self.__data   = None
        self.refresh()


    def getSize(self):
        """
        """
        return self.__width, self.__height


    def setData(self, data):
        """
        Sets the data for this texture - the width and height are determined
        from data shape (which is assumed to be 4*width*height).
        """

        self.__data   = data
        self.__width  = data.shape[1]
        self.__height = data.shape[2]
        self.refresh()

        
    def refresh(self):

        if self.__width is None or self.__height is None:
            return

        self.bindTexture()
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           self.__interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)

        data = self.__data

        if data is not None:
            data = data.ravel('F')

        gl.glTexImage2D(gl.GL_TEXTURE_2D,
                        0,
                        gl.GL_RGBA8,
                        self.__width,
                        self.__height,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        data)
        self.unbindTexture()

        
    def draw(self, vertices):
        
        if vertices.shape != (6, 3):
            raise ValueError('Six vertices must be provided')

        vertices  = np.array(vertices, dtype=np.float32)
        texCoords = np.zeros((6, 2),   dtype=np.float32)
        indices   = np.arange(6,       dtype=np.uint32)

        texCoords[0, :] = [0, 0]
        texCoords[1, :] = [0, 1]
        texCoords[2, :] = [1, 0]
        texCoords[3, :] = [1, 0]
        texCoords[4, :] = [0, 1]
        texCoords[5, :] = [1, 1]

        vertices  = vertices .ravel('C')
        texCoords = texCoords.ravel('C')

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

        self.bindTexture(gl.GL_TEXTURE0)

        gl.glTexEnvf(gl.GL_TEXTURE_ENV,
                     gl.GL_TEXTURE_ENV_MODE,
                     gl.GL_REPLACE)

        gl.glVertexPointer(  3, gl.GL_FLOAT, 0, vertices)
        gl.glTexCoordPointer(2, gl.GL_FLOAT, 0, texCoords)

        gl.glDrawElements(gl.GL_TRIANGLES, 6, gl.GL_UNSIGNED_INT, indices) 

        self.unbindTexture()

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)        
 
        
    def drawOnBounds(self, xmin, xmax, ymin, ymax, xax, yax):

        vertices = np.zeros((6, 3), dtype=np.float32)

        vertices[ 0, [xax, yax]] = [xmin, ymin]
        vertices[ 1, [xax, yax]] = [xmin, ymax]
        vertices[ 2, [xax, yax]] = [xmax, ymin]
        vertices[ 3, [xax, yax]] = [xmax, ymin]
        vertices[ 4, [xax, yax]] = [xmin, ymax]
        vertices[ 5, [xax, yax]] = [xmax, ymax]

        self.draw(vertices)
