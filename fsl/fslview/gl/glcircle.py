#!/usr/bin/env python
#
# glcircle.py - A dummy test case for different image type support. Render a
# 2D slice, drawing voxels as circles.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy                  as np

import fsl.utils.transform    as transform
import fsl.fslview.gl         as fslgl
import fsl.fslview.gl.glimage as glimage

class GLCircle(glimage.GLImage):

    def __init__(self, image, display):
        glimage.GLImage.__init__(self, image, display)

    def genVertexData(self):
        return genVertexData(self.image, self.display, self.xax, self.yax)

    def draw(self, zpos, xform=None):
        fslgl.glcircle_funcs.draw(self, zpos, xform)
        

def genVertexData(image, display, xax, yax):

    zax           = 3 - xax - yax
    worldRes      = display.worldResolution
    voxelRes      = display.voxelResolution
    transformCode = display.transform
    transformMat  = display.voxToDisplayMat

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = transform.axisBounds(image.shape, transformMat, xax)
    ymin, ymax = transform.axisBounds(image.shape, transformMat, yax)

    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # we use the world display resolution
    if transformCode in ('affine'):

        xpixdim = worldRes
        ypixdim = worldRes

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    else:
        xpixdim = image.pixdim[xax] * voxelRes
        ypixdim = image.pixdim[yax] * voxelRes

    # Number of samples across each dimension,
    # given the current sample rate
    xNumSamples = np.floor((xmax - xmin) / xpixdim)
    yNumSamples = np.floor((ymax - ymin) / ypixdim)

    # the adjusted width/height of our sampled voxels
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/{}, num samples {})'.format(
                  image.name, transformCode, worldRes, voxelRes,
                  xNumSamples * yNumSamples))

    # The location of every displayed
    # voxel in real world space
    worldX = np.linspace(xmin + 0.5 * xpixdim,
                         xmax - 0.5 * xpixdim,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * ypixdim,
                         ymax - 0.5 * ypixdim,
                         yNumSamples)

    worldX, worldY = np.meshgrid(worldX, worldY)

    worldX  = worldX.flatten()
    worldY  = worldY.flatten()
    nVoxels = len(worldX)

    # The geometry of a single
    # voxel, rendered as 8 triangles
    voxelGeom = np.array([[ 0.0,    0.0],
                          [ 0.0,    0.5],
                          [ 0.353,  0.353],

                          [ 0.0,    0.0],
                          [ 0.353,  0.353],
                          [ 0.5,    0.0],

                          [ 0.0,    0.0],
                          [ 0.5,    0.0], 
                          [ 0.353, -0.353],

                          [ 0.0,    0.0],
                          [ 0.353, -0.353], 
                          [ 0.0,   -0.5],

                          [ 0.0,    0.0],
                          [ 0.0,   -0.5],
                          [-0.353, -0.353],

                          [ 0.0,    0.0],
                          [-0.353, -0.353],
                          [-0.5,    0.0],

                          [ 0.0,    0.0],
                          [-0.5,    0.0],
                          [-0.353,  0.353],
                          
                          [ 0.0,    0.0],
                          [-0.353,  0.353],
                          [ 0.0,    0.5]], dtype=np.float32)

    voxelGeom[:, 0] *= xpixdim
    voxelGeom[:, 1] *= ypixdim

    worldX = worldX.repeat(24) 
    worldY = worldY.repeat(24)
    worldZ = np.zeros(len(worldX))

    worldCoords = [None] * 3
    texCoords   = [None] * 3
    
    texCoords[xax] = worldX
    texCoords[yax] = worldY
    texCoords[zax] = worldZ
    
    worldX = worldX + np.tile(voxelGeom[:, 0], nVoxels)
    worldY = worldY + np.tile(voxelGeom[:, 1], nVoxels)

    worldCoords[xax] = worldX
    worldCoords[yax] = worldY
    worldCoords[zax] = worldZ

    worldCoords = np.array(worldCoords, dtype=np.float32).transpose()
    texCoords   = np.array(texCoords,   dtype=np.float32).transpose()

    return worldCoords, texCoords
