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


class RenderTexture(texture.Texture2D):
    """A 2D texture and frame buffer, intended to be used as a target for
    off-screen rendering of a scene.
    """
    
    def __init__(self, name, interp=gl.GL_NEAREST):
        """

        Note that a current target must have been set for the GL context
        before a frameBuffer can be created ... in other words, call
        ``context.SetCurrent`` before creating a ``RenderTexture``).
        """

        texture.Texture2D.__init__(self, name, interp)
        
        self.__frameBuffer = glfbo.glGenFramebuffersEXT(1)
        log.debug('Created fbo: {}'.format(self.__frameBuffer))

        
    def destroy(self):
        texture.Texture.destroy(self)

        log.debug('Deleting fbo {}'.format(self.__frameBuffer))
        glfbo.glDeleteFramebuffersEXT(gltypes.GLuint(self.__frameBuffer))


    def setData(self, data):
        raise NotImplementedError('Texture data cannot be set for {} '
                                  'instances'.format(type(self).__name__))


    def bindAsRenderTarget(self):
        glfbo.glBindFramebufferEXT(glfbo.GL_FRAMEBUFFER_EXT,
                                   self.__frameBuffer) 


    @classmethod
    def unbindAsRenderTarget(cls):
        glfbo.glBindFramebufferEXT(glfbo.GL_FRAMEBUFFER_EXT, 0) 

        
    def refresh(self):
        texture.Texture2D.refresh(self)

        # Configure the frame buffer
        self.bindTexture()
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


class ImageRenderTexture(RenderTexture):
    """A :class:`RenderTexture` for off-screen volumetric rendering of an
    :class:`.Image` instance.
    """
    
    def __init__(self, image, display, xax, yax):
        """
        """
        
        self.__name    = '{}_{}'.format(type(self).__name__, id(self))
        self.__image   = image
        self.__display = display
        self.__xax     = xax
        self.__yax     = yax

        RenderTexture.__init__(self, self.__name)

        self.__addListeners()        
        self.__updateSize()


    def __addListeners(self):

        # TODO Could change the resolution when
        #      the image type changes - vector
        #      images will need a higher
        #      resolution than voxel space

        def onInterp(*a):
            if self.__display.interpolation == 'none': interp = gl.GL_NEAREST
            else:                                      interp = gl.GL_LINEAR
            self.setInterpolation(interp)

        self.__display.addListener('resolution',
                                   self.__name,
                                   self.__updateSize)
        self.__display.addListener('interpolation',
                                   self.__name,
                                   self.refresh)
        self.__display.addListener('transform',
                                   self.__name,
                                   self.__updateSize)

    
    def setAxes(self, xax, yax):
        self.__xax = xax
        self.__yax = yax
        self.refresh()

        
    def destroy(self):
        
        RenderTexture.destroy(self)
        self.__display.removeListener('resolution',    self.__name)
        self.__display.removeListener('interpolation', self.__name)
        self.__display.removeListener('transform',     self.__name)

    
    def setSize(self, width, height):
        raise NotImplementedError(
            'Texture size cannot be set for {} instances'.format(
                type(self).__name__))
        
        
    def __updateSize(self, *a):
        image      = self.__image
        display    = self.__display

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
            
            width  = image.shape[self.__xax] / resolution[self.__xax]
            height = image.shape[self.__yax] / resolution[self.__yax]

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

        RenderTexture.setSize(self, width, height)
