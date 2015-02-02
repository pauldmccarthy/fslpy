#!/usr/bin/env python
#
# glvector_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy                          as np
import scipy.ndimage                  as ndi

import OpenGL.GL                      as gl
import OpenGL.raw.GL._types           as gltypes
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform     as transform
import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.gl.globject as globject


log = logging.getLogger(__name__)


def init(self):
  
    vertShaderSrc = shaders.getVertexShader('generic')
    fragShaderSrc = shaders.getFragmentShader(self)

    vertexProgram, fragmentProgram = shaders.compilePrograms(
        vertShaderSrc, fragShaderSrc)
    
    self.vertexProgram   = vertexProgram
    self.fragmentProgram = fragmentProgram


def destroy(self):

    arbvp.glDeleteProgramsARB(1, gltypes.GLuint(self.vertexProgram))
    arbfp.glDeleteProgramsARB(1, gltypes.GLuint(self.fragmentProgram))


def setAxes(self):
    mode = self.displayOpts.displayMode

    if   mode == 'rgb':  rgbModeSetAxes( self)
    elif mode == 'line': lineModeSetAxes(self)

    
def rgbModeSetAxes(self):
    worldCoords, idxs = globject.slice2D(self.image.shape,
                                         self.xax,
                                         self.yax,
                                         self.display.voxToDisplayMat)

    self.worldCoords = worldCoords
    self.indices     = idxs 

    
def lineModeSetAxes(self):
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

    # the fragment program needs to know the image
    # shape and its inverse, so it can scale voxel
    # coordinates to the range [0.0, 1.0], and so
    # it can clip fragments outside of the image
    # space
    shape    = list(self.image.shape)
    invshape = [1.0 / s for s in shape]
    shaders.setFragmentProgramVector(0, shape    + [0])
    shaders.setFragmentProgramVector(1, invshape + [0])

    if self.displayOpts.displayMode == 'line':
        shaders.setFragmentProgramMatrix(2, self.imageTexture.voxValXform.T)
    else:
        shaders.setFragmentProgramMatrix(2, np.eye(4))


def draw(self, zpos, xform=None):
    
    if self.displayOpts.displayMode == 'line':
        lineModeDraw(self, zpos, xform)
        
    elif self.displayOpts.displayMode == 'rgb':
        rgbModeDraw(self, zpos, xform)

        
def lineModeDraw(self, zpos, xform=None):
    """Calculates vector orientations for the specified Z-axis location, and
    renders them using immediate mode OpenGL.
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

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)
