#!/usr/bin/env python
#
# gltensor.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a tensor image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL vertex creation and rendering code for drawing a X*Y*Z*3 image as
a tensor image.

Tensors can be displayed in oneof several 'modes'.

 - init(self)

 - destroy(self)

 - setAxes(self)

 - preDraw(self)

 - draw(self, zpos, xform=None)

 - postDraw(self)




"""

import logging
log = logging.getLogger(__name__)


import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.globject as globject


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

        def modeChange(*a):
            self.modeMod.destroy(self)
            self._setModeModule()
            self.modeMod.init(self)
            self.setAxes(self.xax, self.yax)

        self.displayOpts.addListener('displayMode', self.name, modeChange)

        self.modeMod.init(self)
        
        self._ready = True

        
    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised, and the
        image is ready to be drawn, `False` before.
        """ 
        return self._ready

        
    def destroy(self):
        """Does nothing - nothing needs to be cleaned up. """

        self.displayOpts.removeListener('displayMode', self.name)

        self.modeMod.destroy(self)


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
        self.modeMod.preDraw(self)

        
    def draw(self, zpos, xform=None):
        self.modeMod.draw(self, zpos, xform)

        
    def postDraw(self):
        self.modeMod.postDraw(self) 
