#!/usr/bin/env python
#
# gltensorline.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL.GL     as gl
import numpy         as np
import scipy.ndimage as ndi

import globject

class GLTensorLine(object):

    def __init__(self, image, display):

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ tensor angles')

        self.image   = image
        self.display = display
        self._ready  = False

        
    def ready(self):
        return self._ready


    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax
        
        worldCoords, xpixdim, ypixdim = globject.calculateSamplePoints(
            self.image,
            self.display,
            self.xax,
            self.yax)

        self.worldCoords = worldCoords
        self.xpixdim     = xpixdim
        self.ypixdim     = ypixdim
        
        
    def init(self, xax, yax):
        self.setAxes(xax, yax)
        self._ready = True

        
    def destroy(self):
        pass

        
    def draw(self, zpos, xform=None):

        xax         = self.xax
        yax         = self.yax
        zax         = self.zax
        image       = self.image
        display     = self.display
        worldCoords = self.worldCoords

        if not display.enabled: return

        worldCoords[:, zax] = zpos

        voxCoords  = image.worldToVox(worldCoords).transpose()
        imageData  = image.data
        nVoxels    = worldCoords.shape[0]

        # Interpolate image data at floating
        # point voxel coordinates
        xvals = ndi.map_coordinates(imageData[:, :, :, 0],
                                    voxCoords,
                                    order=0,
                                    prefilter=False)
        yvals = ndi.map_coordinates(imageData[:, :, :, 1],
                                    voxCoords,
                                    order=0,
                                    prefilter=False)
        zvals = ndi.map_coordinates(imageData[:, :, :, 2],
                                    voxCoords,
                                    order=0,
                                    prefilter=False)

        # make a list of vectors
        vecs = np.array([xvals, yvals, zvals]).transpose()

        # make a bunch of lines, centered at
        # the origin and scaled appropriately
        vecs[:, xax] *= 0.5 * self.xpixdim
        vecs[:, yax] *= 0.5 * self.ypixdim
        vecs = np.hstack((-vecs, vecs)).reshape((2 * nVoxels, 3))
        
        worldCoords = worldCoords.repeat(2, 0) + vecs
        worldCoords = np.array(worldCoords, dtype=np.float32).ravel('C')

        if xform is not None: 
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(xform)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        gl.glColor3f(1, 0, 0)
        gl.glLineWidth(2)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)
        gl.glDrawArrays(gl.GL_LINES, 0, 2 * nVoxels)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPopMatrix()
