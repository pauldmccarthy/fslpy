#!/usr/bin/env python
#
# rendertexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL                        as gl
import OpenGL.raw.GL._types             as gltypes
import OpenGL.GL.EXT.framebuffer_object as glfbo

import numpy                            as np

import texture 


log = logging.getLogger(__name__)


class RenderTexture(texture.Texture):
    """A 2D texture and frame buffer, intended to be used as a target for
    off-screen rendering of a scene.
    """
    
    def __init__(self, name, width, height, defaultInterp=gl.GL_NEAREST):
        """

        Note that a current target must have been set for the GL context
        before a frameBuffer can be created ... in other words, call
        ``context.SetCurrent`` before creating a ``RenderTexture``).
        """

        texture.Texture.__init__(self, name, 2)

        
        self.frameBuffer = glfbo.glGenFramebuffersEXT(1)
        log.debug('Created fbo: {}'.format(self.frameBuffer))

        self.defaultInterp = defaultInterp
        self.width         = width
        self.height        = height
        self.refresh()        

        
    def destroy(self):
        texture.Texture.destroy(self)

        log.debug('Deleting fbo {}'.format(self.frameBuffer))
        glfbo.glDeleteFramebuffersEXT(gltypes.GLuint(self.frameBuffer))

        
    def setSize(self, width, height):
        self.width  = width
        self.height = height
        self.refresh()


    def getSize(self):
        return self.width, self.height

        
    def bindAsRenderTarget(self):
        glfbo.glBindFramebufferEXT(glfbo.GL_FRAMEBUFFER_EXT, self.frameBuffer) 


    @classmethod
    def unbindAsRenderTarget(cls):
        glfbo.glBindFramebufferEXT(glfbo.GL_FRAMEBUFFER_EXT, 0) 

        
    def refresh(self, interp=None):
        if interp is None:
            interp = self.defaultInterp

        log.debug('Configuring texture {}, fbo {}, size {}'.format(
            self.getTextureHandle(),
            self.frameBuffer,
            (self.width, self.height)))

        # Configure the texture
        self.bindTexture()

        gl.glTexImage2D(gl.GL_TEXTURE_2D,
                        0,
                        gl.GL_RGBA8,
                        self.width,
                        self.height,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        None)

        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           interp)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           interp)

        # And configure the frame buffer
        self.bindAsRenderTarget()
        glfbo.glFramebufferTexture2DEXT(glfbo.GL_FRAMEBUFFER_EXT,
                                        glfbo.GL_COLOR_ATTACHMENT0_EXT,
                                        gl   .GL_TEXTURE_2D,
                                        self.getTextureHandle(),
                                        0)
            
        if glfbo.glCheckFramebufferStatusEXT(glfbo.GL_FRAMEBUFFER_EXT) != \
           glfbo.GL_FRAMEBUFFER_COMPLETE_EXT:
            raise RuntimeError('An error has occurred while '
                               'configuring the frame buffer')

        self.unbindAsRenderTarget()
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


class ImageRenderTexture(RenderTexture):
    """A :class:`RenderTexture` for off-screen volumetric rendering of an
    :class:`.Image` instance.
    """
    
    def __init__(self, image, display, xax, yax):
        """

        Note that a current target must have been set for the GL context
        before a frameBuffer can be created ... in other words, call
        ``context.SetCurrent`` before creating a ``RenderTexture``).
        """

        self.name    = '{}_{}'.format(type(self).__name__, id(self))
        self.image   = image
        self.display = display
        self.xax     = xax
        self.yax     = yax

        self._addListeners()        
        self._updateSize()
        
        RenderTexture.__init__(self, self.name, self.width, self.height)


    def _addListeners(self):

        # TODO Could change the resolution when
        #      the image type changes - vector
        #      images will need a higher
        #      resolution than voxel space

        self.display.addListener('resolution',    self.name, self._updateSize)
        self.display.addListener('interpolation', self.name, self.refresh)
        self.display.addListener('transform',     self.name, self._updateSize)

        
    def destroy(self):
        
        RenderTexture.destroy(self)
        self.display.removeListener('resolution',    self.name)
        self.display.removeListener('interpolation', self.name)
        self.display.removeListener('transform',     self.name)
        
        
    def _updateSize(self, *a):
        image      = self.image
        display    = self.display

        resolution = display.resolution / np.array(image.pixdim)
        resolution = np.round(resolution)

        if resolution[0] < 1: resolution[0] = 1
        if resolution[1] < 1: resolution[1] = 1
        if resolution[2] < 1: resolution[2] = 1
        
        # If the display transformation is 'id' or
        # 'pixdim', then the display coordinate system
        # axes line up with the voxel coordinate system
        # axes, so we can just match the voxel resolution        
        if display.transform in ('id', 'pixdim'):
            
            width  = image.shape[self.xax] / resolution[self.xax]
            height = image.shape[self.yax] / resolution[self.yax]

        # However, if we're displaying in world coordinates,
        # we cannot assume any correspondence between the
        # voxel coordinate system and the display coordinate
        # system. So we'll use a fixed size render texture
        # instead.
        elif display.transform == 'affine':
            width  = 256 / resolution.min()
            height = 256 / resolution.min()

        # Limit the width/height to an arbitrary maximum
        if width > 256 or height > 256:
            oldWidth, oldHeight = width, height
            ratio = min(width, height) / max(width, height)
            
            if width > height:
                width  = 256
                height = width * ratio
            else:
                height = 256
                width  = height * ratio

            log.debug('Limiting texture resolution to {}x{} '
                      '(for image resolution {}x{})'.format(
                          *map(int, (width, height, oldWidth, oldHeight))))

        width  = int(round(width))
        height = int(round(height))
            
        self.width  = width
        self.height = height 

    
    def setSize(self, width, height):
        raise NotImplementedError(
            'Texture size cannot be set for {} instances'.format(
                type(self).__name__))

    
    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.refresh()

        
    def refresh(self, *a):

        if self.display.interpolation == 'none': interp = gl.GL_NEAREST
        else:                                    interp = gl.GL_LINEAR

        RenderTexture.refresh(self, interp)
