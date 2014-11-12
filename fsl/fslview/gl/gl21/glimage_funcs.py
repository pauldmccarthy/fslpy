#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 2.1 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLImage object encapsulates the OpenGL information necessary
to render 2D slices of a 3D image, in an OpenGL 2.1 compatible manner.

This module is extremely tightly coupled to the vertex and fragment shader
programs (`vertex_shader.glsl` and `fragment_shader.glsl` respectively).

This module provides the following functions:

 - :func:`init`: Compiles vertex and fragment shaders.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image. Actually returns handles to
   VBOs which encapsulate the vertex and texture coordinates.

 - :func:`destroy`: Deletes the vertex and texture coordinate VBOs.
"""

import logging
log = logging.getLogger(__name__)

import numpy             as np
import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

import shaders
import fsl.utils.transform as transform


def _compileShaders(glimg):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and attaches a reference to the resulting program to
    the given GLImage object. Raises an error if compilation/linking
    fails.

    I'm explicitly not using the PyOpenGL
    :func:`OpenGL.GL.shaders.compileProgram` function, because it attempts
    to validate the program after compilation, which fails due to texture
    data not being bound at the time of validation.
    """

    vertShaderSrc = shaders.getVertexShader(  glimg)
    fragShaderSrc = shaders.getFragmentShader(glimg)

    # vertex shader
    vertShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
    gl.glShaderSource(vertShader, vertShaderSrc)
    gl.glCompileShader(vertShader)
    vertResult = gl.glGetShaderiv(vertShader, gl.GL_COMPILE_STATUS)

    if vertResult != gl.GL_TRUE:
        raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(vertShader)))

    # fragment shader
    fragShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
    gl.glShaderSource(fragShader, fragShaderSrc)
    gl.glCompileShader(fragShader)
    fragResult = gl.glGetShaderiv(fragShader, gl.GL_COMPILE_STATUS)

    if fragResult != gl.GL_TRUE:
        raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(fragShader)))

    # link all of the shaders!
    program = gl.glCreateProgram()
    gl.glAttachShader(program, vertShader)
    gl.glAttachShader(program, fragShader)

    gl.glLinkProgram(program)

    gl.glDeleteShader(vertShader)
    gl.glDeleteShader(fragShader)

    linkResult = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)

    if linkResult != gl.GL_TRUE:
        raise RuntimeError('{}'.format(gl.glGetProgramInfoLog(program)))

    glimg.shaders = program

    # Indices of all vertex/fragment shader parameters
    glimg.worldToWorldMatPos = gl.glGetUniformLocation(glimg.shaders,
                                                       'worldToWorldMat')
    glimg.xaxPos             = gl.glGetUniformLocation(glimg.shaders,
                                                       'xax')
    glimg.yaxPos             = gl.glGetUniformLocation(glimg.shaders,
                                                       'yax')
    glimg.zaxPos             = gl.glGetUniformLocation(glimg.shaders,
                                                       'zax')
    glimg.worldCoordPos      = gl.glGetAttribLocation( glimg.shaders,
                                                       'worldCoords') 
    glimg.zCoordPos          = gl.glGetUniformLocation(glimg.shaders,
                                                       'zCoord')
    
    glimg.imageTexturePos    = gl.glGetUniformLocation(glimg.shaders,
                                                       'imageTexture')
    glimg.imageShapePos      = gl.glGetUniformLocation(glimg.shaders,
                                                       'imageShape')
    glimg.colourTexturePos   = gl.glGetUniformLocation(glimg.shaders,
                                                       'colourTexture') 
    glimg.useSplinePos       = gl.glGetUniformLocation(glimg.shaders,
                                                       'useSpline')
    glimg.displayToVoxMatPos  = gl.glGetUniformLocation(glimg.shaders,
                                                        'displayToVoxMat')
    glimg.voxValXformPos      = gl.glGetUniformLocation(glimg.shaders,
                                                        'voxValXform') 


def init(glimg, xax, yax):
    """Compiles the vertex and fragment shaders used to render image slices.
    """
    _compileShaders(glimg)


def destroy(glimg):
    """Cleans up VBO handles."""
    glimg.worldCoords.delete()
    glimg.indices    .delete()


def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render the
    image, and associates them with OpenGL VBOs . See
    :func:`fsl.fslview.gl.glimage.genVertexData`.
    """ 
    xax = glimg.xax
    yax = glimg.yax

    worldCoords, texCoords, indices = glimg.genVertexData()

    worldCoords = worldCoords[:, [xax, yax]]

    worldCoordBuffer = vbo.VBO(worldCoords.ravel('C'), gl.GL_STATIC_DRAW)
    indexBuffer      = vbo.VBO(indices    .ravel('C'), gl.GL_STATIC_DRAW,
                               gl.GL_ELEMENT_ARRAY_BUFFER)

    return worldCoordBuffer, texCoords, indexBuffer, len(indices)


def draw(glimg, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    :arg image:   The :class:`~fsl.fslview.gl..GLImage` object which is 
                  managing the image to be drawn.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the vertex
                  data.
    """

    image   = glimg.image
    display = glimg.display

    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    # load the shaders
    gl.glUseProgram(glimg.shaders) 

    # bind the current alpha value
    # and data range to the shader
    gl.glUniform1f( glimg.useSplinePos,     display.interpolation == 'spline')
    gl.glUniform1f( glimg.zCoordPos,        zpos)
    gl.glUniform3fv(glimg.imageShapePos, 1, np.array(image.shape,
                                                     dtype=np.float32))
    gl.glUniform1i( glimg.xaxPos,           glimg.xax)
    gl.glUniform1i( glimg.yaxPos,           glimg.yax)
    gl.glUniform1i( glimg.zaxPos,           glimg.zax)
    
    # bind the transformation matrices
    # to the shader variable
    if xform is None: xform = np.identity(4)

    tcx = transform.concat(glimg.voxValXform, glimg.colourMapXform)
    w2w = np.array(xform,                   dtype=np.float32).ravel('C')
    w2v = np.array(display.displayToVoxMat, dtype=np.float32).ravel('C')
    vvx = np.array(tcx,                     dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(glimg.displayToVoxMatPos, 1, False, w2v)
    gl.glUniformMatrix4fv(glimg.worldToWorldMatPos, 1, False, w2w)
    gl.glUniformMatrix4fv(glimg.voxValXformPos,     1, False, vvx)

    # Enable storage of tightly packed data
    # of any size, for our 3D image texture 
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1) 
    
    # Set up the colour texture
    gl.glActiveTexture(gl.GL_TEXTURE0) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)
    gl.glUniform1i(glimg.colourTexturePos, 0) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_3D, glimg.imageTexture)
    gl.glUniform1i(glimg.imageTexturePos, 1)

    # world x/y coordinates
    glimg.worldCoords.bind()
    gl.glVertexAttribPointer(
        glimg.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(glimg.worldCoordPos)

    # Draw all of the triangles!
    glimg.indices.bind()
    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      glimg.nVertices,
                      gl.GL_UNSIGNED_INT,
                      None)

    gl.glDisableVertexAttribArray(glimg.worldCoordPos)

    glimg.indices.unbind()
    glimg.worldCoords.unbind()

    gl.glUseProgram(0)
