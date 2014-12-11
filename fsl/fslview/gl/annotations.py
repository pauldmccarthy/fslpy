#!/usr/bin/env python
#
# annotations.py - 2D annotations on a SliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Annotations` class, which implements
functionality to draw 2D OpenGL annotations on a canvas

The :class:`Annotations` class is used by the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class.
"""

import logging
log = logging.getLogger(__name__)

import Queue

import numpy     as np
import OpenGL.GL as gl


import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform


class Annotations(object):

    
    def __init__(self, imageList, displayCtx):
        
        self._q          = Queue.Queue()
        self._imageList  = imageList
        self._displayCtx = displayCtx

        
    def _adjustColour(self, colour):
        if len(colour) == 3: return (colour[0], colour[1], colour[2], 1.0)
        else:                return colour

        
    def line(self, *args, **kwargs): self._q.put(Line(*args, **kwargs))
    def rect(self, *args, **kwargs): self._q.put(Rect(*args, **kwargs))


    def selection(self, voxels, imageIdx=None, *args, **kwargs):
        """
        Voxels must be an N*3 array of xyz values
        """
        
        if imageIdx is None:
            imageIdx = self._displayCtx.selectedImage

        image   = self._imageList[imageIdx]
        display = self._displayCtx.getDisplayProperties(image)

        self._q.put(VoxelSelection(voxels,
                                   xform=display.voxToDisplayMat,
                                   *args, **kwargs))

        
    def obj(self, obj):
        self._q.put(obj)
        

    def draw(self, xax, yax, zax, zpos):

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        while True:

            zpos = zpos + 1
            try:
                
                obj            = self._q.get_nowait()
                verts, indices = obj.vertices(xax, yax)

                verts[:, zax] = zpos

                verts   = np.array(verts,   dtype=np.float32).ravel('C')
                indices = np.array(indices, dtype=np.uint32)
                
                if obj.xform is not None:
                    gl.glMatrixMode(gl.GL_MODELVIEW)
                    gl.glPushMatrix()
                    gl.glMultMatrixf(obj.xform.ravel('C'))
                
                gl.glColor4f(*self._adjustColour(obj.colour))
                gl.glLineWidth(obj.width)

                gl.glVertexPointer(3, gl.GL_FLOAT, 0, verts)

                gl.glDrawElements(gl.GL_LINES,
                                  len(indices),
                                  gl.GL_UNSIGNED_INT,
                                  indices)

                if obj.xform is not None:
                    gl.glPopMatrix()
                
            except Queue.Empty:
                break
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)


class AnnotationObject(object):
    
    def __init__(self, xform=None, colour=None, width=None):
        
        if colour is None: colour = (1, 1, 1, 1)
        if width  is None: width  = 1

        self.colour = colour
        self.width  = width
        self.xform  = xform

        
class Line(AnnotationObject):

    def __init__(self, xy1, xy2, *args, **kwargs):
        AnnotationObject.__init__(self, *args, **kwargs)
        self.xy1       = xy1
        self.xy2       = xy2
        
    def vertices(self, xax, yax):
        
        verts                = np.zeros((2, 3))
        verts[0, [xax, yax]] = self.xy1
        verts[1, [xax, yax]] = self.xy2
        
        return verts, np.arange(2)

        
class Rect(AnnotationObject):

    def __init__(self, bl, br, tl, tr, *args, **kwargs):
        AnnotationObject.__init__(self, *args, **kwargs)
        self.bl        = bl
        self.br        = br
        self.tl        = tl
        self.tr        = tr

        
    def vertices(self, xax, yax):

        verts                = np.zeros((8, 3))
        verts[0, [xax, yax]] = self.bl
        verts[1, [xax, yax]] = self.br
        verts[2, [xax, yax]] = self.tl
        verts[3, [xax, yax]] = self.tr
        verts[4, [xax, yax]] = self.bl
        verts[5, [xax, yax]] = self.tl
        verts[6, [xax, yax]] = self.br
        verts[7, [xax, yax]] = self.tr

        return verts, np.arange(8)


class VoxelSelection(AnnotationObject):

    
    def __init__(self, voxels, *args, **kwargs):
        AnnotationObject.__init__(self, *args, **kwargs)

        
        self.voxels = voxels


    def vertices(self, xax, yax):

        return globject.voxelGrid(self.voxels, xax, yax, 1, 1)

# class Text(AnnotationObject) ?
# class Circle(AnnotationObject) ?
