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

This module is extremely tightly coupled to the vertex and fragment shader
programs (`glvolume_vert.glsl` and `glvolume_frag.glsl` respectively).

This module provides the following functions:

 - :func:`init`: Compiles vertex and fragment shaders.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image. Actually returns handles to
   VBOs which encapsulate the vertex and texture coordinates.

 - :func:`destroy`: Deletes the vertex and texture coordinate VBOs.
"""

import logging
log = logging.getLogger(__name__)

import numpy                  as np
import OpenGL.GL              as gl
import OpenGL.raw.GL._types   as gltypes

import fsl.fslview.gl.shaders as shaders
import fsl.utils.transform    as transform


def _compileShaders(glvol):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program, and
    all GLSL variables, to the given GLVolume object. 
    """

    vertShaderSrc = shaders.getVertexShader(  glvol)
    fragShaderSrc = shaders.getFragmentShader(glvol)
    glvol.shaders = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

    # indices of all vertex/fragment shader parameters
    glvol.worldToWorldMatPos = gl.glGetUniformLocation(glvol.shaders,
                                                       'worldToWorldMat')
    glvol.xaxPos             = gl.glGetUniformLocation(glvol.shaders,
                                                       'xax')
    glvol.yaxPos             = gl.glGetUniformLocation(glvol.shaders,
                                                       'yax')
    glvol.zaxPos             = gl.glGetUniformLocation(glvol.shaders,
                                                       'zax')
    glvol.worldCoordPos      = gl.glGetAttribLocation( glvol.shaders,
                                                       'worldCoords') 
    glvol.zCoordPos          = gl.glGetUniformLocation(glvol.shaders,
                                                       'zCoord')
    
    glvol.imageTexturePos    = gl.glGetUniformLocation(glvol.shaders,
                                                       'imageTexture')
    glvol.imageShapePos      = gl.glGetUniformLocation(glvol.shaders,
                                                       'imageShape')
    glvol.colourTexturePos   = gl.glGetUniformLocation(glvol.shaders,
                                                       'colourTexture') 
    glvol.useSplinePos       = gl.glGetUniformLocation(glvol.shaders,
                                                       'useSpline')
    glvol.displayToVoxMatPos = gl.glGetUniformLocation(glvol.shaders,
                                                       'displayToVoxMat')
    glvol.voxValXformPos     = gl.glGetUniformLocation(glvol.shaders,
                                                       'voxValXform') 


def init(glvol):
    """Compiles the vertex and fragment shaders used to render image slices.
    """
    _compileShaders(glvol)

    glvol.worldCoordBuffer = gl.glGenBuffers(1)
    glvol.indexBuffer      = gl.glGenBuffers(1) 


def destroy(glvol):
    """Cleans up VBO handles."""

    gl.glDeleteBuffers(1, gltypes.GLuint(glvol.worldCoordBuffer))
    gl.glDeleteBuffers(1, gltypes.GLuint(glvol.indexBuffer))
    gl.glDeleteProgram(glvol.shaders)


def genVertexData(glvol):
    """Generates vertex and texture coordinates required to render the
    image, and associates them with OpenGL VBOs . See
    :func:`fsl.fslview.gl.glvolume.genVertexData`.
    """ 
    xax = glvol.xax
    yax = glvol.yax

    worldCoordBuffer     = glvol.worldCoordBuffer
    indexBuffer          = glvol.indexBuffer
    worldCoords, indices = glvol.genVertexData()

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


def preDraw(glvol):
    """Sets up the GL state to draw a slice from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    display = glvol.display
    if not display.enabled: return

    # load the shaders
    gl.glUseProgram(glvol.shaders)
    
    gl.glEnable(gl.GL_TEXTURE_1D)
    gl.glEnable(gl.GL_TEXTURE_3D)

    # bind the current interpolation setting,
    # image shape, and image->screen axis
    # mappings
    gl.glUniform1f( glvol.useSplinePos,     display.interpolation == 'spline')
    
    gl.glUniform3fv(glvol.imageShapePos, 1, np.array(glvol.imageShape,
                                                     dtype=np.float32))
    gl.glUniform1i( glvol.xaxPos,           glvol.xax)
    gl.glUniform1i( glvol.yaxPos,           glvol.yax)
    gl.glUniform1i( glvol.zaxPos,           glvol.zax)

    # Bind transformation matrices to transform
    # display coordinates to voxel coordinates,
    # and to scale voxel values to colour map
    # texture coordinates
    tcx = transform.concat(glvol.voxValXform, glvol.colourMapXform)
    w2v = np.array(display.displayToVoxMat, dtype=np.float32).ravel('C')
    vvx = np.array(tcx,                     dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(glvol.displayToVoxMatPos, 1, False, w2v)
    gl.glUniformMatrix4fv(glvol.voxValXformPos,     1, False, vvx)

    # Enable storage of tightly packed data
    # of any size, for our 3D image texture 
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1) 
    
    # Set up the colour texture
    gl.glActiveTexture(gl.GL_TEXTURE0) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glvol.colourTexture)
    gl.glUniform1i(glvol.colourTexturePos, 0) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_3D, glvol.imageTexture)
    gl.glUniform1i(glvol.imageTexturePos, 1)

    # Bind the world x/y coordinate buffer
    gl.glBindBuffer(gl.GL_ARRAY_BUFFER, glvol.worldCoords)
    gl.glVertexAttribPointer(
        glvol.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(glvol.worldCoordPos)

    # Bind the vertex index buffer
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, glvol.indices)


def draw(glvol, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg image:   The :class:`~fsl.fslview.gl.glvolume.GLVolume` object which
                  is managing the image to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """
    display = glvol.display
    if not display.enabled: return 
    
    if xform is None: xform = np.identity(4)
    
    w2w = np.array(xform, dtype=np.float32).ravel('C')

    # Bind the current world z position, and
    # the xform transformation matrix
    gl.glUniform1f(       glvol.zCoordPos,                    zpos)
    gl.glUniformMatrix4fv(glvol.worldToWorldMatPos, 1, False, w2w)

    # Draw all of the triangles!
    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      glvol.nVertices,
                      gl.GL_UNSIGNED_INT,
                      None)


def postDraw(glvol):
    """Cleans up the GL state after drawing from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    if not glvol.display.enabled: return

    gl.glDisableVertexAttribArray(glvol.worldCoordPos)

    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

    gl.glDisable(gl.GL_TEXTURE_1D)
    gl.glDisable(gl.GL_TEXTURE_3D)

    gl.glBindBuffer(gl.GL_ARRAY_BUFFER,         0)
    gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, 0)

    gl.glUseProgram(0)
