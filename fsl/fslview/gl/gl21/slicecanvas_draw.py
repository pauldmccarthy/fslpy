#!/usr/bin/env python
#
# slicecanvas_draw.py - Render slices from a collection of images in an OpenGL
#                       2.1 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Render slices from a collection of images in an OpenGL 2.1 compatible
 manner, using 3D textures, vertex buffer objects and custom vertex/fragment
 shader programs.

.. note:: This module is extremely tightly coupled to the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class, and to the
:class:`~fsl.fslview.gl.gl21.glimagedata.GLImageData` class.

This module provides two functions:

  - :func:`drawScene` draws slices from all of the images in an
    :class:`~fsl.data.image.ImageList` to a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` display.

  - :func:`drawSlice` (used by :func:`drawScene`) draws slices from one image
    to the :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`.

"""

import logging
log = logging.getLogger(__name__)

import os.path   as op
import numpy     as np
import OpenGL.GL as gl
import              wx


_vertex_shader_file   = op.join(op.dirname(__file__), 'vertex_shader.glsl')
"""Location of the GLSL vertex shader source code."""


_fragment_shader_file = op.join(op.dirname(__file__), 'fragment_shader.glsl')
"""Location of the GLSL fragment shader source code."""


def initGL(canvas):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and returns a reference to the resulting program. Raises
    an error if compilation/linking fails.

    I'm explicitly not using the PyOpenGL
    :func:`OpenGL.GL.shaders.compileProgram` function, because it attempts
    to validate the program after compilation, which fails due to texture
    data not being bound at the time of validation.
    """

    # initGL has already been called for this canvas
    if hasattr(canvas, 'shaders'): return

    with open(_vertex_shader_file,   'rt') as f: vertShaderSrc = f.read()
    with open(_fragment_shader_file, 'rt') as f: fragShaderSrc = f.read()

    canvas.glContext.SetCurrent(canvas)

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

    canvas.shaders = program

    canvas.glContext.SetCurrent(canvas)

    # Indices of all vertex/fragment shader parameters
    canvas.imageBufferPos   = gl.glGetUniformLocation(canvas.shaders,
                                                      'imageBuffer')
    canvas.worldToVoxMatPos = gl.glGetUniformLocation(canvas.shaders,
                                                      'worldToVoxMat')
    canvas.worldToWorldMatPos = gl.glGetUniformLocation(canvas.shaders,
                                                        'worldToWorldMat') 
    canvas.colourMapPos     = gl.glGetUniformLocation(canvas.shaders,
                                                      'colourMap')
    canvas.imageShapePos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'imageShape') 
    canvas.normFactorPos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'normFactor')
    canvas.normOffsetPos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'normOffset') 
    canvas.displayMinPos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'displayMin')
    canvas.displayMaxPos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'displayMax') 
    canvas.signedPos        = gl.glGetUniformLocation(canvas.shaders,
                                                      'signed')
    canvas.zCoordPos        = gl.glGetUniformLocation(canvas.shaders,
                                                      'zCoord')
    canvas.xaxPos           = gl.glGetUniformLocation(canvas.shaders,
                                                      'xax')
    canvas.yaxPos           = gl.glGetUniformLocation(canvas.shaders,
                                                      'yax')
    canvas.zaxPos           = gl.glGetUniformLocation(canvas.shaders,
                                                      'zax') 
    canvas.samplingRatePos  = gl.glGetUniformLocation(canvas.shaders,
                                                      'samplingRate')
    canvas.worldCoordPos    = gl.glGetAttribLocation( canvas.shaders,
                                                      'worldCoords')
    canvas.texCoordPos      = gl.glGetAttribLocation( canvas.shaders,
                                                      'texCoords') 

    
def drawSlice(canvas, image, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    If ``xform`` is not provided, the
    :class:`~fsl.data.image.Image` ``voxToWorldMat`` transformation
    matrix is used.

    :arg image:   The :class:`~fsl.data.image.Image` object to draw.
    
    :arg zpos:    World Z position of slice to be drawn.
    
    :arg xform:   A 4*4 transformation matrix to be applied to the slice
                  data (or ``None`` to use the
                  :class:`~fsl.data.image.Image` ``voxToWorldMat``
                  matrix).
    """

    # The GL data is stored as an attribute of the image,
    # and is created in the _imageListChanged method when
    # images are added to the image. If there's no data
    # here, ignore it; hopefully by the time _draw() is
    # called again, it will have been created.
    try:    glImageData = image.getAttribute(canvas.name)
    except: return
    
    imageDisplay = image.getAttribute('display')

    # Don't draw the slice if this
    # image display is disabled
    if not imageDisplay.enabled: return

    sliceno = image.worldToVox(zpos, glImageData.zax)

    # if the slice is out of range, don't draw it
    if sliceno < 0 or sliceno >= image.shape[glImageData.zax]:
        return

    # bind the current alpha value
    # and data range to the shader
    gl.glUniform1f( canvas.normFactorPos,    glImageData.normFactor)
    gl.glUniform1f( canvas.normOffsetPos,    glImageData.normOffset)
    gl.glUniform1f( canvas.displayMinPos,    imageDisplay.displayRange.xlo)
    gl.glUniform1f( canvas.displayMaxPos,    imageDisplay.displayRange.xhi)
    gl.glUniform1f( canvas.signedPos,        glImageData.signed)
    gl.glUniform1i( canvas.samplingRatePos,  imageDisplay.samplingRate)
    gl.glUniform1f( canvas.zCoordPos,        zpos)
    gl.glUniform3fv(canvas.imageShapePos, 1, np.array(glImageData.imageShape,
                                                      dtype=np.float32))
    gl.glUniform1i( canvas.xaxPos,           glImageData.xax)
    gl.glUniform1i( canvas.yaxPos,           glImageData.yax)
    gl.glUniform1i( canvas.zaxPos,           glImageData.zax)
    
    # bind the transformation matrices
    # to the shader variable
    if xform is None: xform = np.identity(4)
    
    w2w = np.array(xform,               dtype=np.float32).ravel('C')
    w2v = np.array(image.worldToVoxMat, dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(canvas.worldToVoxMatPos,   1, False, w2v)
    gl.glUniformMatrix4fv(canvas.worldToWorldMatPos, 1, False, w2w)

    # Set up the colour texture
    gl.glActiveTexture(gl.GL_TEXTURE0) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glImageData.colourBuffer)
    gl.glUniform1i(canvas.colourMapPos, 0) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_3D, glImageData.imageBuffer)
    gl.glUniform1i(canvas.imageBufferPos, 1)

    # world x/y coordinates
    glImageData.worldCoordBuffer.bind()
    gl.glVertexAttribPointer(
        canvas.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(canvas.worldCoordPos)

    # world x/y texture coordinates
    glImageData.texCoordBuffer.bind()
    gl.glVertexAttribPointer(
        canvas.texCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(canvas.texCoordPos) 

    # Draw all of the triangles!
    gl.glDrawArrays(
        gl.GL_QUADS, 0, glImageData.nVertices)

    gl.glDisableVertexAttribArray(canvas.worldCoordPos)
    gl.glDisableVertexAttribArray(canvas.texCoordPos)
    glImageData.worldCoordBuffer.unbind()
    glImageData.texCoordBuffer.unbind()


def drawScene(canvas):
    """Draws the currently selected slice (as specified by the ``z``
    value of the :attr:`pos` property) to the canvas."""

    # shaders have not been initialised.
    if not hasattr(canvas, 'shaders'):
        wx.CallAfter(lambda : initGL(canvas))
        return

    canvas.glContext.SetCurrent(canvas)
    canvas._setViewport()

    # clear the canvas
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # load the shaders
    gl.glUseProgram(canvas.shaders)

    # enable transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    # Enable storage of tightly packed data
    # of any size, for our 3D image texture 
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1) 

    # disable interpolation
    gl.glShadeModel(gl.GL_FLAT)

    for image in canvas.imageList:

        log.debug('Drawing {} slice for image {}'.format(
            canvas.zax, image.name))

        drawSlice(canvas, image, canvas.pos.z)

    gl.glUseProgram(0)

    if canvas.showCursor:

        # A vertical line at xpos, and a horizontal line at ypos
        xverts = np.zeros((2, 3))
        yverts = np.zeros((2, 3))

        xmin, xmax = canvas.imageList.bounds.getRange(canvas.xax)
        ymin, ymax = canvas.imageList.bounds.getRange(canvas.yax)

        # add a little padding to the lines if they are
        # on the boundary, so they don't get cropped
        xverts[:, canvas.xax] = canvas.pos.x
        yverts[:, canvas.yax] = canvas.pos.y 

        xverts[:, canvas.yax] = [ymin, ymax]
        xverts[:, canvas.zax] =  canvas.pos.z + 1
        yverts[:, canvas.xax] = [xmin, xmax]
        yverts[:, canvas.zax] =  canvas.pos.z + 1

        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex3f(*xverts[0])
        gl.glVertex3f(*xverts[1])
        gl.glVertex3f(*yverts[0])
        gl.glVertex3f(*yverts[1])
        gl.glEnd()

    canvas.SwapBuffers()
