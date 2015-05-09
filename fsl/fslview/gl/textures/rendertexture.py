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

import                            texture
import fsl.fslview.gl.routines as glroutines


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


    def setRenderViewport(self, xax, yax, lo, hi):

        width, height = self.getSize()
        
        self.__oldSize    = gl.glGetIntegerv(gl.GL_VIEWPORT)
        self.__oldProjMat = gl.glGetFloatv(  gl.GL_PROJECTION_MATRIX)
        self.__oldMVMat   = gl.glGetFloatv(  gl.GL_MODELVIEW_MATRIX)

        glroutines.show2D(xax, yax, width, height, lo, hi)
            

    def restoreViewport(self):

        gl.glViewport(*self.__oldSize)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadMatrixf(self.__oldProjMat)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadMatrixf(self.__oldMVMat)        
        

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
    
    def __init__(self, name, image, display, xax, yax, maxResolution=512):
        """
        """
        
        self.__image         = image
        self.__display       = display
        self.__xax           = xax
        self.__yax           = yax
        self.__maxResolution = maxResolution

        RenderTexture.__init__(self, name)

        self.__addListeners()        
        self.__updateSize()


    def __addListeners(self):

        def onInterp(*a):
            if self.__display.interpolation == 'none': interp = gl.GL_NEAREST
            else:                                      interp = gl.GL_LINEAR
            self.setInterpolation(interp)

        name = '{}_{}'.format(self.getTextureName(), id(self))

        self.__display.addListener('imageType',     name, self.__updateSize)
        self.__display.addListener('resolution',    name, self.__updateSize)
        self.__display.addListener('interpolation', name, onInterp)
        self.__display.addListener('transform',     name, self.__updateSize)

    
    def setAxes(self, xax, yax):
        self.__xax = xax
        self.__yax = yax
        self.__updateSize()

        
    def destroy(self):

        name = '{}_{}'.format(self.getTextureName(), id(self))
        
        RenderTexture.destroy(self)
        self.__display.removeListener('imageType',     name)
        self.__display.removeListener('resolution',    name)
        self.__display.removeListener('interpolation', name)
        self.__display.removeListener('transform',     name)

    
    def setSize(self, width, height):
        raise NotImplementedError(
            'Texture size cannot be set for {} instances'.format(
                type(self).__name__))
        
        
    def __updateSize(self, *a):
        image      = self.__image
        display    = self.__display
        maxRes     = self.__maxResolution

        resolution = display.resolution / np.array(image.pixdim)
        resolution = np.round(resolution)
        keepAspectRatio = True

        if resolution[0] < 1: resolution[0] = 1
        if resolution[1] < 1: resolution[1] = 1
        if resolution[2] < 1: resolution[2] = 1

        # For some image types, the display resolution
        # does not affect performance, and needs to be
        # higher than the image resolution
        if display.imageType == 'linevector':

            keepAspectRatio = False
            width  = 16 * image.shape[self.__xax] / resolution[self.__xax]
            height = 16 * image.shape[self.__yax] / resolution[self.__yax]
        
        # If the display transformation is 'id' or
        # 'pixdim', then the display coordinate system
        # axes line up with the voxel coordinate system
        # axes, so we can just match the voxel resolution        
        elif display.transform in ('id', 'pixdim'):
            
            width  = image.shape[self.__xax] / resolution[self.__xax]
            height = image.shape[self.__yax] / resolution[self.__yax]

        # However, if we're displaying in world coordinates,
        # we cannot assume any correspondence between the
        # voxel coordinate system and the display coordinate
        # system. So we'll use a fixed size render texture
        # instead.
        elif display.transform == 'affine':
            width  = maxRes / resolution.min()
            height = maxRes / resolution.min()

        # Limit the width/height to an arbitrary maximum
        if not keepAspectRatio:
            if width  > maxRes: width  = maxRes
            if height > maxRes: height = maxRes
        elif width > maxRes or height > maxRes:
            oldWidth, oldHeight = width, height
            ratio = min(width, height) / max(width, height)
            
            if width > height:
                width  = maxRes
                height = width * ratio
            else:
                height = maxRes
                width  = height * ratio

            log.debug('Limiting texture resolution to {}x{} '
                      '(for image resolution {}x{})'.format(
                          *map(int, (width, height, oldWidth, oldHeight))))

        width  = int(round(width))
        height = int(round(height))

        RenderTexture.setSize(self, width, height)
