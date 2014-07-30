#!/usr/bin/env python
#
# slicecanvas_draw.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import os.path   as op
import numpy     as np
import OpenGL.GL as gl
import              wx

import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi


_vertex_shader_file   = op.join(op.dirname(__file__), 'vertex_shader.glsl')
"""Location of the GLSL vertex shader source code."""


_fragment_shader_file = op.join(op.dirname(__file__), 'fragment_shader.glsl')
"""Location of the GLSL fragment shader source code."""


def _initGL(canvas):
    """Compiles and links the OpenGL GLSL vertex and fragment shader
    programs, and returns a reference to the resulting program. Raises
    an error if compilation/linking fails.

    I'm explicitly not using the PyOpenGL
    :func:`OpenGL.GL.shaders.compileProgram` function, because it attempts
    to validate the program after compilation, which fails due to texture
    data not being bound at the time of validation.
    """

    # _initGL has already been called for this canvas
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
    canvas.alphaPos         = gl.glGetUniformLocation(canvas.shaders, 'alpha')
    canvas.imageBufferPos   = gl.glGetUniformLocation(canvas.shaders,
                                                      'imageBuffer')
    canvas.voxToWorldMatPos = gl.glGetUniformLocation(canvas.shaders,
                                                      'voxToWorldMat')
    canvas.colourMapPos     = gl.glGetUniformLocation(canvas.shaders,
                                                      'colourMap')
    canvas.imageShapePos    = gl.glGetUniformLocation(canvas.shaders,
                                                      'imageShape') 
    canvas.subTexShapePos   = gl.glGetUniformLocation(canvas.shaders,
                                                      'subTexShape')
    canvas.subTexPadPos     = gl.glGetUniformLocation(canvas.shaders,
                                                      'subTexPad')
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
    canvas.fullTexShapePos  = gl.glGetUniformLocation(canvas.shaders,
                                                      'fullTexShape')
    canvas.inVertexPos      = gl.glGetAttribLocation( canvas.shaders,
                                                      'inVertex')
    canvas.voxXPos          = gl.glGetAttribLocation( canvas.shaders, 'voxX')
    canvas.voxYPos          = gl.glGetAttribLocation( canvas.shaders, 'voxY')
    canvas.voxZPos          = gl.glGetAttribLocation( canvas.shaders, 'voxZ')

        
def _drawSlice(canvas, image, sliceno, xform=None):
    """Draws the specified slice from the specified image on the canvas.

    If ``xform`` is not provided, the
    :class:`~fsl.data.image.Image` ``voxToWorldMat`` transformation
    matrix is used.

    :arg image:   The :class:`~fsl.data.image.Image` object to draw.
    
    :arg sliceno: Voxel index of the slice to be drawn.
    
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

    # The number of voxels to be displayed along
    # each dimension is not necessarily equal to
    # the actual image shape, as the image may
    # be sampled at a lower resolution. The
    # GLImageData object keeps track of the
    # current image display resolution.
    xdim = glImageData.xdim
    ydim = glImageData.ydim
    zdim = glImageData.zdim
    
    # Don't draw the slice if this
    # image display is disabled
    if not imageDisplay.enabled: return

    # if the slice is out of range, don't draw it
    if sliceno < 0 or sliceno >= zdim: return

    # bind the current alpha value
    # and data range to the shader
    gl.glUniform1f(canvas.alphaPos,      imageDisplay.alpha)
    gl.glUniform1f(canvas.normFactorPos, glImageData.normFactor)
    gl.glUniform1f(canvas.normOffsetPos, glImageData.normOffset)
    gl.glUniform1f(canvas.displayMinPos, imageDisplay.displayRange.xlo)
    gl.glUniform1f(canvas.displayMaxPos, imageDisplay.displayRange.xhi)
    gl.glUniform1f(canvas.signedPos,     glImageData.signed)

    # and the image/texture shape buffers
    gl.glUniform3fv(canvas.fullTexShapePos, 1, glImageData.fullTexShape)
    gl.glUniform3fv(canvas.subTexShapePos,  1, glImageData.subTexShape)
    gl.glUniform3fv(canvas.subTexPadPos,    1, glImageData.subTexPad)
    gl.glUniform3fv(canvas.imageShapePos,   1, image.shape[:3])
    
    # bind the transformation matrix
    # to the shader variable
    if xform is None:
        xform = np.array(image.voxToWorldMat, dtype=np.float32)
    xform = xform.ravel('C')
    gl.glUniformMatrix4fv(canvas.voxToWorldMatPos, 1, False, xform)

    # Set up the colour texture
    gl.glActiveTexture(gl.GL_TEXTURE0) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glImageData.colourBuffer)
    gl.glUniform1i(canvas.colourMapPos, 0) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_3D, glImageData.imageBuffer)
    gl.glUniform1i(canvas.imageBufferPos, 1)
    
    # voxel x/y/z coordinates
    voxOffs  = [0, 0, 0]
    voxSteps = [1, 1, 1]

    voxOffs[ canvas.zax] = sliceno
    voxSteps[canvas.yax] = xdim
    voxSteps[canvas.zax] = xdim * ydim
    for buf, pos, step, off in zip(
            (glImageData.voxXBuffer,
             glImageData.voxYBuffer,
             glImageData.voxZBuffer),
            (canvas.voxXPos,
             canvas.voxYPos,
             canvas.voxZPos),
            voxSteps,
            voxOffs):

        if off == 0: off = None
        else:        off = buf + (off * 2)
        
        buf.bind()
        gl.glVertexAttribPointer(
            pos,
            1,
            gl.GL_UNSIGNED_SHORT,
            gl.GL_FALSE,
            0,
            off)
        gl.glEnableVertexAttribArray(pos)
        arbia.glVertexAttribDivisorARB(pos, step)

    # The geometry buffer, which defines the geometry of a
    # single vertex (4 vertices, drawn as a triangle strip)
    glImageData.geomBuffer.bind()
    gl.glVertexAttribPointer(
        canvas.inVertexPos,
        3,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(canvas.inVertexPos)
    arbia.glVertexAttribDivisorARB(canvas.inVertexPos, 0)

    # Draw all of the triangles!
    arbdi.glDrawArraysInstancedARB(
        gl.GL_TRIANGLE_STRIP, 0, 4, xdim * ydim)

    gl.glDisableVertexAttribArray(canvas.inVertexPos)
    gl.glDisableVertexAttribArray(canvas.voxXPos)
    gl.glDisableVertexAttribArray(canvas.voxYPos)
    gl.glDisableVertexAttribArray(canvas.voxZPos)


def draw(canvas):
    """Draws the currently selected slice (as specified by the ``z``
    value of the :attr:`pos` property) to the canvas."""

    # shaders have not been initialised.
    if not hasattr(canvas, 'shaders'):
        wx.CallAfter(lambda : _initGL(canvas))
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

    # disable interpolation
    gl.glShadeModel(gl.GL_FLAT)

    for image in canvas.imageList:

        log.debug('Drawing {} slice for image {}'.format(
            canvas.zax, image.name))

        zi = int(image.worldToVox(canvas.pos.z, canvas.zax))
        _drawSlice(canvas, image, zi)

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
