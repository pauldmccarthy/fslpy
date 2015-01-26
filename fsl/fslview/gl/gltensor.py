#!/usr/bin/env python
#
# gltensor.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a tensor image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL vertex creation and rendering code for drawing a X*Y*Z*3 image as
a tensor image.

Tensors can be displayed in one of several 'modes'.

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

        self._setModeModule()


    def _setModeModule(self):

        mode = self.displayOpts.displayMode
        
        if   mode == 'line': self.modeMod = fslgl.gltensor_line_funcs
        elif mode == 'rgb':  self.modeMod = fslgl.gltensor_rgb_funcs

        else:
            raise RuntimeError('No tensor module for mode {}'.format(mode))



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
        
        def modUpdate( *a):
            self.refreshModulateTexture()

        def cmapUpdate(*a):
            self.refreshColourTextures()

        def modeChange(*a):
            self.modeMod.destroy(self)
            self._setModeModule()
            self.modeMod.init(self)
            self.setAxes(self.xax, self.yax)

        display.addListener('alpha',       name, cmapUpdate)
        opts   .addListener('xColour',     name, cmapUpdate)
        opts   .addListener('yColour',     name, cmapUpdate)
        opts   .addListener('zColour',     name, cmapUpdate)
        opts   .addListener('suppressX',   name, cmapUpdate)
        opts   .addListener('suppressY',   name, cmapUpdate)
        opts   .addListener('suppressZ',   name, cmapUpdate)
        opts   .addListener('modulate',    name, modUpdate)
        opts   .addListener('displayMode', name, modeChange)

        self.refreshModulateTexture()
        self.refreshColourTextures()


        def prefilter(data):
            return np.abs(data.transpose((3, 0, 1, 2)))

        self.imageTexture = fsltextures.getTexture(
            self.image,
            type(self).__name__,
            display=self.display,
            nvals=3,
            normalise=True,
            prefilter=prefilter) 

        self.modeMod.init(self)
        
        self._ready = True

        
    def destroy(self):
        """Does nothing - nothing needs to be cleaned up. """

        gl.glDeleteTextures(self.xColourTexture)
        gl.glDeleteTextures(self.yColourTexture)
        gl.glDeleteTextures(self.zColourTexture)

        fsltextures.deleteTexture(self.imageTexture)
        fsltextures.deleteTexture(self.modTexture) 

        self.display    .removeListener('alpha',       self.name)
        self.displayOpts.removeListener('xColour',     self.name)
        self.displayOpts.removeListener('yColour',     self.name)
        self.displayOpts.removeListener('zColour',     self.name)
        self.displayOpts.removeListener('suppressX',   self.name)
        self.displayOpts.removeListener('suppressY',   self.name)
        self.displayOpts.removeListener('suppressZ',   self.name)
        self.displayOpts.removeListener('modulate',    self.name)
        self.displayOpts.removeListener('displayMode', self.name)

        self.modeMod.destroy(self)

        
    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised, and the
        image is ready to be drawn, `False` before.
        """ 
        return self._ready



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

        self.modeMod.setAxes(self)

        
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
 
        self.modeMod.preDraw(self)

        
    def draw(self, zpos, xform=None):
        if not self.display.enabled:
            return
        
        self.modeMod.draw(self, zpos, xform)

        
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
        
        self.modeMod.postDraw(self) 
