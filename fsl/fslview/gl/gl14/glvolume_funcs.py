#!/usr/bin/env python
#
# glvolume_funcs.py - Functions used by the fsl.fslview.gl.glvolume.GLVolume
#                     class to render 3D images in an OpenGL 1.4 compatible
#                     manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides functions which are used by the
:class:`~fsl.fslview.gl.glvolume.GLVolume` class to render 3D images in an
OpenGL 1.4 compatible manner.

This module depends upon two OpenGL ARB extensions, ARB_vertex_program and
ARB_fragment_program which, being ancient (2002) technology, should be
available on pretty much any graphics card in the wild today.

This module provides the following functions:

 - :func:`init`: Compiles the vertex/fragment programs used in rendering.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`preDraw: Prepares the GL state for drawing.

 - :func:`draw`: Renders the current image slice.

 - :func:`postDraw: Resets the GL state after drawing.

 - :func:`destroy`: Deletes handles to the vertex/fragment programs

This PDF is quite useful:
 - http://www.renderguild.com/gpuguide.pdf
"""

import logging

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform    as transform
import fsl.fslview.gl.shaders as shaders


log = logging.getLogger(__name__)


def init(glvol):
    """Compiles the vertex and fragment programs used for rendering."""

    vertShaderSrc = shaders.getVertexShader('generic')
    fragShaderSrc = shaders.getFragmentShader(glvol) 

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    glvol.vertexProgram   = vertexProgram
    glvol.fragmentProgram = fragmentProgram

    
def destroy(glvol):
    """Deletes handles to the vertex/fragment programs."""

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(glvol.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(glvol.fragmentProgram))

    
def genVertexData(glvol):
    """Generates vertex coordinates required to render the image. See
    :func:`fsl.fslview.gl.glvolume.genVertexData`.
    """
    
    worldCoords, indices = glvol.genVertexData()
    return worldCoords, indices, len(indices)


def preDraw(glvol):
    """Prepares to draw a slice from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    display = glvol.display

    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    gl.glEnable(gl.GL_TEXTURE_1D)
    gl.glEnable(gl.GL_TEXTURE_3D)
    
    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glvol.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glvol.fragmentProgram) 

    # Set up the image data texture 
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, glvol.imageTexture.texture)

    # Set up the colour map texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glvol.colourTexture)

    # The fragment program needs to know
    # the image shape (and its inverse,
    # because there's no division operation,
    # and the RCP operation works on scalars)
    shape = glvol.image.shape
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

    # Configure the texture coordinate
    # transformation for the colour map
    # 
    # The voxValXform transformation turns
    # an image texture value into a raw
    # voxel value. The colourMapXform
    # transformation turns a raw voxel value
    # into a value between 0 and 1, suitable
    # for looking up an appropriate colour
    # in the 1D colour map texture
    cmapXForm = transform.concat(glvol.imageTexture.voxValXform,
                                 glvol.colourMapXform)
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPushMatrix()
    gl.glLoadMatrixf(cmapXForm)
    
    # And configure the image data
    # transformation for the image texture.
    # The image texture coordinates need
    # to be transformed from display space
    # to voxel coordinates
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPushMatrix()
    gl.glLoadMatrixf(display.displayToVoxMat)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    # Save a copy of the current MV matrix.
    # We do this to minimise the number of GL
    # calls in the draw function (see inline
    # comments in draw)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    glvol.mvmat = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)


def draw(glvol, zpos, xform=None):
    """Draws a slice of the image at the given Z location. """

    display = glvol.display
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords  = glvol.worldCoords
    indices      = glvol.indices
    worldCoords[:, glvol.zax] = zpos

    # Apply the custom xform if provided.
    # I'm doing this on CPU to minimise
    # the number of GL calls (which, when
    # running over a network, is the major
    # performance bottleneck). Doing this
    # on the GPU would require three calls:
    # 
    #   gl.glPushMatrix
    #   gl.glMultiMatrixf
    #   ...
    #   gl.glPopMatrix
    #
    # as opposed to the single call to
    # glLoadMatrixf required here
    if xform is not None:
        xform = transform.concat(xform, glvol.mvmat)
        gl.glLoadMatrixf(xform)

    worldCoords = worldCoords.ravel('C')

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)


def postDraw(glvol):
    """Cleans up the GL state after drawing from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    display = glvol.display
    if not display.enabled: return

    gl.glPopMatrix()

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    gl.glPopMatrix()

    gl.glDisable(gl.GL_TEXTURE_1D)
    gl.glDisable(gl.GL_TEXTURE_3D) 
