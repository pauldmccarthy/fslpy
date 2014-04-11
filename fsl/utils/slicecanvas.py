#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a 3D numpy array.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools         as it

import numpy             as np
import                      wx
import wx.glcanvas       as wxgl
import OpenGL.GL         as gl
import OpenGL.GLUT       as glut
import OpenGL.GL.shaders as shaders
import OpenGL.arrays.vbo as vbo


import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi

vertex_shader = """
#version 120

attribute vec2  inVertex;
attribute vec2  inPosition;
attribute float inColour;
varying   vec4  outColour;

void main(void) {

  gl_Position = gl_ModelViewProjectionMatrix * vec4(inVertex+inPosition, 0.0, 1.0);
  outColour   = vec4(inColour, inColour, inColour, 1.0);
}
"""

fragment_shader = """
#version 120

varying vec4 outColour;

void main(void) {
    gl_FragColor = outColour;
}
"""


class SliceCanvas(wxgl.GLCanvas):
    """
    A wx.glcanvas.GLCanvas which may be used to display a single
    2D slice from a 3D numpy array.
    """

    @property
    def zpos(self):
        """
        The slice currently being displayed.
        """
        return self._zpos

    @zpos.setter
    def zpos(self, zpos):

        zpos = int(round(zpos))

        if   zpos >= self.zdim: zpos = self.zdim - 1
        elif zpos <  0:         zpos = 0

        self._zpos = zpos

    @property
    def xpos(self):
        """
        The current X location of the cursor.
        """
        return self._xpos

    @xpos.setter
    def xpos(self, xpos):

        xpos = int(round(xpos))

        if   xpos >= self.xdim: xpos = self.xdim - 1
        elif xpos <  0:         xpos = 0

        self._xpos = xpos

    @property
    def ypos(self):
        """
        The current Y location of the cursor.
        """
        return self._ypos

    @ypos.setter
    def ypos(self, ypos):

        ypos = int(round(ypos))

        if   ypos >= self.ydim: ypos = self.ydim - 1
        elif ypos <  0:         ypos = 0

        self._ypos = ypos


    def __init__(self, parent, image, zax=0, zpos=None, **kwargs):

        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.pop(zax)

        self.image = np.array(image, dtype=np.float32)
        self.xax   = dims[1]
        self.yax   = dims[0]
        self.zax   = zax

        self.xdim = self.image.shape[self.xax]
        self.ydim = self.image.shape[self.yax]
        self.zdim = self.image.shape[self.zax]

        self.xstride = self.image.strides[self.xax] / 4
        self.ystride = self.image.strides[self.yax] / 4
        self.zstride = self.image.strides[self.zax] / 4

        if zpos is None:
            zpos = self.zdim / 2

        self._xpos = self.xdim / 2
        self._ypos = self.ydim / 2
        self._zpos = zpos

        self.context = wxgl.GLContext(self)

        # these attributes are created by _initGLData,
        # which is called on the first EVT_PAINT event
        self.imageBuffer = None
        self.indexBuffer = None
        self.geomBuffer  = None
        self.nvertices   = 0

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE,  self.resize)


    def _initGLData(self):
        """
        """

        self.SetCurrent(self.context)

        self.shaders = shaders.compileProgram(
            shaders.compileShader(vertex_shader,   gl.GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER))

        self.rawVertexPos   = gl.glGetAttribLocation(self.shaders, 'inVertex')
        self.rawColourPos   = gl.glGetAttribLocation(self.shaders, 'inColour')
        self.rawPositionPos = gl.glGetAttribLocation(self.shaders, 'inPosition')

        geomData = np.array([[0, 0,
                              1, 0,
                              0, 1,
                              1, 1]], dtype=np.float32)

        positionData = np.zeros((self.xdim*self.ydim, 2), dtype=np.float32)

        for xi in range(self.xdim):
            for yi in range(self.ydim):

                positionData[xi * self.ydim + yi, 0] = xi
                positionData[xi * self.ydim + yi, 1] = yi

        self.geomBuffer     = vbo.VBO(geomData,     gl.GL_STATIC_DRAW)
        self.positionBuffer = vbo.VBO(positionData, gl.GL_STATIC_DRAW)
        self.imageBuffer,_  = self._initImageBuffer()


    def _initImageBuffer(self):
        """
        """

        imageData = self.image

        # The image data is normalised to lie between 0.0 and 1.0.
        imageData = (imageData       - imageData.min()) / \
                    (imageData.max() - imageData.min())

        # and flattened
        imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)

        return imageBuffer,imageData


    def resize(self, ev):

        try: self.SetCurrent(self.context)
        except: return
        size = self.GetSize()

        # set up 2D drawing
        gl.glViewport(0, 0, size.width, size.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.xdim, 0, self.ydim, 0, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()


    def draw(self, ev):
        """
        """

        if not self.imageBuffer:
            wx.CallAfter(self._initGLData)
            return

        self.SetCurrent(self.context)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glUseProgram(self.shaders)

        for xi in range(self.xdim):

            imageOffset = (self.zpos * self.zstride + xi * self.xstride) * 4
            imageStride = self.ystride * 4
            posOffset   = xi * self.ydim * 8

            # The geometry buffer, which defines the geometry of a
            # single vertex (4 vertices, drawn as a triangle strip)
            self.geomBuffer.bind()
            gl.glVertexAttribPointer(
                self.rawVertexPos,
                2,
                gl.GL_FLOAT,
                gl.GL_FALSE,
                0,
                None)
            gl.glEnableVertexAttribArray(self.rawVertexPos)
            arbia.glVertexAttribDivisorARB(self.rawVertexPos, 0)

            # The position buffer, which defines
            # the location of every voxel
            self.positionBuffer.bind()
            gl.glVertexAttribPointer(
                self.rawPositionPos,
                2,
                gl.GL_FLOAT,
                gl.GL_FALSE,
                0,
                self.positionBuffer + posOffset)
            gl.glEnableVertexAttribArray(self.rawPositionPos)
            arbia.glVertexAttribDivisorARB(self.rawPositionPos, 1)

            # The image buffer, which defines
            # the value at each voxel.
            self.imageBuffer.bind()
            gl.glVertexAttribPointer(
                self.rawColourPos,
                1,
                gl.GL_FLOAT,
                gl.GL_FALSE,
                imageStride,
                self.imageBuffer + imageOffset)

            gl.glEnableVertexAttribArray(self.rawColourPos)
            arbia.glVertexAttribDivisorARB(self.rawColourPos, 1)

            # Draw all of the triangles!
            arbdi.glDrawArraysInstancedARB(
                gl.GL_TRIANGLE_STRIP, 0, 4, self.ydim)
            
            gl.glDisableVertexAttribArray(self.rawVertexPos)
            gl.glDisableVertexAttribArray(self.rawPositionPos)
            gl.glDisableVertexAttribArray(self.rawColourPos)

        gl.glUseProgram(0)

        # a vertical line at horizPos, and a horizontal line at vertPos
        x = self.xpos + 0.5
        y = self.ypos + 0.5
        gl.glBegin(gl.GL_LINES)

        gl.glColor3f(0,1,0)
        gl.glVertex2f(x, 0)
        gl.glVertex2f(x, self.ydim)

        gl.glColor3f(0,1,0)
        gl.glVertex2f(0,         y)
        gl.glVertex2f(self.xdim, y)

        gl.glEnd()

        self.SwapBuffers()
