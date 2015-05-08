#!/usr/bin/env python
#
# glroutines.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL as gl


def show2D(
        xax,
        yax,
        width,
        height,
        zpos,
        lo,
        hi):

    zax = 3 - xax - yax

    xmin, xmax = lo[xax], hi[xax]
    ymin, ymax = lo[yax], hi[yax]
    zmin, zmax = lo[zax], hi[zax]

    gl.glViewport(0, 0, width, height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()

    gl.glOrtho(xmin, xmax, ymin, ymax, zmin - 1, zmax + 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()

    # Rotate world space so the displayed slice
    # is visible and correctly oriented
    # TODO There's got to be a more generic way
    # to perform this rotation. This will break
    # if I add functionality allowing the user
    # to specifty the x/y axes on initialisation. 
    if zax == 0:
        gl.glRotatef(-90, 1, 0, 0)
        gl.glRotatef(-90, 0, 0, 1)
    elif zax == 1:
        gl.glRotatef(270, 1, 0, 0)

    trans = [0, 0, 0]
    trans[zax] = -zpos
    gl.glTranslatef(*trans) 
