#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides functions which are used by the
:class:`~fsl.fslview.gl.glimage.GLImage` class to render 3D images in an
OpenGL 1.4 compatible manner. (i.e. using immediate mode rendering).

The functions in this module make use of functions in the
:mod:`fsl.fslview.gl.glimage` module to actually generate the vertex and
texture information necessary to render an image.

This module provides the following functions:

 - :func:`init`: Does nothing - no initialisation is necessary for OpenGL 1.4.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`genImageData`: Prepares and returns the 3D image data to be
   rendered.

 - :func:`genColourMap`: Configures a `matplotlib.colors.Colormap` instance
   for generating voxel colours from image data.

 - :func:`draw`: Draws the image using OpenGL.

 - :func:`destroy`: Deletes the texture handle for the colour map texture.
"""

import logging
log = logging.getLogger(__name__)

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform as transform


_glimage_vertex_program = """!!ARBvp1.0

# Transform the vertex coordinates from the display
# coordinate system to the screen coordinate system
TEMP vertexPos;
DP4 vertexPos.x, state.matrix.mvp.row[0], vertex.position;
DP4 vertexPos.y, state.matrix.mvp.row[1], vertex.position;
DP4 vertexPos.z, state.matrix.mvp.row[2], vertex.position;
DP4 vertexPos.w, state.matrix.mvp.row[3], vertex.position;

MOV result.position, vertexPos;

# Set the vertex texture coordinate
# to the vertex position
MOV result.texcoord[0], vertex.position;

END
"""


_glimage_fragment_program = """!!ARBfp1.0
TEMP dispTexCoord;
TEMP voxTexCoord;
TEMP voxValue;

# This matrix scales the voxel value to
# lie in a range which is appropriate to
# the current display range 
PARAM voxValXform[4] = { state.matrix.texture[1] };

# This matrix transforms coordinates
# from the display coordinate system
# to image voxel coordinates
PARAM dispToVoxMat[4] = { state.matrix.texture[0] };

# retrieve the 3D texture coordinates
# (which are in terms of the display
# coordinate system)
MOV dispTexCoord, fragment.texcoord[0];

# Transform said coordinates
# into voxel coordinates
DP4 voxTexCoord.x, dispToVoxMat[0], dispTexCoord;
DP4 voxTexCoord.y, dispToVoxMat[1], dispTexCoord;
DP4 voxTexCoord.z, dispToVoxMat[2], dispTexCoord;

# look up image voxel value from 3D image texture
TEX voxValue, voxTexCoord, texture[0], 3D;

# Scale voxel value according
# to the current display range
MUL voxValue, voxValue, voxValXform[0].x;
ADD voxValue, voxValue, voxValXform[0].w;

# look up the appropriate colour in the 1D colour map
# texture, and apply it to the fragment output colour
TEX result.color, voxValue.x, texture[1], 1D;
END
"""


def init(glimg, xax, yax):
    """No initialisation is necessary for OpenGL 1.4."""

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    glimg.fragmentProgram = arbfp.glGenProgramsARB(1)
    glimg.vertexProgram   = arbvp.glGenProgramsARB(1) 

    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glimg.fragmentProgram)

    arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                             arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                             len(_glimage_fragment_program),
                             _glimage_fragment_program)

    if (gl.glGetError() == gl.GL_INVALID_OPERATION):

        position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling fragment program '
                           '({}): {}'.format(position, message))


    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glimg.vertexProgram)

    arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                             arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                             len(_glimage_vertex_program),
                             _glimage_vertex_program)

    if (gl.glGetError() == gl.GL_INVALID_OPERATION):

        position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling vertex program '
                           '({}): {}'.format(position, message)) 
                  
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    
def destroy(glimg):
    """"""
    arbfp.glDeleteProgramsARB(glimg.fragmentProgram)
    arbvp.glDeleteProgramsARB(glimg.vertexProgram)

    
def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords, indices = glimg.genVertexData()

    return worldCoords, texCoords, indices, indices.shape[0]


def draw(glimg, zpos, xform=None):
    """Draws a slice of the image at the given Z location using immediate
    mode rendering.
    """

    display = glimg.display
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords  = glimg.worldCoords
    indices      = glimg.indices
    worldCoords[:, glimg.zax] = zpos

    # enable the vertex and fragment programs
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glimg.fragmentProgram)
    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glimg.vertexProgram)

    # Set up the image data texture 
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, glimg.imageTexture)

    # Set up the colour map texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)

    # Configure the texture coordinate
    # transformation for the colour map
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPushMatrix()
    
    cmapXForm = transform.concat(glimg.voxValXform, glimg.colourMapXform)
    gl.glLoadMatrixf(cmapXForm)
    
    # And the image data transformation
    # for the image texture
    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = 1.0 / glimg.image.shape[0]
    mat[1, 1] = 1.0 / glimg.image.shape[1]
    mat[2, 2] = 1.0 / glimg.image.shape[2]
    mat = transform.concat(display.displayToVoxMat, mat)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPushMatrix()
    gl.glLoadMatrixf(mat)
    
    worldCoords = worldCoords.ravel('C')

    if xform is not None: 
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPopMatrix() 

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
