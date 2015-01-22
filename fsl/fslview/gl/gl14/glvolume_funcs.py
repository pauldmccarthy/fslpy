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

 - :func:`draw`: Renders the current image slice.

 - :func:`destroy`: Deletes handles to the vertex/fragment programs

This PDF is quite useful:
 - http://www.renderguild.com/gpuguide.pdf
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform as transform
import fsl.fslview.gl      as fslgl


_glvolume_vertex_program = """!!ARBvp1.0

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


_glvolume_fragment_program = """!!ARBfp1.0
TEMP  dispTexCoord;
TEMP  voxTexCoord;
TEMP  normVoxTexCoord;
TEMP  voxValue;
TEMP  voxColour;
PARAM imageShape    = program.local[0];
PARAM imageShapeInv = program.local[1];

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


def init(glvol, xax, yax):
    """Compiles the vertex and fragment programs used for rendering."""

    vertexProgram, fragmentProgram = fslgl.compilePrograms(
        _glvolume_vertex_program, _glvolume_fragment_program)

    glvol.vertexProgram   = vertexProgram
    glvol.fragmentProgram = fragmentProgram

    
def destroy(glvol):
    """Deletes handles to the vertex/fragment programs."""
    arbvp.glDeleteProgramsARB(glvol.vertexProgram) 
    arbfp.glDeleteProgramsARB(glvol.fragmentProgram)

    
def genVertexData(glvol):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glvolume.genVertexData`.
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
    gl.glBindTexture(gl.GL_TEXTURE_3D, glvol.imageTexture)

    # Set up the colour map texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glvol.colourTexture)

    # The fragment program needs to know
    # the image shape (and its inverse,
    # because there's no division operation,
    # and the RCP operation works on scalars)
    shape = glvol.imageShape
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
    cmapXForm = transform.concat(glvol.voxValXform,
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
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPopMatrix()

    gl.glDisable(gl.GL_TEXTURE_1D)
    gl.glDisable(gl.GL_TEXTURE_3D) 
