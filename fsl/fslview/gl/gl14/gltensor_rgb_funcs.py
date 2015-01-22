#!/usr/bin/env python
#
# gltensor_rgb_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


######################
# Methods for RGB mode
######################

# The tensor data is stored as a 3D RGB texture,
# and rendered as a four-vertex slice through said
# texture. The fragment program looks up each of
# the texture values, and calculates the appropriate
# colour (red for axial, blue for sagittal, green
# for coronal?) for the fragment


def init(self):

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self) 

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram

    createImageTexture(self)

    # This matrix is used by the tensor fragment
    # program to transform tensor values (which
    # are assumed to lie in the range [-1.0, 1.0]
    # to the range [0.0, 1.0], for texture lookup.
    # We can customised this if we get tensor data
    # which is not in the range [-1.0, 1.0]
    self.voxValXform = transform.scaleOffsetXform(
        [0.5, 0.5, 0.5], [1.0, 1.0, 1.0])

    def imageUpdate(*a):
        createImageTexture(self)

    self.display.addListener('interpolation', self.name, imageUpdate)
    self.display.addListener('resolution',    self.name, imageUpdate)


def destroy(self):

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    # Another GLTensor object may have
    # already deleted the image texture
    try:
        imageTexture = self.image.delAttribute(
            '{}Texture'.format(type(self).__name__))
        log.debug('Deleting GL texture: {}'.format(imageTexture))
        gl.glDeleteTextures(1, imageTexture)
        
    except KeyError:
        pass

    self.display.removeListener('interpolation', self.name)
    self.display.removeListener('resolution',    self.name)

    del self.vertexProgram
    del self.fragmentProgram
    del self.imageTexture
    del self.imageTextureShape
    del self.worldCoords
    del self.indices
    del self.voxValXform


def setAxes(self):

    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs

    
def createImageTexture(self, *a):

    image   = self.image
    display = self.display

    textureData = globject.subsample(image.data,
                                     display.resolution,
                                     image.pixdim)

    texDataShape = textureData.shape

    textureData = np.abs(textureData)

    dmin        = textureData.min()
    dmax        = textureData.max()
    textureData = 255.0 * (textureData - dmin) / (dmax - dmin)
    textureData = np.array(textureData, dtype=np.uint8)
    
    # Check to see if the image texture
    # has already been created
    try:
        imageTexture = image.getAttribute(
            '{}Texture'.format(type(self).__name__))
    except:
        imageTexture = None

    if imageTexture is None:
        imageTexture = gl.glGenTextures(1)
        log.debug('Created GL texture: {}'.format(imageTexture))
        
    elif not image.getAttribute('{}Dirty'.format(type(self).__name__)):
        self.imageTexture      = imageTexture
        self.imageTextureShape = texDataShape
        return

    self.imageTexture      = imageTexture
    self.imageTextureShape = texDataShape

    textureData = textureData.transpose((3, 0, 1, 2)).ravel('F')
    
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

    if display.interpolation == 'none': interp = gl.GL_NEAREST
    else:                               interp = gl.GL_LINEAR

    gl.glBindTexture(gl.GL_TEXTURE_3D, imageTexture)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_MAG_FILTER,
                       interp)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_MIN_FILTER,
                       interp) 

    gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                        gl.GL_TEXTURE_BORDER_COLOR,
                        np.array([0, 0, 0, 0], dtype=np.float32))
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_WRAP_S,
                       gl.GL_CLAMP_TO_BORDER)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_WRAP_T,
                       gl.GL_CLAMP_TO_BORDER)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_WRAP_R,
                       gl.GL_CLAMP_TO_BORDER)
    
    gl.glTexImage3D(gl.GL_TEXTURE_3D,
                    0,
                    gl.GL_RGB8,
                    texDataShape[0],
                    texDataShape[1],
                    texDataShape[2],
                    0,
                    gl.GL_RGB, 
                    gl.GL_UNSIGNED_BYTE,
                    textureData)


def preDraw(self):

    if not self.display.enabled:
        return

    gl.glEnable(gl.GL_TEXTURE_3D)

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    # the fragment program needs to know the image
    # shape and its inverse, so it can scale voxel
    # coordinates to the range [0.0, 1.0], and so
    # it can  clip fragments outside of the image
    # space
    shape = self.image.shape
    arbfp.glProgramLocalParameter4fARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                       0,
                                       shape[0],
                                       shape[1],
                                       shape[2],
                                       0)
    arbfp.glProgramLocalParameter4fARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                       1,
                                       1.0 / shape[0],
                                       1.0 / shape[1],
                                       1.0 / shape[2],
                                       0)

    # The fragment program usees the displayToVoxMat
    # to transform from display coordinates to voxel
    # coordinates
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPushMatrix()
    gl.glLoadMatrixf(self.display.displayToVoxMat)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPushMatrix()
    gl.glLoadMatrixf(self.voxValXform) 
    
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, self.imageTexture)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    self.mvmat = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX) 


def draw(self, zpos, xform=None):

    display = self.display
    
    if not display.enabled:
        return

    worldCoords  = self.worldCoords
    indices      = self.indices
    worldCoords[:, self.zax] = zpos

    worldCoords = worldCoords.ravel('C')

    if xform is not None:
        xform = transform.concat(xform, self.mvmat)
        gl.glLoadMatrixf(xform)

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices) 


def postDraw(self):

    if not self.display.enabled:
        return

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPopMatrix()

    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPopMatrix() 
    
    gl.glDisable(gl.GL_TEXTURE_3D) 
