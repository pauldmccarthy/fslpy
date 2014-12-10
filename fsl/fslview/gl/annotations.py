#!/usr/bin/env python
#
# annotations.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import Queue

import numpy     as np
import OpenGL.GL as gl


class Annotations(object):

    def __init__(self):
        self._q = Queue.Queue()


    def line(self, *args, **kwargs): self._q.put(Line(*args, **kwargs))
    def rect(self, *args, **kwargs): self._q.put(Rect(*args, **kwargs))

    def draw(self):

        while True:

            try: 
                obj = self._q.get_nowait()
                obj.draw()

            except Queue.Empty:
                break


def _adjustColour(colour):
    if len(colour) == 3: return (colour[0], colour[1], colour[2], 1.0)
    else:                return colour


class Line(object):

    def __init__(self, xyz1, xyz2, colour, width=1):
        self.xyz1   = xyz1
        self.xyz2   = xyz2
        self.colour = _adjustColour(colour)
        self.width  = width

    def draw(self):
        gl.glLineWidth(self.width)
        gl.glBegin(gl.GL_LINES)
        gl.glColor4f( *self.colour)
        gl.glVertex3f(*self.xyz1)
        gl.glVertex3f(*self.xyz2)
        gl.glEnd() 

        
class Rect(object):

    def __init__(self, bl, br, tl, tr, colour, lineWidth=1):
        self.bl        = bl
        self.br        = br
        self.tl        = tl
        self.tr        = tr
        self.colour    = _adjustColour(colour)
        self.lineWidth = lineWidth

    def draw(self):

        verts = np.zeros((8, 3))
        verts[0, :] = self.bl
        verts[1, :] = self.br
        verts[2, :] = self.tl
        verts[3, :] = self.tr
        verts[4, :] = self.bl
        verts[5, :] = self.tl
        verts[6, :] = self.br
        verts[7, :] = self.tr 
        
        gl.glLineWidth(self.lineWidth)
        gl.glBegin(gl.GL_LINES)
        gl.glColor4f(*self.colour)
        for i in range(8):
            gl.glVertex3f(*verts[i])
        gl.glEnd() 


# class Text(object)
# class Grid(objec)t
# class Circle(object) ?
