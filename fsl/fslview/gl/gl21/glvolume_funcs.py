#!/usr/bin/env python
#
# glvolume_funcs.py - Functions used by the fsl.fslview.gl.glvolume.GLVolume 
#                     class to render 3D images in an OpenGL 2.1 compatible 
#                     manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLVolume object encapsulates the OpenGL information necessary
to render 2D slices of a 3D image, in an OpenGL 2.1 compatible manner.

This module is extremely tightly coupled to the fragment shader
program ``glvolume_frag.glsl``.

This module provides the following functions:

 - :func:`init`: Compiles vertex and fragment shaders.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image. Actually returns handles to
   VBOs which encapsulate the vertex and texture coordinates.

 - :func:`preDraw`:  Prepares the GL state for drawing.

 - :func:`draw`:     Draws the scene.

 - :func:`postDraw`: Resets the GL state after drawing.

 - :func:`destroy`:  Deletes the vertex and texture coordinate VBOs.
"""

import logging

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fslview.gl.shaders as shaders
import fsl.utils.transform    as transform


log = logging.getLogger(__name__)

def _compileShaders(self):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program, and
    all GLSL variables, to the given GLVolume object. 
    """

    vertShaderSrc = shaders.getVertexShader('generic')
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    # indices of all vertex/fragment shader parameters
    self.worldToWorldMatPos = gl.glGetUniformLocation(self.shaders,
                                                       'worldToWorldMat')
    self.xaxPos             = gl.glGetUniformLocation(self.shaders,
                                                       'xax')
    self.yaxPos             = gl.glGetUniformLocation(self.shaders,
                                                       'yax')
    self.zaxPos             = gl.glGetUniformLocation(self.shaders,
                                                       'zax')
    self.worldCoordPos      = gl.glGetAttribLocation( self.shaders,
                                                       'worldCoords') 
    self.zCoordPos          = gl.glGetUniformLocation(self.shaders,
                                                       'zCoord')
    
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                       'imageTexture')
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                       'imageShape')
    self.colourTexturePos   = gl.glGetUniformLocation(self.shaders,
                                                       'colourTexture') 
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                       'useSpline')
    self.displayToVoxMatPos = gl.glGetUniformLocation(self.shaders,
                                                       'displayToVoxMat')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                       'voxValXform') 


def init(self):
    """Compiles the vertex and fragment shaders used to render image slices.
    """
    _compileShaders(self)

    self.worldCoordBuffer = gl.glGenBuffers(1)
    self.indexBuffer      = gl.glGenBuffers(1) 


def destroy(self):
    """Cleans up VBO handles."""

    gl.glDeleteBuffers(1, gltypes.GLuint(self.worldCoordBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.indexBuffer))
    gl.glDeleteProgram(self.shaders)


def genVertexData(self):
    """Generates vertex and texture coordinates required to render the
    image, and associates them with OpenGL VBOs . See
    :func:`fsl.fslview.gl.glvolume.genVertexData`.
    """ 
    xax = self.xax
    yax = self.yax

    worldCoordBuffer     = self.worldCoordBuffer
    indexBuffer          = self.indexBuffer
    worldCoords, indices = self.genVertexData()

    worldCoords = worldCoords[:, [xax, yax]]

    worldCoords = worldCoords.ravel('C')
    indices     = indices    .ravel('C')
    
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, worldCoordBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER, 
                    worldCoords.nbytes,
                    worldCoords,
                    gl.GL_STATIC_DRAW)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, indexBuffer)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW)

    return worldCoordBuffer, indexBuffer, len(indices)


def preDraw(self):
    """Sets up the GL state to draw a slice from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    display = self.display
    if not display.enabled: return

    # load the shaders
    gl.glUseProgram(self.shaders)
    
    gl.glEnable(gl.GL_TEXTURE_1D)
    gl.glEnable(gl.GL_TEXTURE_3D)

    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( self.useSplinePos,     display.interpolation == 'spline')
    
    gl.glUniform3fv(self.imageShapePos, 1, np.array(self.image.shape,
                                                     dtype=np.float32))
    gl.glUniform1i( self.xaxPos,           self.xax)
    gl.glUniform1i( self.yaxPos,           self.yax)
    gl.glUniform1i( self.zaxPos,           self.zax)

    # Bind transformation matrices to transform
    # display coordinates to voxel coordinates,
    # and to scale voxel values to colour map
    # texture coordinates
    tcx = transform.concat(self.imageTexture.voxValXform,
                           self.colourMapXform)
    w2v = np.array(display.displayToVoxMat, dtype=np.float32).ravel('C')
    vvx = np.array(tcx,                     dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(self.displayToVoxMatPos, 1, False, w2v)
    gl.glUniformMatrix4fv(self.voxValXformPos,     1, False, vvx)

    # Set up the colour and image textures
    gl.glUniform1i(self.colourTexturePos, 0) 
    gl.glUniform1i(self.imageTexturePos,  1)

    # Bind the world x/y coordinate buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.worldCoords)
    gl.glVertexAttribPointer(
        self.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.worldCoordPos)

    # Bind the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indices)


def draw(self, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg image:   The :class:`~fsl.fslview.gl.glvolume.GLVolume` object which
                  is managing the image to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """
    display = self.display
    if not display.enabled: return 
    
    if xform is None: xform = np.identity(4)
    
    w2w = np.array(xform, dtype=np.float32).ravel('C')

    # Bind the current world z position, and
    # the xform transformation matrix
    gl.glUniform1f(       self.zCoordPos,                    zpos)
    gl.glUniformMatrix4fv(self.worldToWorldMatPos, 1, False, w2w)

    # Draw all of the triangles!
    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      self.nVertices,
                      gl.GL_UNSIGNED_INT,
                      None)


def postDraw(self):
    """Cleans up the GL state after drawing from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    if not self.display.enabled: return

    gl.glDisableVertexAttribArray(self.worldCoordPos)

    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

    gl.glDisable(gl.GL_TEXTURE_1D)
    gl.glDisable(gl.GL_TEXTURE_3D)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    gl.glUseProgram(0)
