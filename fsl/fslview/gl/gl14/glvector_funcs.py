#!/usr/bin/env python
#
# glvector_funcs.py - Logic for rendering GLVector instances in an OpenGL 1.4
#                     compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions used by the
:class:`~fsl.fslview.gl.glvector.GLVector` class, for rendering
:class:`~fsl.data.image.Image` instances as vectors in an OpenGL 1.4
compatible manner.

See the ``GLVector`` documentation for more details.
"""

import numpy                          as np
import scipy.ndimage                  as ndi

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform     as transform
import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject


def init(self):
    """Compiles the vertex and fragment programs used for rendering. The
    same programs are used for both ``line`` and ``rgb`` mode.
    """
  
    vertShaderSrc = shaders.getVertexShader('generic')
    fragShaderSrc = shaders.getFragmentShader(self)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram


def destroy(self):
    """Deletes the vertex/fragment programs. """

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


def setAxes(self):
    """Calls one of :func:`rgbModeSetAxes` or :func:`lineModeSetAxes`,
    depending upon the current display mode.
    """
    mode = self.displayOpts.displayMode

    if   mode == 'rgb':  rgbModeSetAxes( self)
    elif mode == 'line': lineModeSetAxes(self)

    
def rgbModeSetAxes(self):
    """Creates four vertices which represent a slice through the image
    texture, oriented according to the plane defined by
    ``self.xax`` and  ``self.yax``.

    See :func:`~fsl.fslview.globject.slice2D` for more details.
    """
    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs 

    
def lineModeSetAxes(self):
    """Creates an array of points forming a rectangular grid, one point
    in the centre of each voxel, oriented according to the plane defined by
    ``self.xax`` and  ``self.yax``. These points are used by
    :func:`lineModeDraw` to generate lines representing vectors at every
    voxel.

    See :func:`~fsl.fslview.globject.calculateSamplePoints` for more details.
    """
    worldCoords, xpixdim, ypixdim, lenx, leny = \
        globject.calculateSamplePoints(
            self.image,
            self.display,
            self.xax,
            self.yax)

    self.worldCoords = worldCoords
    self.xpixdim     = xpixdim
    self.ypixdim     = ypixdim


def preDraw(self):
    """Loads the vertex/fragment programs, and sets some program parameters.
    """

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)

    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           self.vertexProgram)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           self.fragmentProgram)

    # the vertex program needs to be able to
    # transform from display space to voxel
    # space
    shaders.setVertexProgramMatrix(0, self.display.displayToVoxMat.T)

    if self.displayOpts.displayMode == 'line':
        shaders.setFragmentProgramMatrix(0, self.imageTexture.voxValXform.T)
    else:
        shaders.setFragmentProgramMatrix(0, np.eye(4))
    
    # The fragment program needs to know the image
    # shape and its inverse, so it can scale voxel
    # coordinates to the range [0.0, 1.0], and so
    # it can clip fragments outside of the image
    # space. It also needs to know the global
    # brightness, contrast, and alpha values.
    shape    = list(self.image.shape)
    invshape = [1.0 / s for s in shape]
    bca      = [self.display.brightness       / 100.0,
                self.display.contrast         / 100.0,
                self.display.alpha            / 100.0]
    modThres = [self.displayOpts.modThreshold / 100.0]
    
    shaders.setFragmentProgramVector(4, shape    + [0])
    shaders.setFragmentProgramVector(5, invshape + [0])
    shaders.setFragmentProgramVector(6, modThres + [0, 0, 0])
    shaders.setFragmentProgramVector(7, bca      + [0])


def draw(self, zpos, xform=None):
    """Calls one of :func:`lineModeDraw` or :func:`rgbModeDraw`, depending
    upon the current display mode.
    """
    
    if self.displayOpts.displayMode == 'line':
        lineModeDraw(self, zpos, xform)
        
    elif self.displayOpts.displayMode == 'rgb':
        rgbModeDraw(self, zpos, xform)

        
def lineModeDraw(self, zpos, xform=None):
    """Creates a line, representing a vector, at each voxel at the specified
    ``zpos``, and renders them.
    """

    image       = self.image
    display     = self.display
    worldCoords = self.worldCoords

    if not display.enabled:
        return

    worldCoords[:, self.zax] = zpos

    # Transform the world coordinates to
    # floating point voxel coordinates
    dToVMat = display.displayToVoxMat
    vToDMat = display.voxToDisplayMat
    
    voxCoords  = transform.transform(worldCoords, dToVMat).transpose()
    imageData  = image.data
    nVoxels    = worldCoords.shape[0]

    # Get the image data at those 
    # voxel coordinates, using
    # nearest neighbour interpolation
    xvals = ndi.map_coordinates(imageData[:, :, :, 0],
                                voxCoords,
                                order=0,
                                mode='nearest',
                                prefilter=False)
    yvals = ndi.map_coordinates(imageData[:, :, :, 1],
                                voxCoords,
                                order=0,
                                mode='nearest',
                                prefilter=False)
    zvals = ndi.map_coordinates(imageData[:, :, :, 2],
                                voxCoords,
                                order=0,
                                mode='nearest',
                                prefilter=False)

    # make a N*3 list of vectors
    vecs = np.array([xvals, yvals, zvals]).transpose()

    # make a bunch of vertices which represent lines 
    # (two vertices per line), centered at the origin
    # and scaled appropriately
    vecs *= 0.5
    vecs  = np.hstack((-vecs, vecs)).reshape((2 * nVoxels, 3))

    # Scale the vector by the minimum voxel length, 
    # so it is a unit vector within real world space
    vecs /= (image.pixdim[:3] / min(image.pixdim[:3]))

    # Offset each of those vertices by
    # their original voxel coordinates
    vecs += voxCoords.T.repeat(2, 0)

    # Translate those line vertices
    # into display coordinates
    worldCoords = transform.transform(vecs, vToDMat)
    worldCoords[:, self.zax] = zpos
    worldCoords = np.array(worldCoords, dtype=np.float32).ravel('C')

    # Draw all the lines!
    if xform is None: 
        xform = np.eye(4)

    shaders.setVertexProgramMatrix(4, xform.T) 

    gl.glLineWidth(2)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)
    gl.glDrawArrays(gl.GL_LINES, 0, 2 * nVoxels) 

    
def rgbModeDraw(self, zpos, xform=None):
    """Renders a rectangular slice through the vector image texture at the
    specified ``zpos``.
    """

    worldCoords  = self.worldCoords
    indices      = self.indices
    worldCoords[:, self.zax] = zpos

    worldCoords = worldCoords.ravel('C')

    if xform is None:
        xform = np.eye(4)

    shaders.setVertexProgramMatrix(4, xform.T)

    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices) 

    
def postDraw(self):
    """Disables the vertex/fragment programs used for drawing."""

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
