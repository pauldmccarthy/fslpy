#!/usr/bin/env python
#
# gltensor_line_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL     as gl

import numpy         as np
import scipy.ndimage as ndi

import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform


log = logging.getLogger(__name__)


#######################
# methods for Line Mode
#######################


def init(self):
    """Adds a bunch of listeners to the
    :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
    how the given image is to be displayed.
        """

    display = self.display
    
    def coordUpdate(*a):
        self.setAxes(self.xax, self.yax)

    display.addListener('transform',     self.name, coordUpdate)
    display.addListener('interpolation', self.name, coordUpdate)
    display.addListener('resolution',    self.name, coordUpdate)

    
def destroy(self):
    
    self.display.removeListener('transform',     self.name)
    self.display.removeListener('interpolation', self.name)
    self.display.removeListener('resolution',    self.name)
    
    del self.worldCoords
    del self.xpixdim
    del self.ypixdim


def setAxes(self):
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

    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    self.mvmat = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

    
def draw(self, zpos, xform=None):
    """Calculates tensor orientations for the specified Z-axis location, and
    renders them using immediate mode OpenGL.
    """

    xax         = self.xax
    yax         = self.yax
    zax         = self.zax
    image       = self.image
    display     = self.display
    opts        = self.displayOpts
    worldCoords = self.worldCoords

    if not display.enabled: return

    worldCoords[:, zax] = zpos

    # Transform the world coordinates to
    # floating point voxel coordinates
    dToVMat = display.displayToVoxMat
    
    voxCoords  = transform.transform(worldCoords, dToVMat).transpose()
    imageData  = image.data
    nVoxels    = worldCoords.shape[0]

    if   display.interpolation == 'spline': order = 3
    elif display.interpolation == 'linear': order = 1
    else:                                   order = 0

    # Get the image data at those (floating point)
    # voxel coordinates, interpolating if it is enabled
    xvals = ndi.map_coordinates(imageData[:, :, :, 0],
                                voxCoords,
                                order=order,
                                prefilter=False)
    yvals = ndi.map_coordinates(imageData[:, :, :, 1],
                                voxCoords,
                                order=order,
                                prefilter=False)
    zvals = ndi.map_coordinates(imageData[:, :, :, 2],
                                voxCoords,
                                order=order,
                                prefilter=False)

    # make a N*3 list of vectors
    vecs = np.array([xvals, yvals, zvals]).transpose()

    # if interpolating, rescale those
    # vectors back to unit vectors
    if order != 0:
        dists = np.sqrt(np.sum(vecs ** 2, axis=1))
        vecs  = np.multiply(vecs.transpose(), 1.0 / dists).transpose()

    # make a bunch of vertices which represent lines 
    # (two vertices per line), centered at the origin
    # and scaled appropriately
    vecs[:, xax] *= 0.5 * self.xpixdim
    vecs[:, yax] *= 0.5 * self.ypixdim
    vecs = np.hstack((-vecs, vecs)).reshape((2 * nVoxels, 3))

    # Translate the world coordinates
    # by those line vertices
    worldCoords = worldCoords.repeat(2, 0) + vecs
    worldCoords = np.array(worldCoords, dtype=np.float32).ravel('C')

    # Draw all the lines!
    if xform is not None: 
        xform = transform.concat(xform. self.mvmat)
        gl.glMultMatrixf(xform)

    colour = opts.colour

    gl.glColor4f(colour[0], colour[1], colour[2], display.alpha)
    gl.glLineWidth(2)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)
    gl.glDrawArrays(gl.GL_LINES, 0, 2 * nVoxels)

    
def postDraw(self):

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPopMatrix()
