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

    def __init__(self, xyz, width, height, colour, lineWidth=1):
        self.xyz       = xyz
        self.width     = width
        self.height    = height
        self.colour    = _adjustColour(colour)
        self.lineWidth = lineWidth

    def draw(self):

        x, y, z = self.xyz
        width   = self.width
        height  = self.height

        verts = np.zeros((8, 3))
        verts[:, 2] = z

        # left line
        verts[0, 0] = x
        verts[0, 1] = y
        verts[1, 0] = x
        verts[1, 1] = y + height

        # right line
        verts[2, 0] = x + width
        verts[2, 1] = y
        verts[3, 0] = x + width
        verts[3, 1] = y + height

        # bottom line
        verts[4, 0] = x
        verts[4, 1] = y
        verts[5, 0] = x + width
        verts[5, 1] = y

        # top line
        verts[6, 0] = x
        verts[6, 1] = y + height
        verts[7, 0] = x + width
        verts[7, 1] = y + height
        
        gl.glLineWidth(self.lineWidth)
        gl.glBegin(gl.GL_LINES)
        gl.glColor4f(*self.colour)
        for i in range(8):
            gl.glVertex3f(*verts[i])
        gl.glEnd() 


# class Text(object)
# class Grid(objec)t
# class Circle(object) ?
