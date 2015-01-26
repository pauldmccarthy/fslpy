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
import fsl.data.image          as fslimage
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

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self) 

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram

    self.xColourTexture = gl.glGenTextures(1)
    self.yColourTexture = gl.glGenTextures(1)
    self.zColourTexture = gl.glGenTextures(1)

    def prefilter(data):
        return np.abs(data.transpose((3, 0, 1, 2)))

    self.imageTexture = fsltextures.getTexture(
        self.image,
        type(self).__name__,
        display=self.display,
        nvals=3,
        normalise=True,
        prefilter=prefilter)

    self.modTexture = None

    createColourTextures( self)
    createModulateTexture(self)

    display = self.display
    opts    = self.displayOpts
    lName   = self.name

    def modUpdate( *a): createModulateTexture(self)
    def cmapUpdate(*a): createColourTextures( self)

    display.addListener('alpha',         lName, cmapUpdate)
    opts   .addListener('xColour',       lName, cmapUpdate)
    opts   .addListener('yColour',       lName, cmapUpdate)
    opts   .addListener('zColour',       lName, cmapUpdate)
    opts   .addListener('suppressX',     lName, cmapUpdate)
    opts   .addListener('suppressY',     lName, cmapUpdate)
    opts   .addListener('suppressZ',     lName, cmapUpdate)
    opts   .addListener('modulate',      lName, modUpdate)
    

def destroy(self):

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    gl.glDeleteTextures(self.xColourTexture)
    gl.glDeleteTextures(self.yColourTexture)
    gl.glDeleteTextures(self.zColourTexture)

    fsltextures.deleteTexture(self.imageTexture)
    fsltextures.deleteTexture(self.modTexture)
    
    self.display    .removeListener('alpha',     self.name)
    self.displayOpts.removeListener('xColour',   self.name)
    self.displayOpts.removeListener('yColour',   self.name)
    self.displayOpts.removeListener('zColour',   self.name)
    self.displayOpts.removeListener('suppressX', self.name)
    self.displayOpts.removeListener('suppressY', self.name)
    self.displayOpts.removeListener('suppressZ', self.name) 


def setAxes(self):

    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs


def createModulateTexture(self):
    
    modImage = self.displayOpts.modulate

    if self.modTexture is not None:
        fsltextures.deleteTexture(self.modTexture)

    if modImage == 'none':
        textureData = np.zeros((5, 5, 5), dtype=np.uint8)
        textureData[:] = 255
        modImage   = fslimage.Image(textureData)
        modDisplay = None
        norm       = False
    else:
        modDisplay = self.display
        norm       = True

    self.modTexture = fsltextures.getTexture(
        modImage,
        '{}_{}_modulate'.format(type(self).__name__, id(self.image)),
        display=modDisplay,
        normalise=norm)


def createColourTextures(self, colourRes=256):


    xcol = self.displayOpts.xColour + [1.0]
    ycol = self.displayOpts.yColour + [1.0]
    zcol = self.displayOpts.zColour + [1.0]

    xsup = self.displayOpts.suppressX
    ysup = self.displayOpts.suppressY
    zsup = self.displayOpts.suppressZ 

    xtex = self.xColourTexture
    ytex = self.yColourTexture
    ztex = self.zColourTexture

    for colour, texture, suppress in zip(
            (xcol, ycol, zcol),
            (xtex, ytex, ztex),
            (xsup, ysup, zsup)):

        if not suppress:
            cmap = np.array([np.linspace(0.0, i, colourRes) for i in colour])
        else:
            cmap = np.zeros((4, colourRes))

        cmap[3, :] = self.display.alpha
        cmap[3, 0] = 0.0

        cmap = np.array(np.floor(cmap * 255), dtype=np.uint8).ravel('F')

        gl.glBindTexture(gl.GL_TEXTURE_1D, texture)
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
                        colourRes,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        cmap)
        
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)


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
