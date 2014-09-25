#!/usr/bin/env python
#
# slicecanvas_draw.py - Render slices from a collection of images in an OpenGL
#                       1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Render slices from a collection of images in an OpenGL 1.4 compatible
 manner, using immediate mode rendering. 

.. note:: This module is extremely tightly coupled to the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class, to the
:class:`~fsl.fslview.gl.glimage.GLImage` class, and to the
:mod:`~fsl.fslview.gl.glimage.gl14.glimage_funcs` module.

This module provides one function:

  - :func:`draw` draws slices from all of the images in an
    :class:`~fsl.data.image.ImageList` to a
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` display.
"""

import logging
log = logging.getLogger(__name__)


import OpenGL.GL as gl

    
def draw(canvas):
    """Draws the currently selected slice (as specified by the ``z``
    value of the :attr:`pos` property) to the canvas."""

    # clear the canvas
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    # enable transparency
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    # disable interpolation
    gl.glShadeModel(gl.GL_FLAT)

    for image in canvas.imageList:

        try: globj = image.getAttribute(canvas.name)
        except KeyError:
            continue

        if (globj is None) or (not globj.ready()):
            continue

        log.debug('Drawing {} slice for image {}'.format(
            canvas.zax, image.name))

        globj.draw(canvas.pos.z)
