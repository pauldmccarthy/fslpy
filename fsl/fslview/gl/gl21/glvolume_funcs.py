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

import fsl.fslview.gl.globject as globject
import fsl.fslview.gl.shaders  as shaders
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)

def _compileShaders(self):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program, and
    all GLSL variables, to the given GLVolume object. 
    """

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self)
    self.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    # indices of all vertex/fragment shader parameters
    self.vertexPos          = gl.glGetAttribLocation( self.shaders,
                                                       'vertex')
    self.voxCoordPos        = gl.glGetAttribLocation( self.shaders,
                                                       'voxCoord') 
    self.imageTexturePos    = gl.glGetUniformLocation(self.shaders,
                                                       'imageTexture')
    self.colourTexturePos   = gl.glGetUniformLocation(self.shaders,
                                                       'colourTexture') 
    self.imageShapePos      = gl.glGetUniformLocation(self.shaders,
                                                       'imageShape')
    self.useSplinePos       = gl.glGetUniformLocation(self.shaders,
                                                       'useSpline')
    self.voxValXformPos     = gl.glGetUniformLocation(self.shaders,
                                                       'voxValXform')
    self.clipLowPos         = gl.glGetUniformLocation(self.shaders,
                                                       'clipLow')
    self.clipHighPos        = gl.glGetUniformLocation(self.shaders,
                                                       'clipHigh') 


def init(self):
    """Compiles the vertex and fragment shaders used to render image slices.
    """
    _compileShaders(self)

    self.vertexBuffer   = gl.glGenBuffers(1)
    self.voxCoordBuffer = gl.glGenBuffers(1)
    self.indexBuffer    = gl.glGenBuffers(1)

    indices = np.arange(6, dtype=np.uint32)

    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)
    gl.glBufferData(gl.GL_ELEMENT_ARRAY_BUFFER,
                    indices.nbytes,
                    indices,
                    gl.GL_STATIC_DRAW)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
                    

def destroy(self):
    """Cleans up VBO handles."""

    gl.glDeleteBuffers(1, gltypes.GLuint(self.vertexBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.voxCoordBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(self.indexBuffer))
    gl.glDeleteProgram(self.shaders)


def preDraw(self):
    """Sets up the GL state to draw a slice from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    display = self.display
    opts    = self.displayOpts

    # load the shaders
    gl.glUseProgram(self.shaders)

    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( self.useSplinePos,     display.interpolation == 'spline')
    gl.glUniform3fv(self.imageShapePos, 1, np.array(self.image.shape,
                                                     dtype=np.float32))

    # The clipping range options are in the voxel value
    # range, but the shader needs them to be in image
    # texture value range (0.0 - 1.0). So let's scale 
    # them.
    clipLow = opts.clippingRange[0]           * \
        self.imageTexture.invVoxValXform[0, 0] + \
        self.imageTexture.invVoxValXform[3, 0]
    clipHigh = opts.clippingRange[1]          * \
        self.imageTexture.invVoxValXform[0, 0] + \
        self.imageTexture.invVoxValXform[3, 0] 

    gl.glUniform1f(self.clipLowPos,  clipLow)
    gl.glUniform1f(self.clipHighPos, clipHigh)

    # Bind transformation matrices to transform
    # display coordinates to voxel coordinates,
    # and to scale voxel values to colour map
    # texture coordinates
    vvx = transform.concat(self.imageTexture.voxValXform,
                           self.colourTexture.getCoordinateTransform())
    vvx = np.array(vvx, dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(self.voxValXformPos, 1, False, vvx)

    # Set up the colour and image textures
    gl.glUniform1i(self.imageTexturePos,  0)
    gl.glUniform1i(self.colourTexturePos, 1)


def draw(self, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg image:   The :class:`~fsl.fslview.gl.glvolume.GLVolume` object which
                  is managing the image to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """
    
    vertices, _ = globject.slice2D(
        self.image.shape[:3],
        self.xax,
        self.yax,
        self.display.getTransform('voxel', 'display'))

    vertices[:, self.zax] = zpos
    
    voxCoords = transform.transform(
        vertices,
        self.display.getTransform('display', 'voxel'))

    if xform is not None: 
        vertices = transform.transform(vertices, xform)

    vertices  = np.array(vertices,  dtype=np.float32).ravel('C')
    voxCoords = np.array(voxCoords, dtype=np.float32).ravel('C')

    # Bind the world x/y coordinate buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vertexBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER,
                    vertices.nbytes,
                    vertices,
                    gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        self.vertexPos,
        3,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.vertexPos)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.voxCoordBuffer)
    gl.glBufferData(gl.GL_ARRAY_BUFFER,
                    voxCoords.nbytes,
                    voxCoords,
                    gl.GL_STATIC_DRAW)
    gl.glVertexAttribPointer(
        self.voxCoordPos,
        3,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(self.voxCoordPos)    

    # Bind the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, self.indexBuffer)

    # Draw all of the triangles!
    gl.glDrawElements(gl.GL_TRIANGLES,
                      6,
                      gl.GL_UNSIGNED_INT,
                      None)


def drawAll(self, zposes, xforms):
    """Delegates to the default implementation in
    :meth:`~fsl.fslview.gl.globject.GLObject.drawAll`.
    """
    globject.GLObject.drawAll(self, zposes, xforms)


def postDraw(self):
    """Cleans up the GL state after drawing from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    gl.glDisableVertexAttribArray(self.vertexPos)
    gl.glDisableVertexAttribArray(self.voxCoordPos)
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)
    gl.glUseProgram(0)
