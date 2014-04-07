#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy             as np
import                      wx
import wx.glcanvas       as wxgl
import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

vertex_shader   = 'void main() { gl_Position = gl_Vertex; }'
fragment_shader = 'void main() { gl_FragColor = vec4(1,1,0,1); }'

class SliceCanvas(wxgl.GLCanvas):

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index):
        self._index = index

    @property
    def horizPos(self):
        return self._horizPos

    @horizPos.setter
    def horizPos(self, horizPos):
        self._horizPos = horizPos

    @property
    def vertPos(self):
        return self._vertPos

    @vertPos.setter
    def vertPos(self, vertPos):
        self._vertPos = vertPos

    def __init__(self, parent, image, axis=0, index=None, **kwargs):

        # reshape the image so the axis being displayed is
        # the last, or 'z' axis.
        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.append(dims.pop(axis))
        image = image.transpose(dims)

        if index is None:
            index = image.shape[2] / 2

        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        self.image  = image
        self.min    = image.min()
        self.max    = image.max()
        self.xdim   = dims[0]
        self.ydim   = dims[1]
        self.axis   = axis

        self._index    = index
        self._horizPos = image.shape[0] / 2
        self._vertPos  = image.shape[1] / 2

        self.vboBuffers = None

        self.context = wxgl.GLContext(self)

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE,  self.resize)


    def _genSliceBuffers(self):

        nslices = self.image.shape[2]
        data    = self.image[:,:,self.index]

        self.vboBuffers = []
        for i in range(nslices):

            print 'slice {}'.format(i)

            # a big array containing four vertices,
            # which specify a square for each voxel
            sliceData = np.zeros((self.xdim*self.ydim,2), dtype=np.float32)
            for xi in range(self.xdim):
                for yi in range(self.ydim):

                    # TODO colour
                    c = (data[xi,yi] - self.min) / float(self.max)

                    sliceData[xi*yi,0] = xi + 0.5
                    sliceData[xi*yi,1] = yi + 0.5

            self.SetCurrent(self.context)
            vboBuffer = vbo.VBO(sliceData)
            self.vboBuffers.append(vboBuffer)


    def resize(self, ev):

        size = self.GetClientSize()
        self.SetCurrent(self.context)

        # set up 2D drawing
        gl.glViewport(0, 0, size.width, size.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0.0, self.xdim, 0.0, self.ydim, 0.0, 1.0)


    def draw(self, ev):

        if self.vboBuffers is None:
            wx.CallAfter(self._genSliceBuffers)
            return

        screenx,screeny = self.GetClientSize()
        datax,  datay   = self.image.shape[0:-1]

        vboBuf = self.vboBuffers[self.index]

        self.SetCurrent(self.context)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # draw the current slice
        gl.glColor(1,1,0)
        vboBuf.bind()

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, vboBuf)
        gl.glDrawArrays(gl.GL_POINTS, 0, datax*datay)


        # 3 a vertical line at horizPos
        # x = self.horizPos * screenx / float(datax)
        # gl.glColor3f(0,1,0)
        # gl.glBegin(gl.GL_LINES)
        # gl.glVertex2f(x, 0)
        # gl.glVertex2f(x, screeny)
        # gl.glEnd()

        # # and a horizontal line at vertPos
        # y = self.vertPos * screeny / float(datay)
        # gl.glColor3f(0,1,0)
        # gl.glBegin(gl.GL_LINES)
        # gl.glVertex2f(0,       y)
        # gl.glVertex2f(screenx, y)
        # gl.glEnd()

        self.SwapBuffers()
