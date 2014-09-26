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

import OpenGL

# Using PyOpenGL 3.1 (and OSX Mavericks 10.9.4 on a MacbookPro11,3), the
# OpenGL.contextdata.setValue method throws 'unhashable type' TypeErrors
# unless we set these constants. I don't know why.
OpenGL.ERROR_ON_COPY  = True 
OpenGL.STORE_POINTERS = False 

import OpenGL.GL              as gl
import OpenGL.arrays          as glarrays
import OpenGL.raw.osmesa.mesa as osmesa

import slicecanvas as sc
       

class OSMesaSliceCanvas(sc.SliceCanvas):
    """A :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`
    which uses OSMesa for static off-screen OpenGL rendering.
    """
    
    def __init__(self,
                 imageList,
                 zax=0,
                 glContext=None,
                 glVersion=None,
                 width=0,
                 height=0):
        """See the :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` constructor
        for details on the other parameters.

        :arg width:  Canvas width in pixels
        
        :arg height: Canvas height in pixels
        """

        self._width  = width
        self._height = height 
 
        sc.SliceCanvas.__init__(self, imageList, zax, glContext, glVersion)

        # We're doing off-screen rendering, so we
        # can initialise the GL data immediately
        self._initGL()


    def _getSize(self):
        """Returns a tuple containing the canvas width and height.
        """
        return self._width, self._height

        
    def _makeGLContext(self):
        """Creates and returns a OSMesa OpenGL context. Also creates the
        buffer which is to be used as the 'screen'.
        """
        ctx       = osmesa.OSMesaCreateContext(gl.GL_RGBA, None)
        targetBuf = glarrays.GLubyteArray.zeros((self._height, self._width, 4))
        
        self._targetBuf = targetBuf
        return ctx

        
    def _setGLContext(self):
        """Configures the GL context to render to this canvas. """
        osmesa.OSMesaMakeCurrent(self.glContext,
                                 self._targetBuf,
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
