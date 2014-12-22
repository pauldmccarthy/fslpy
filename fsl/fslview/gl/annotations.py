#!/usr/bin/env python
#
# annotations.py - 2D annotations on a SliceCanvas.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Annotations` class, which implements
functionality to draw 2D OpenGL annotations on a canvas

The :class:`Annotations` class is used by the
:class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` class, and users of that
class, to annotate the canvas.
"""

import logging
log = logging.getLogger(__name__)


import numpy     as np
import OpenGL.GL as gl


import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform


class Annotations(object):
    """An :class:`Annotations` object provides functionality to draw 2D
    annotations on a 3D OpenGL canvas. Annotations may be enqueued via any
    of the :meth:`line`, :meth:`rect`, :meth:`selection` or :meth:`obj`,
    methods.

    A call to :meth:`draw` will then draw each of the queued annotations,
    and clear the queue.

    If an annotation is to be persistent, it can be enqueued, as above, but
    passing ``hold=True`` to the queueing method.  The annotation will then
    remain in the queue until it is removed via :meth:`dequeue`, or the
    entire annotations queue is cleared via :meth:`clear`.

    Annotations can be queued by one of the helper methods on the
    :class:`Annotations` object (e.g. :meth:`line`, :meth:`rect` or
    :meth:`selection`), or by manually creating an :class:`AnnotationObject`
    and passing it to the :meth:`obj` method.

    The :class:`AnnotationObject` defines a set of parameters which are
    shared by all annotations (e.g. colour and linewidth).
    """

    
    def __init__(self):
        """Creates an :class:`Annotations` object."""
        
        self._q     = []
        self._holdq = []

        
    def _adjustColour(self, colour):
        """Turns RGB colour tuples into RGBA tuples, if necessary."""
        if len(colour) == 3: return (colour[0], colour[1], colour[2], 1.0)
        else:                return colour

        
    def line(self, *args, **kwargs):
        """Queues a line for drawing - see the :class:`Line` class. """
        hold = kwargs.pop('hold', False)
        return self.obj(Line(*args, **kwargs), hold)

        
    def rect(self, *args, **kwargs):
        """Queues a rectangle for drawing - see the :class:`Rectangle` class.
        """
        hold = kwargs.pop('hold', False)
        return self.obj(Rect(*args, **kwargs), hold)


    def selection(self, *args, **kwargs):
        """Queues a selection for drawing - see the :class:`VoxelSelection`
        class.
        """ 
        hold = kwargs.pop('hold', False)
        return self.obj(VoxelSelection(*args, **kwargs), hold)

        
    def obj(self, obj, hold=False):
        """Queues the given :class:`AnnotationObject` for drawing."""

        
        if hold: self._holdq.append(obj)
        else:    self._q    .append(obj)

        return obj


    def dequeue(self, obj, hold=False):
        """Removes the given :class:`AnnotationObject` from the queue.
        """

        if hold:
            try:    self._holdq.remove(obj)
            except: pass
        else:
            try:    self._q.remove(obj)
            except: pass


    def clear(self):
        """Clears both the normal queue and the persistent (a.k.a. ``hold``)
        queue.
        """
        self._q     = []
        self._holdq = []
        

    def draw(self, xax, yax, zax, zpos):
        """Draws all enqueued annotations.

        :arg xax:  Data axis which corresponds to the horizontal screen axis.
        
        :arg yax:  Data axis which corresponds to the vertical screen axis.
        
        :arg zax:  Data axis which corresponds to the depth screen axis.
        
        :arg zpos: Position along the Z axis, above which all annotations
                   should be drawn.
        """

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        objs = self._holdq + self._q

        for obj in objs:

            verts, indices = obj.vertices(xax, yax, zax, zpos)

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
            
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        self._q = []


class AnnotationObject(object):
    """Superclass for all annotation objects. Subclasses must override the
    :meth:`vertices` method.
    """
    
    def __init__(self, xform=None, colour=None, width=None):
        """Create an AnnotationObject.

        :arg xform:  Transformation matrix which will be applied to all
                     vertex coordinates.
        
        :arg colour: RGB/RGBA tuple specifying the annotation.
        
        :arg width:  Line width to use for the annotation.
        """
        
        if colour is None: colour = (1, 1, 1, 1)
        if width  is None: width  = 1

        self.colour = colour
        self.width  = width
        self.xform  = xform

        
    def vertices(self, xax, yax, zax, zpos):
        """Generate/return vertices to render this :class:`AnnotationObject`.

        This method must be overridden by subclasses, and must return two
        values:

          - A 2D ``float32`` numpy array of shape ``(N, 3)`` (where ``N`` is
            the number of vertices), containing the xyz coordinates of every
            vertex.

          - A 1D ``uint32`` numpy array containing the indices of all
            vertices to be rendered.

        :arg xax:  The axis which corresponds to the horizontal screen axis.
        
        :arg yax:  The axis which corresponds to the horizontal screen axis.
        
        :arg zax:  The axis which corresponds to the depth screen axis.
        
        :arg zpos: The position along the depth axis.
        """
        raise NotImplementedError('Subclasses must implement '
                                  'the vertices method')

        
class Line(AnnotationObject):
    """Annotation object which represents a 2D line.
    """

    def __init__(self, xy1, xy2, *args, **kwargs):
        """Create a :class:`Line`. The (x, y) coordinate tuples should be in
        relation to the axes which map to the horizontal/vertical screen axes
        on the target canvas.

        :arg xy1: Tuple containing the (x, y) coordinates of one endpoint.
        
        :arg xy2: Tuple containing the (x, y) coordinates of the second
                  endpoint.

        """
        AnnotationObject.__init__(self, *args, **kwargs)
        self.xy1       = xy1
        self.xy2       = xy2

        
    def vertices(self, xax, yax, zax, zpos):
        verts                = np.zeros((2, 3))
        verts[0, [xax, yax]] = self.xy1
        verts[1, [xax, yax]] = self.xy2
        
        return verts, np.arange(2)

        
class Rect(AnnotationObject):
    """Annotation object which represents a 2D rectangle."""

    def __init__(self, xy, w, h, *args, **kwargs):
        """Create a :class:`Rect` annotation. The `xy` parameter should
        be a tuple specifying the bottom left of the rectangle, and the `w`
        and `h` parameters specifying the rectangle width and height
        respectively.
        """
        AnnotationObject.__init__(self, *args, **kwargs)
        self.xy = xy
        self.w  = w
        self.h  = h

        
    def vertices(self, xax, yax, zax, zpos):

        xy = self.xy
        w  = self.w
        h  = self.h

        bl = [xy[0],     xy[1]]
        br = [xy[0] + w, xy[1]]
        tl = [xy[0],     xy[1] + h]
        tr = [xy[0] + w, xy[1] + h]

        verts                = np.zeros((8, 3))
        verts[0, [xax, yax]] = bl
        verts[1, [xax, yax]] = br
        verts[2, [xax, yax]] = tl
        verts[3, [xax, yax]] = tr
        verts[4, [xax, yax]] = bl
        verts[5, [xax, yax]] = tl
        verts[6, [xax, yax]] = br
        verts[7, [xax, yax]] = tr

        return verts, np.arange(8)


class VoxelSelection(AnnotationObject):
    """Annotation object which represents a collection of 'selected' voxels.

    Each selected voxel is highlighted with a rectangle around its border.
    """

    
    def __init__(self,
                 selectMask,
                 displayToVoxMat,
                 voxToDisplayMat,
                 offsets=None,
                 *args,
                 **kwargs):
        """Create a :class:`VoxelSelection` object.

        :arg selectMask:      A 3D numpy array, the same shape as the image
                              being annotated (or a sub-space of the image - 
                              see the ``offsets`` argument),  which is 
                              interpreted as a mask array - values which are 
                              ``True`` denote selected voxels. 

        :arg displayToVoxMat: A transformation matrix which transforms from
                              display space coordinates into voxel space
                              coordinates.

        :arg voxToDisplayMat: A transformation matrix which transforms from
                              voxel coordinates into display space
                              coordinates.

        :arg offsets:         If ``None`` (the default), the ``selectMask``
                              must have the same shape as the image data
                              being annotated. Alternately, you may set
                              ``offsets`` to a sequence of three values,
                              which are used as offsets for the xyz voxel
                              values. This is to allow for a sub-space of
                              the full image space to be annotated.
        """
        
        kwargs['xform'] = voxToDisplayMat
        AnnotationObject.__init__(self, *args, **kwargs)
        
        if offsets is None:
            offsets = [0, 0, 0]

        self.displayToVoxMat = displayToVoxMat
        self.selectMask      = selectMask
        self.offsets         = offsets


    def vertices(self, xax, yax, zax, zpos):

        dispLoc = [0] * 3
        dispLoc[zax] = zpos
        voxLoc = transform.transform([dispLoc], self.displayToVoxMat)[0]

        vox = int(round(voxLoc[zax]))

        restrictions = [slice(None)] * 3
        restrictions[zax] = slice(vox - self.offsets[zax],
                                  vox - self.offsets[zax] + 1)

        xs, ys, zs = np.where(self.selectMask[restrictions])
        voxels     = np.vstack((xs, ys, zs)).T

        for ax in range(3):
            off = restrictions[ax].start
            if off is None:
                off = 0
            voxels[:, ax] += off + self.offsets[ax]

        return globject.voxelGrid(voxels, xax, yax, 1, 1)

# class Text(AnnotationObject) ?
# class Circle(AnnotationObject) ?
