#!/usr/bin/env python
#
# gltensorline.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a tensor image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL vertex creation and rendering code for drawing a # X*Y*Z*3 image as
a tensor image.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL     as gl
import numpy         as np
import scipy.ndimage as ndi

import globject

class GLTensorLine(object):
    """The :class:`GLTensorLine` class encapsulates the data and logic required to
    render 2D slices of a X*Y*Z*3 image as tensor lines.
    """

    def __init__(self, image, display):
        """Create a :class:`GLTensorLine` object bound to the given image and
        display.

        :arg image:        A :class:`~fsl.data.image.Image` object.
        
        :arg imageDisplay: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                           object which describes how the image is to be
                           displayed .
        """

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ tensor angles')

        self.image   = image
        self.display = display
        self._ready  = False

        
    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised, and the
        image is ready to be drawn, `False` before.
        """ 
        return self._ready


    def setAxes(self, xax, yax):
        """Calculates vertex locations according to the specified X/Y axes, and image
        display properties. This is done via a call to the
        :func:`~fsl.fslview.gl.globject.calculateSamplePoints` function.
        """

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
        """Initialise the OpenGL data required to render the given image.

        After this method has been called, the image is ready to be rendered.
        """ 
        self.setAxes(xax, yax)
        self._configDisplayListeners()
        self._ready = True

        
    def destroy(self):
        """Does nothing - nothing needs to be cleaned up. """
        pass

        
    def draw(self, zpos, xform=None):
        """Calculates tensor orientations for the specified Z-axis location, and
        renders them using immediate mode OpenGL.
        """

        xax         = self.xax
        yax         = self.yax
        zax         = self.zax
        image       = self.image
        display     = self.display
        worldCoords = self.worldCoords

        if not display.enabled: return

        worldCoords[:, zax] = zpos

        # Transform the world coordinates to
        # floating point voxel coordinates
        voxCoords  = image.worldToVox(worldCoords).transpose()
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
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPushMatrix()
            gl.glMultMatrixf(xform)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        colour = self.display.cmap(0.5)

        gl.glColor4f(colour[0], colour[1], colour[2], self.display.alpha)
        gl.glLineWidth(2)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)
        gl.glDrawArrays(gl.GL_LINES, 0, 2 * nVoxels)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        if xform is not None:
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glPopMatrix()

    def _configDisplayListeners(self):
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.
        """

        def coordUpdate(*a):
            self.setAxes(self.xax, self.yax)

        display = self.display
        lnrName = '{}_{}'.format(self.__class__.__name__, id(self))

        display.addListener('transform',       lnrName, coordUpdate)
        display.addListener('interpolation',   lnrName, coordUpdate)
        display.addListener('voxelResolution', lnrName, coordUpdate)
        display.addListener('worldResolution', lnrName, coordUpdate)
