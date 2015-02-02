#!/usr/bin/env python
#
# glvector.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a vector.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL vertex creation and rendering code for drawing a X*Y*Z*3 image as
a vector.

Vectors can be displayed in one of several 'modes'.
 - RGB
 - Line
 - Arrow?

Each mode module must provide the following functions:

 - init(self)

 - destroy(self)

 - setAxes(self)

 - preDraw(self)

 - draw(self, zpos, xform=None)

 - postDraw(self)
"""

import logging

import numpy                   as np
import OpenGL.GL               as gl

import fsl.data.image          as fslimage
import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.textures as fsltextures
import fsl.fslview.gl.globject as globject

log = logging.getLogger(__name__)


class GLVector(globject.GLObject):
    """The :class:`GLVector` class encapsulates the data and logic required
    to render 2D slices of a X*Y*Z*3 image as vectors.
    """

    def __init__(self, image, display):
        """Create a :class:`GLVector` object bound to the given image and
        display.

        :arg image:        A :class:`~fsl.data.image.Image` object.
        
        :arg imageDisplay: A :class:`~fsl.fslview.displaycontext.Display`
                           object which describes how the image is to be
                           displayed .
        """

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ vector angles')

        globject.GLObject.__init__(self, image, display)
        self._ready = False

        
    def init(self):
        """Initialise the OpenGL data required to render the given image.

        After this method has been called, the image is ready to be rendered.
        """

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        self.xColourTexture = gl.glGenTextures(1)
        self.yColourTexture = gl.glGenTextures(1)
        self.zColourTexture = gl.glGenTextures(1)
        self.modTexture     = None
        self.imageTexture   = None
        
        def modUpdate( *a):
            self.refreshModulateTexture()

        def cmapUpdate(*a):
            self.refreshColourTextures()

        def modeChange(*a):
            self._onModeChange()

        def coordUpdate(*a):
            self.setAxes(self.xax, self.yax)

        display.addListener('alpha',       name, cmapUpdate)
        display.addListener('transform',   name, coordUpdate)
        display.addListener('resolution',  name, coordUpdate) 
        opts   .addListener('xColour',     name, cmapUpdate)
        opts   .addListener('yColour',     name, cmapUpdate)
        opts   .addListener('zColour',     name, cmapUpdate)
        opts   .addListener('suppressX',   name, cmapUpdate)
        opts   .addListener('suppressY',   name, cmapUpdate)
        opts   .addListener('suppressZ',   name, cmapUpdate)
        opts   .addListener('modulate',    name, modUpdate)
        opts   .addListener('displayMode', name, modeChange)

        def prefilter(data):
            data = data.transpose((3, 0, 1, 2))
            if self.displayOpts.displayMode == 'rgb': return np.abs(data)
            else:                                     return data

        self.imageTexture = fsltextures.getTexture(
            self.image,
            type(self).__name__,
            display=self.display,
            nvals=3,
            normalise=True,
            prefilter=prefilter) 

        self.refreshModulateTexture()
        self.refreshColourTextures()

        fslgl.glvector_funcs.init(self)
        
        self._ready = True

        
    def destroy(self):
        """Does nothing - nothing needs to be cleaned up. """

        gl.glDeleteTextures(self.xColourTexture)
        gl.glDeleteTextures(self.yColourTexture)
        gl.glDeleteTextures(self.zColourTexture)

        fsltextures.deleteTexture(self.imageTexture)
        fsltextures.deleteTexture(self.modTexture) 

        self.display    .removeListener('alpha',       self.name)
        self.display    .removeListener('transform',   self.name)
        self.display    .removeListener('resolution',  self.name)
        self.displayOpts.removeListener('xColour',     self.name)
        self.displayOpts.removeListener('yColour',     self.name)
        self.displayOpts.removeListener('zColour',     self.name)
        self.displayOpts.removeListener('suppressX',   self.name)
        self.displayOpts.removeListener('suppressY',   self.name)
        self.displayOpts.removeListener('suppressZ',   self.name)
        self.displayOpts.removeListener('modulate',    self.name)
        self.displayOpts.removeListener('displayMode', self.name)

        fslgl.glvector_funcs.destroy(self)

        
    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised,
        and the image is ready to be drawn, `False` before.
        """ 
        return self._ready


    def _onModeChange(self, *a):
        """Called when the
        :attr:`~fsl.fslview.displaycontext.vectoropts.VectorOpts` property
        changes.

        Initialises data and GL state for the newly selected vector display
        mode.
        """

        # No texture interpolation in line mode
        if self.displayOpts.displayMode == 'line':
            
            if self.display.interpolation != 'none':
                self.display.interpolation = 'none'
                
            self.display.disableProperty('interpolation')
            
        elif self.displayOpts.displayMode == 'rgb':
            self.display.enableProperty('interpolation')
            
        fslgl.glvector_funcs.destroy(self)
        self.imageTexture.refreshTexture()
        fslgl.glvector_funcs.init(self)
        self.setAxes(self.xax, self.yax)
        

    def refreshModulateTexture(self):

        modImage = self.displayOpts.modulate

        if self.modTexture is not None:
            fsltextures.deleteTexture(self.modTexture)

        if modImage == 'none':
            textureData = np.zeros((5, 5, 5), dtype=np.uint8)
            textureData[:] = 255
            modImage   = fslimage.Image(textureData)
            modDisplay = None
            norm       = False
        else:
            modDisplay = self.display
            norm       = True

        self.modTexture = fsltextures.getTexture(
            modImage,
            '{}_{}_modulate'.format(type(self).__name__, id(self.image)),
            display=modDisplay,
            normalise=norm)


    def refreshColourTextures(self, colourRes=256):

        xcol = self.displayOpts.xColour + [1.0]
        ycol = self.displayOpts.yColour + [1.0]
        zcol = self.displayOpts.zColour + [1.0]

        xsup = self.displayOpts.suppressX
        ysup = self.displayOpts.suppressY
        zsup = self.displayOpts.suppressZ 

        xtex = self.xColourTexture
        ytex = self.yColourTexture
        ztex = self.zColourTexture

        for colour, texture, suppress in zip(
                (xcol, ycol, zcol),
                (xtex, ytex, ztex),
                (xsup, ysup, zsup)):

            if not suppress:
                cmap = np.array(
                    [np.linspace(0.0, i, colourRes) for i in colour])
            else:
                cmap = np.zeros((4, colourRes))

            cmap[3, :] = self.display.alpha
            cmap[3, 0] = 0.0

            cmap = np.array(np.floor(cmap * 255), dtype=np.uint8).ravel('F')

            gl.glBindTexture(gl.GL_TEXTURE_1D, texture)
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_MAG_FILTER,
                               gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_MIN_FILTER,
                               gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_EDGE)

            gl.glTexImage1D(gl.GL_TEXTURE_1D,
                            0,
                            gl.GL_RGBA8,
                            colourRes,
                            0,
                            gl.GL_RGBA,
                            gl.GL_UNSIGNED_BYTE,
                            cmap)

        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
    

    def setAxes(self, xax, yax):
        """Calculates vertex locations according to the specified X/Y axes,
        and image display properties. This is done via a call to the
        :func:`~fsl.fslview.gl.globject.calculateSamplePoints` function.
        """

        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        fslgl.glvector_funcs.setAxes(self)

        
    def preDraw(self):
        if not self.display.enabled:
            return

        gl.glEnable(gl.GL_TEXTURE_1D)
        gl.glEnable(gl.GL_TEXTURE_3D)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.imageTexture.texture)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.modTexture.texture) 

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.xColourTexture)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.yColourTexture)

        gl.glActiveTexture(gl.GL_TEXTURE4)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.zColourTexture) 
 
        fslgl.glvector_funcs.preDraw(self)

        
    def draw(self, zpos, xform=None):
        if not self.display.enabled:
            return
        
        fslgl.glvector_funcs.draw(self, zpos, xform)

        
    def postDraw(self):
        if not self.display.enabled:
            return

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)

        gl.glActiveTexture(gl.GL_TEXTURE3)
        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)

        gl.glActiveTexture(gl.GL_TEXTURE4)
        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)    

        gl.glDisable(gl.GL_TEXTURE_1D) 
        gl.glDisable(gl.GL_TEXTURE_3D) 
        
        fslgl.glvector_funcs.postDraw(self) 
