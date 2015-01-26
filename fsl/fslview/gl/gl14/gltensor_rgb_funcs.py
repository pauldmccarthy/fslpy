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

import fsl.utils.transform     as transform
import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.textures as fsltextures
import fsl.fslview.gl.globject as globject

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

    vertShaderSrc = shaders.getVertexShader(  'gltensor_rgb')
    fragShaderSrc = shaders.getFragmentShader('gltensor_rgb')

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram

    def prefilter(data):
        return np.abs(data.transpose((3, 0, 1, 2)))

    self.imageTexture = fsltextures.getTexture(
        self.image,
        type(self).__name__,
        display=self.display,
        nvals=3,
        normalise=True,
        prefilter=prefilter)


def destroy(self):

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    fsltextures.deleteTexture(self.imageTexture)


def setAxes(self):

    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs


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
    # it can clip fragments outside of the image
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
    
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, self.imageTexture.texture)

    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glBindTexture(gl.GL_TEXTURE_3D, self.modTexture.texture) 

    gl.glActiveTexture(gl.GL_TEXTURE2)
    gl.glBindTexture(gl.GL_TEXTURE_1D, self.xColourTexture)
    
    gl.glActiveTexture(gl.GL_TEXTURE3)
    gl.glBindTexture(gl.GL_TEXTURE_1D, self.yColourTexture)

    gl.glActiveTexture(gl.GL_TEXTURE4)
    gl.glBindTexture(gl.GL_TEXTURE_1D, self.zColourTexture) 

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

    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

    gl.glActiveTexture(gl.GL_TEXTURE2)
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)

    gl.glActiveTexture(gl.GL_TEXTURE3)
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    
    gl.glActiveTexture(gl.GL_TEXTURE4)
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)    

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPopMatrix()
    
    gl.glDisable(gl.GL_TEXTURE_3D) 
