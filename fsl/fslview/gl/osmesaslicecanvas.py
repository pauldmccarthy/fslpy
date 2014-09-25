#!/usr/bin/env python
#
# osmesaslicecanvas.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL
OpenGL.ERROR_ON_COPY = True 
OpenGL.STORE_POINTERS = False 

import OpenGL.GL              as gl



import OpenGL.arrays          as glarrays
import OpenGL.platform        as glplatform
import OpenGL.raw.osmesa.mesa as osmesa

import slicecanvas as sc
       

class OSMesaSliceCanvas(sc.SliceCanvas):
    
    def __init__(self,
                 imageList,
                 zax=0,
                 glContext=None,
                 glVersion=None,
                 width=0,
                 height=0):

        self._width  = width
        self._height = height 
 
        sc.SliceCanvas.__init__(self, imageList, zax, glContext, glVersion)

        self._initGL()


    def _getSize(self):
        return self._width, self._height
        
    def _makeGLContext(self):
        ctx       = osmesa.OSMesaCreateContext(gl.GL_RGBA, None)
        targetBuf = glarrays.GLubyteArray.zeros((self._height, self._width, 4))
        p = glarrays.ArrayDatatype.dataPointer(targetBuf) 
        self._targetBuf = targetBuf
        self._p = p


        def eq(s, o):
            return True
        def hash(s):
            return 1234
            

        setattr(ctx, '__hash__', hash)
        setattr(ctx, '__eq__',   eq)

        print dir(ctx)

        
        return ctx
        
    def _setGLContext(self):
        assert(osmesa.OSMesaMakeCurrent(self.glContext,
                                        self._targetBuf,
                                        gl.GL_UNSIGNED_BYTE,
                                        self._width,
                                        self._height))
        assert(glplatform.CurrentContextIsValid())
 
    def _refresh(self): pass
