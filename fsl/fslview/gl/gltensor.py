#!/usr/bin/env python
#
# gltensor.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a tensor image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL vertex creation and rendering code for drawing a X*Y*Z*3 image as
a tensor image.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL     as gl
import numpy         as np
import scipy.ndimage as ndi

import globject

import fsl.utils.transform as transform


class GLTensor(globject.GLObject):
    """The :class:`GLTensor` class encapsulates the data and logic required to
    render 2D slices of a X*Y*Z*3 image as tensor lines.
    """

    def __init__(self, image, display):
        """Create a :class:`GLTensor` object bound to the given image and
        display.

        :arg image:        A :class:`~fsl.data.image.Image` object.
        
        :arg imageDisplay: A :class:`~fsl.fslview.displaycontext.Display`
                           object which describes how the image is to be
                           displayed .
        """

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ tensor angles')

        globject.GLObject.__init__(self, image, display)
        self._ready = False


        if self.displayOpts.displayMode == 'line':
            self.preDraw  = self.lineModePreDraw
            self.draw     = self.lineModeDraw
            self.postDraw = self.lineModePostDraw
        elif self.displayOpts.displayMode == 'rgb':
            self.preDraw  = self.rgbModePreDraw
            self.draw     = self.rgbModeDraw
            self.postDraw = self.rgbModePostDraw 

    
    def addDisplayListeners(self):
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.
        """

        display = self.display
        opts    = self.displayOpts

        def coordUpdate(*a):
            self.setAxes(self.xax, self.yax)

        def modeChange(*a):
            if opts.displayMode == 'line':
                self.preDraw  = self.lineModePreDraw
                self.draw     = self.lineModeDraw 
                self.postDraw = self.lineModePostDraw
                self.rgbModeDestroy()

            elif opts.displayMode == 'rgb':
                self.preDraw  = self.rgbModePreDraw
                self.draw     = self.rgbModeDraw 
                self.postDraw = self.rgbModePostDraw
                self.lineModeDestroy()

            self.setAxes(self.xax, self.yax)
            

        lName = '{}_{}'.format(self.__class__.__name__, id(self))

        display.addListener('transform',     lName, coordUpdate)
        display.addListener('interpolation', lName, coordUpdate)
        display.addListener('resolution',    lName, coordUpdate)
        opts   .addListener('displayMode',   lName, modeChange)

        
    def removeDisplayListeners(self):
        lName = '{}_{}'.format(self.__class__.__name__, id(self))

        self.display    .removeListener('transform',     lName)
        self.display    .removeListener('interpolation', lName)
        self.display    .removeListener('resolution',    lName)
        self.displayOpts.removeListener('displayMode',   lName)


    def init(self, xax, yax):
        """Initialise the OpenGL data required to render the given image.

        After this method has been called, the image is ready to be rendered.
        """ 
        self.setAxes(xax, yax)
        self.addDisplayListeners()
        self._ready = True

        
    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised, and the
        image is ready to be drawn, `False` before.
        """ 
        return self._ready

        
    def destroy(self):
        """Does nothing - nothing needs to be cleaned up. """

        self.removeDisplayListeners()

        if   self.displayOpts.displayMode == 'line': self.lineModeDestroy()
        elif self.displayOpts.displayMode == 'rgb':  self.rgbModeDestroy()


    def setAxes(self, xax, yax):
        """Calculates vertex locations according to the specified X/Y axes,
        and image display properties. This is done via a call to the
        :func:`~fsl.fslview.gl.globject.calculateSamplePoints` function.
        """

        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        if   self.displayOpts.displayMode == 'line': self.lineModeInit()
        elif self.displayOpts.displayMode == 'rgb':  self.rgbModeInit()


    #######################
    # methods for Line Mode
    #######################


    def lineModeInit(self):

        worldCoords, xpixdim, ypixdim, lenx, leny = \
            globject.calculateSamplePoints(
                self.image,
                self.display,
                self.xax,
                self.yax)

        self.worldCoords = worldCoords
        self.xpixdim     = xpixdim
        self.ypixdim     = ypixdim 

        
    def lineModeDestroy(self):
        del self.worldCoords
        del self.xpixdim
        del self.ypixdim

    
    def lineModePreDraw(self):

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        self.mvmat = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        
    def lineModeDraw(self, zpos, xform=None):
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

        
    def lineModePostDraw(self):

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()



    ######################
    # Methods for RGB mode
    ######################

    def rgbModeInit(self):
        pass

    def rgbModeDestroy(self):
        pass
    
    def rgbModePreDraw(self):
        pass

    def rgbModeDraw(self, zpos, xform=None):
        pass

    def rgbModePostDraw(self):
        pass
