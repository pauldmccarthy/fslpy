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

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform    as transform
import fsl.fslview.gl.shaders as shaders


log = logging.getLogger(__name__)


def init(self):
    """Compiles the vertex and fragment programs used for rendering."""

    vertShaderSrc = shaders.getVertexShader(  self)
    fragShaderSrc = shaders.getFragmentShader(self) 

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)

    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram

    
def destroy(self):
    """Deletes handles to the vertex/fragment programs."""

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))

    
def genVertexData(self):
    """Generates vertex coordinates required to render the image. See
    :func:`fsl.fslview.gl.glvolume.genVertexData`.
    """
    
    worldCoords, indices = self.genVertexData()
    return worldCoords, indices, len(indices)


def preDraw(self):
    """Prepares to draw a slice from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    # enable drawing from a vertex array
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    # enable the vertex and fragment programs
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    # The vertex program needs to be
    # able to transform from display
    # coordinates to voxel coordinates
    shaders.setVertexProgramMatrix(
        0, self.display.getTransform('display', 'voxel').T)

    # The voxValXform transformation turns
    # an image texture value into a raw
    # voxel value. The colourMapXform
    # transformation turns a raw voxel value
    # into a value between 0 and 1, suitable
    # for looking up an appropriate colour
    # in the 1D colour map texture
    cmapXForm = transform.concat(self.imageTexture.voxValXform,
                                 self.colourMapXform)
    
    shaders.setFragmentProgramMatrix(0, cmapXForm.T)

    # The fragment program needs to know
    # the image shape, and its inverse,
    # because there's no division operation,
    # and the RCP operation only works on
    # scalars
    
    # We also need to pass the global
    # brightness/contrast/alpha values to
    # the fragment program 
    shape    = list(self.image.shape)
    invshape = [1.0 / s for s in shape]
    bca      = [self.display.brightness / 100.0, 
                self.display.contrast   / 100.0,
                self.display.alpha      / 100.0]    
    shaders.setFragmentProgramVector(4, shape    + [0])
    shaders.setFragmentProgramVector(5, invshape + [0])
    shaders.setFragmentProgramVector(6, bca      + [0])


def draw(self, zpos, xform=None):
    """Draws a slice of the image at the given Z location. """

    worldCoords  = self.worldCoords
    indices      = self.indices
    worldCoords[:, self.zax] = zpos

    # Apply the custom xform if provided.
    if xform is None:
        xform = np.eye(4)

    shaders.setVertexProgramMatrix(4, xform.T)

    worldCoords = worldCoords.ravel('C')

    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, worldCoords)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)

    
def drawAll(self, zposs, xforms):
    """Draws mutltiple slices of the given image at the given Z position,
    applying the corresponding transformation to each of the slices.
    """

    # Don't use a custom world-to-world
    # transformation matrix.
    shaders.setVertexProgramMatrix(4, np.eye(4))
    
    # Instead, tell the vertex
    # program to use texture coordinates
    shaders.setFragmentProgramVector(7, -np.ones(4))
    
    worldCoords  = np.array(self.worldCoords)
    indices      = np.array(self.indices)
    nverts       = worldCoords.shape[0]
    nidxs        = indices.shape[0]

    # The world coordinates are ordered to 
    # be rendered as a triangle strip, but
    # we want to render as quads. So we
    # need to re-order them
    worldCoords[[2, 3], :] = worldCoords[[3, 2], :]

    # Combine all of the world/texture
    # coordinates and indices into single
    # arrays, so we can send them all
    # with a single draw command
    allTexCoords   = np.zeros((nverts * len(zposs), 3), dtype=np.float32)
    allWorldCoords = np.zeros((nverts * len(zposs), 3), dtype=np.float32)
    allIndices     = np.zeros( nidxs  * len(zposs),     dtype=np.uint32)
    
    for i, (zpos, xform) in enumerate(zip(zposs, xforms)):

        worldCoords[:, self.zax] = zpos

        vStart = i * nverts
        vEnd   = vStart + nverts

        iStart = i * nidxs
        iEnd   = iStart + nidxs

        allIndices[    iStart:iEnd]    = indices + i * nverts
        allTexCoords[  vStart:vEnd, :] = worldCoords
        allWorldCoords[vStart:vEnd, :] = transform.transform(worldCoords,
                                                             xform)
    allWorldCoords = allWorldCoords.ravel('C')
    allTexCoords   = allTexCoords  .ravel('C')

    # Draw all of the slices with 
    # these four function calls.
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, allTexCoords)
    gl.glVertexPointer(  3, gl.GL_FLOAT, 0, allWorldCoords)

    gl.glDrawElements(gl.GL_QUADS,
                      len(allIndices),
                      gl.GL_UNSIGNED_INT,
                      allIndices)


def postDraw(self):
    """Cleans up the GL state after drawing from the given
    :class:`~fsl.fslview.gl.glvolume.GLVolume` instance.
    """

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
