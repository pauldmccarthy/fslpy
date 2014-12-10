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


import fsl.utils.transform as transform


class Annotations(object):

    
    def __init__(self, imageList, displayCtx, xax, yax, zax):
        
        self._q          = Queue.Queue()
        self._imageList  = imageList
        self._displayCtx = displayCtx

        self.changeAxes(xax, yax, zax)


    def changeAxes(self, xax, yax, zax):
        self._xax = xax
        self._yax = yax
        self._zax = zax
        
    def _adjustColour(self, colour):
        if len(colour) == 3: return (colour[0], colour[1], colour[2], 1.0)
        else:                return colour

        
    def line(self, *args, **kwargs): self._q.put(Line(*args, **kwargs))
    def rect(self, *args, **kwargs): self._q.put(Rect(*args, **kwargs))


    def voxelRegion(self, voxels, imageIdx=None, *args, **kwargs):
        """
        Voxels must be an N*3 array of xyz values
        """
        
        if imageIdx is None:
            imageIdx = self._displayCtx.selectedImage

        image   = self._imageList[imageIdx]
        display = self._displayCtx.getDisplayProperties(image)

        self._q.put(VoxelRegion(image, display, voxels, *args, **kwargs))

        
    def obj(self, obj):
        self._q.put(obj)
        

    def draw(self):

        # TODO line width is not supported -
        # to support different line widths, I'd
        # have to draw each object in a separate
        # glBegin/glEnd block, as the line width
        # must be specified before glBegin

        gl.glBegin(gl.GL_LINES)

        while True:

            try: 
                obj   = self._q.get_nowait()
                verts = obj.vertices()
                
                gl.glColor4f(*self._adjustColour(obj.colour))

                for vert in verts:
                    gl.glVertex3f(*vert)

            except Queue.Empty:
                break

        gl.glEnd()

        
class Line(object):

    def __init__(self, xyz1, xyz2, colour=(1, 1, 1), width=1):
        self.xyz1   = xyz1
        self.xyz2   = xyz2
        self.colour = colour
        self.width  = width


    def __eq__(self, other):

        return (np.all(np.abs(self.xyz1 - other.xyz1) < 0.0000001) and
                np.all(np.abs(self.xyz2 - other.xyz2) < 0.0000001))

    def __hash__(self):
        return hash(tuple(self.xyz1) + tuple(self.xyz2))
        
    def vertices(self):
        
        verts       = np.zeros((2, 3))
        verts[0, :] = self.xyz1
        verts[1, :] = self.xyz2
        
        return verts

        
class Rect(object):

    def __init__(self, bl, br, tl, tr, colour=(1, 1, 1), width=1):
        self.bl     = bl
        self.br     = br
        self.tl     = tl
        self.tr     = tr
        self.colour = colour
        self.width  = width

    def vertices(self):

        verts = np.zeros((8, 3))
        verts[0, :] = self.bl
        verts[1, :] = self.br
        verts[2, :] = self.tl
        verts[3, :] = self.tr
        verts[4, :] = self.bl
        verts[5, :] = self.tl
        verts[6, :] = self.br
        verts[7, :] = self.tr

        return verts


class VoxelRegion(object):

    def __init__(self,
                 voxToDisplayMat,
                 voxels=None,
                 colour=(1, 1, 1), width=1):
        
        self.colour          = colour
        self.width           = width
        self.voxToDisplayMat = voxToDisplayMat
        
        self.lineCounts = {}
        self.lines      = []

        self.voxels     = set()

        print 'new Region {}'.format(id(self))

        if voxels is not None:
            self.addVoxels(voxels)

    @profile
    def addVoxels(self, voxels):

        corners = np.repeat(np.array(voxels, dtype=np.float32), 8, axis=0)

        corners[::8, 0] -= 0.5
        corners[::8, 1] -= 0.5
        corners[::8, 2] -= 0.5

        corners[1::8, 0] -= 0.5
        corners[1::8, 1] -= 0.5
        corners[1::8, 2] += 0.5

        corners[2::8, 0] -= 0.5
        corners[2::8, 1] += 0.5
        corners[2::8, 2] -= 0.5

        corners[3::8, 0] -= 0.5
        corners[3::8, 1] += 0.5
        corners[3::8, 2] += 0.5 

        corners[4::8, 0] += 0.5
        corners[4::8, 1] -= 0.5
        corners[4::8, 2] -= 0.5

        corners[5::8, 0] += 0.5
        corners[5::8, 1] -= 0.5
        corners[5::8, 2] += 0.5

        corners[6::8, 0] += 0.5
        corners[6::8, 1] += 0.5
        corners[6::8, 2] -= 0.5

        corners[7::8, 0] += 0.5
        corners[7::8, 1] += 0.5
        corners[7::8, 2] += 0.5 

        corners = transform.transform(corners, self.voxToDisplayMat)

        linePairs = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3),
                     (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]

        for i in range(len(voxels)):

            if tuple(voxels[i]) in self.voxels: continue
            self.voxels.add(tuple(voxels[i]))

            i = i * 8

            for li, lj in linePairs:

                line = Line(corners[i + li, :], corners[i + lj, :])
                self.lines.append(line)
                lh = hash(line)
                self.lineCounts[lh] = self.lineCounts.get(lh, 0) + 1

            
    def vertices(self):

        verts = np.zeros((len(self.lines) * 2, 3))

        for i, line in enumerate(self.lines):
            if self.lineCounts[hash(line)] != 1: continue
            verts[i * 2,     :] = line.xyz1
            verts[i * 2 + 1, :] = line.xyz2

        return verts
    

# class Text(object)
# class Grid(objec)t
# class Circle(object) ?
