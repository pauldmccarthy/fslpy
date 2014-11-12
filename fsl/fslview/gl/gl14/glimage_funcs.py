#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides functions which are used by the
:class:`~fsl.fslview.gl.glimage.GLImage` class to render 3D images in an
OpenGL 1.4 compatible manner.

This module depends upon two OpenGL ARB extensions, ARB_vertex_program and
ARB_fragment_program which, being ancient (2002) technology, should be
available on pretty much any graphics card in the wild today.

This module provides the following functions:

 - :func:`init`: Compiles the vertex/fragment programs used in rendering.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`draw`: Renders the current image slice.

 - :func:`destroy`: Deletes handles to the vertex/fragment programs
"""

import logging
log = logging.getLogger(__name__)

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
"""The vertex program does two things:

  - Transforms vertex coordinates from display space into screen space

  - Sets the vertex texture coordinate from its display coordinate
"""


_glimage_fragment_program = """!!ARBfp1.0
TEMP  dispTexCoord;
TEMP  voxTexCoord;
TEMP  normVoxTexCoord;
TEMP  voxValue;
TEMP  voxColour;
PARAM imageShape       = program.local[0];
PARAM imageShapeInv    = program.local[1];
PARAM imageTexShapeInv = program.local[2];

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

# Offset voxel coordinates by 0.5 
# so they are centred within a voxel
ADD voxTexCoord, voxTexCoord, { 0.5, 0.5, 0.5, 0.0 };

# Normalise voxel coordinates to 
# lie in the range (0, 1), so they 
# can be used for texture lookup
MUL normVoxTexCoord, voxTexCoord, imageTexShapeInv;
MUL normVoxTexCoord, voxTexCoord, imageShapeInv;

# look up image voxel value
# from 3D image texture
TEX voxValue, normVoxTexCoord, texture[0], 3D;

# Scale voxel value according
# to the current display range
MUL voxValue, voxValue, voxValXform[0].x;
ADD voxValue, voxValue, voxValXform[0].w;

# look up the appropriate colour
# in the 1D colour map texture
TEX voxColour, voxValue.x, texture[1], 1D;

# If any of the voxel coordinates are
# less than 0, clear the voxel colour
CMP voxColour.w, voxTexCoord.x, 0.0, voxColour.w;
CMP voxColour.w, voxTexCoord.y, 0.0, voxColour.w;
CMP voxColour.w, voxTexCoord.z, 0.0, voxColour.w;

# If any voxel coordinates are greater than
# the image shape, clear the voxel colour
SUB voxTexCoord, voxTexCoord, imageShape;
CMP voxColour.w, voxTexCoord.x, voxColour.w, 0.0;
CMP voxColour.w, voxTexCoord.y, voxColour.w, 0.0;
CMP voxColour.w, voxTexCoord.z, voxColour.w, 0.0;

# Colour the pixel!
MOV result.color, voxColour;

END
"""
"""
The fragment shader does the following:

 1. Retrieves the texture coordinates corresponding to the fragment

 2. Transforms those coordinates into voxel coordinates

 3. Uses those voxel coordinates to look up the corresponding voxel
    value in the 3D image texture.

 4. Uses that voxel value to look up the corresponding colour in the
    1D colour map texture.

 5. Sets the fragment colour.
"""


def init(glimg, xax, yax):
    """Compiles the vertex and fragment programs used for rendering."""

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    glimg.fragmentProgram = arbfp.glGenProgramsARB(1)
    glimg.vertexProgram   = arbvp.glGenProgramsARB(1) 

    # vertex program
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

    # fragment program
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

    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB) 

    
def destroy(glimg):
    """Deletes handles to the vertex/fragment programs."""
    arbvp.glDeleteProgramsARB(glimg.vertexProgram) 
    arbfp.glDeleteProgramsARB(glimg.fragmentProgram)

    
def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords, indices = glimg.genVertexData()

    return worldCoords, texCoords, indices, indices.shape[0]


def draw(glimg, zpos, xform=None):
    """Draws a slice of the image at the given Z location. """

    display = glimg.display
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords  = glimg.worldCoords
    indices      = glimg.indices
    worldCoords[:, glimg.zax] = zpos

    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glimg.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glimg.fragmentProgram) 

    # Set up the image data texture 
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, glimg.imageTexture)

    # Set up the colour map texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)

    # The fragment program needs to know
    # the image shape (and its inverse,
    # because there's no division operation,
    # and the RCP operation works on scalars)
    shape    = glimg.imageShape
    texShape = glimg.imageTextureShape
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
    arbfp.glProgramLocalParameter4fARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                                       2,
                                       1.0 / texShape[0],
                                       1.0 / texShape[1],
                                       1.0 / texShape[2],
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
    cmapXForm = transform.concat(glimg.voxValXform,
                                 glimg.colourMapXform)
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
