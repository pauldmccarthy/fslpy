#!/usr/bin/env python
#
# osmesaslicecanvas.py - A SliceCanvas which uses OSMesa for off-screen OpenGL
# rendering.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides the :class:`OSMesaSliceCanvas` which supports off-screen
rendering.
"""

import logging
log = logging.getLogger(__name__)

import numpy            as np
import matplotlib.image as mplimg


import OpenGL.GL              as gl
import OpenGL.arrays          as glarrays
import OpenGL.raw.osmesa.mesa as osmesa

import fsl.fslview.gl as fslgl
import slicecanvas    as sc
       

class OSMesaSliceCanvas(sc.SliceCanvas):
    """A :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`
    which uses OSMesa for static off-screen OpenGL rendering.
    """
    
    def __init__(self,
                 imageList,
                 zax=0,
                 width=0,
                 height=0):
        """See the :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` constructor
        for details on the other parameters.

        :arg width:  Canvas width in pixels
        
        :arg height: Canvas height in pixels
        """

        self._width  = width
        self._height = height
        self._buffer = glarrays.GLubyteArray.zeros((height, width, 4)) 
 
        sc.SliceCanvas.__init__(self, imageList, zax)


    def saveToFile(self, filename):
        """Saves the contents of this canvas as an image, to the specified
        file.
        """
        ia  = gl.glReadPixels(
            0, 0,
            self._width, self._height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)
        
        img = np.fromstring(ia, dtype=np.uint8)
        img = img.reshape((self._height, self._width, 4))
        img = np.flipud(img)
        mplimg.imsave(filename, img) 


    def _getSize(self):
        """Returns a tuple containing the canvas width and height.
        """
        return self._width, self._height

        
    def _setGLContext(self):
        """Configures the GL context to render to this canvas. """
        osmesa.OSMesaMakeCurrent(fslgl.getOSMesaContext(),
                                 self._buffer,
                                 gl.GL_UNSIGNED_BYTE,
                                 self._width,
                                 self._height)

        
    def _refresh( self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass

        
    def _postDraw(self):
        """Does nothing."""
        pass
