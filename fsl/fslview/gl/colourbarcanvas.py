#!/usr/bin/env python
#
# colourbarcanvas.py - Render a colour bar using OpenGL and matplotlib.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarCanvas`.

The :class:`ColourBarCanvas` contains logic to draw a colour bar (with
labels), and then renders said colour bar as a texture using OpenGL.

See the :mod:`~fsl.utils.colourbarbitmap` module for details on how
the colour bar is created.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL         as gl
import numpy             as np


import props

import fsl.utils.colourbarbitmap as cbarbmp
import fsl.data.strings          as strings


class ColourBarCanvas(props.HasProperties):
    """Contains logic to render a colour bar as an OpenGL texture.
    """

    cmap = props.ColourMap()
    """The :mod:`matplotlib` colour map to use."""

    
    vrange = props.Bounds(ndims=1)
    """The minimum/maximum values to display."""

    
    label = props.String()
    """A label to display under the centre of the colour bar."""

    
    orientation = props.Choice(
        ('horizontal', 'vertical'),
        labels=[strings.choices['ColourBarCanvas.orientation.horizontal'],
                strings.choices['ColourBarCanvas.orientation.vertical']])
    """Whether the colour bar should be vertical or horizontal. """

    
    labelSide = props.Choice(
        ('top-left', 'bottom-right'),
        labels=[strings.choices['ColourBarCanvas.labelSide.top-left'],
                strings.choices['ColourBarCanvas.labelSide.bottom-right']])
    """Whether the colour bar labels should be on the top/left, or bottom/right
    of the colour bar (depending upon whether the colour bar orientation is
    horizontal/vertical).
    """

    def __init__(self):
        """Adds a few listeners to the properties of this object, to update
        the colour bar when they change.
        """

        self._tex  = None
        self._name = '{}_{}'.format(self.__class__.__name__, id(self)) 

        def _update(*a):
            self._genColourBarTexture()
            self._refresh()

        for prop in ('cmap', 'vrange', 'label', 'orientation', 'labelSide'):
            self.addListener(prop, self._name, _update)
        

    def _initGL(self):
        """Called automatically by the OpenGL canvas target superclass (see
        the :class:`~fsl.fslview.gl.WXGLCanvasTarget` and
        :class:`~fsl.fslview.gl.OSMesaCanvasTarget` for details).

        Generates the colour bar texture.
        """
        self._genColourBarTexture()


    def _genColourBarTexture(self):
        """Generates a texture containing an image of the colour bar,
        according to the current property values.
        """

        self._setGLContext()

        w, h = self._getSize()

        if w == 0 or h == 0:
            if self.orientation == 'horizontal': w, h = 600, 200
            else:                                w, h = 200, 600

        if self.orientation == 'horizontal':
            if  self.labelSide == 'top-left': labelSide = 'top'
            else:                             labelSide = 'bottom'
        else:
            if  self.labelSide == 'top-left': labelSide = 'left'
            else:                             labelSide = 'right'

        if self.cmap is None:
            bitmap = np.zeros((w, h, 4), dtype=np.uint8)
        else:
            bitmap = cbarbmp.colourBarBitmap(
                self.cmap,
                self.vrange.xlo,
                self.vrange.xhi,
                w, h,
                self.label,
                self.orientation,
                labelSide)
            bitmap = np.flipud(bitmap)

        if self._tex is None:
            self._tex = gl.glGenTextures(1)

        # Allow textures of any size
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

        gl.glBindTexture(  gl.GL_TEXTURE_2D, self._tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_2D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)

        bitmap = bitmap.ravel('C')

        gl.glTexImage2D(gl.GL_TEXTURE_2D,
                        0,
                        gl.GL_RGBA8,
                        w,
                        h,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        bitmap)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)


    def _draw(self):
        """Renders the colour bar texture using all available canvas space."""

        self._setGLContext()
        
        width, height = self._getSize()

        # viewport
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, 1, 0, 1, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

        gl.glActiveTexture(gl.GL_TEXTURE0) 
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_REPLACE) 
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._tex)

        gl.glBegin(gl.GL_QUADS)
        gl.glTexCoord2f(0, 0)
        gl.glVertex3f(  0, 0, 0)
        gl.glTexCoord2f(0, 1)
        gl.glVertex3f(  0, 1, 0)
        gl.glTexCoord2f(1, 1)
        gl.glVertex3f(  1, 1, 0)
        gl.glTexCoord2f(1, 0)
        gl.glVertex3f(  1, 0, 0)
        gl.glEnd()

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glDisable(gl.GL_TEXTURE_2D)

        self._postDraw()
