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
import OpenGL.GLUT       as glut
import OpenGL.GL.shaders as shaders
import OpenGL.arrays.vbo as vbo


# TODO could store raw slice data/indices, and
# calculate posiiton/colour here in the shader.
vertex_shader   = """
#version 120

attribute vec2 inPosition;
attribute vec3 inColor;

varying   vec3 outColor;

void main() {
    gl_Position = vec4(inPosition, 0.0, 1.0);
    outColor    = inColor;
}
"""

fragment_shader = """
#version 120

varying vec3 outColor;

void main() {
    gl_FragColor = vec4(outColor, 1.0);
}
"""

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
        self.xdim   = image.shape[0]
        self.ydim   = image.shape[1]
        self.axis   = axis

        self._index    = index
        self._horizPos = image.shape[0] / 2
        self._vertPos  = image.shape[1] / 2

        self.indexBuffers  = None
        self.geomBuffers   = None
        self.colourBuffers = None

        self.context = wxgl.GLContext(self)

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE,  self.resize)


    def _initGLData(self):

        self.SetCurrent(self.context)

#        self.shader = shaders.compileProgram(
#            shaders.compileShader(vertex_shader,   gl.GL_VERTEX_SHADER),
#            shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER))

#        self.geomLocation   = gl.glGetAttribLocation(self.shader, 'inPosition')
#        self.colourLocation = gl.glGetAttribLocation(self.shader, 'inColor')

        nslices = self.image.shape[2]

        self.geomBuffers   = []
        self.colourBuffers = []
        self.indexBuffers  = []

        for i in range(nslices):

            print 'slice {}'.format(i)

            sliceGeom   = np.zeros((self.xdim*self.ydim*6,2), dtype=np.float32)
            sliceColour = np.zeros((self.xdim*self.ydim*6,3), dtype=np.float32)
            sliceIndex  = np.arange(self.xdim*self.ydim*6,    dtype=np.uint32)

            for xi in range(self.xdim):
                for yi in range(self.ydim):

                    offset = (xi*self.ydim + yi)*6

                    sliceGeom[offset,     :] = [xi,   yi+1]
                    sliceGeom[offset + 1, :] = [xi,   yi]
                    sliceGeom[offset + 2, :] = [xi+1, yi]
                    sliceGeom[offset + 3, :] = [xi+1, yi]
                    sliceGeom[offset + 4, :] = [xi+1, yi+1]
                    sliceGeom[offset + 5, :] = [xi,   yi+1]

                    colour = self.image[xi,yi,i] / float(self.max)
                    sliceColour[offset:offset+6,:] = colour

                    #sliceColour[offset  :offset+3,:] = [1.0,0.0,0.0]
                    #sliceColour[offset+3:offset+6,:] = [0.0,1.0,0.0]

                    #print xi,yi,offset


            geomVBO   = vbo.VBO(sliceGeom,   gl.GL_STATIC_DRAW)
            colourVBO = vbo.VBO(sliceColour, gl.GL_STATIC_DRAW)
            indexVBO  = vbo.VBO(sliceIndex,  gl.GL_STATIC_DRAW, gl.GL_ELEMENT_ARRAY_BUFFER)

            self.geomBuffers  .append(geomVBO)
            self.colourBuffers.append(colourVBO)
            self.indexBuffers .append(indexVBO)


    def resize(self, ev):

        self.SetCurrent(self.context)
        size = self.GetSize()

        # set up 2D drawing
        gl.glViewport(0, 0, size.width, size.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0, self.xdim, 0, self.ydim, 0, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()


    def draw(self, ev):

        if not self.geomBuffers:
            wx.CallAfter(self._initGLData)
            return

        print 'paint'

        geomBuf   = self.geomBuffers  [self._index]
        colourBuf = self.colourBuffers[self._index]
        indexBuf  = self.indexBuffers [self._index]

        self.SetCurrent(self.context)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
#        gl.glUseProgram(self.shader)

        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        geomBuf.bind()#gl.glBindBuffer(gl.GL_ARRAY_BUFFER, geomBuf)
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, None)
        # gl.glVertexAttribPointer(
        #     self.geomLocation,
        #     2,
        #     gl.GL_FLOAT,
        #     gl.GL_FALSE,
        #     0,
        #     None)
        # gl.glEnableVertexAttribArray(self.geomLocation)

        colourBuf.bind()# gl.glBindBuffer(gl.GL_ARRAY_BUFFER, colourBuf)
        gl.glColorPointer(3, gl.GL_FLOAT, 0, None)
        # gl.glVertexAttribPointer(
        #     self.colourLocation,
        #     3,
        #     gl.GL_FLOAT,
        #     gl.GL_FALSE,
        #     0,
        #     None)
        # gl.glEnableVertexAttribArray(self.colourLocation)

        indexBuf.bind() #gl.glBindBuffer(gl.GL_ELEMENT_ARRAY_BUFFER, indexBuf)
        gl.glDrawElements(gl.GL_TRIANGLES, self.xdim*self.ydim*6, gl.GL_UNSIGNED_INT, None)

        # 3 a vertical line at horizPos
        x = self.horizPos
        gl.glColor3f(0,1,0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(x, 0)
        gl.glVertex2f(x, self.ydim)
        gl.glEnd()

        # # and a horizontal line at vertPos
        y = self.vertPos
        gl.glColor3f(0,1,0)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex2f(0,         y)
        gl.glVertex2f(self.xdim, y)
        gl.glEnd()

        self.SwapBuffers()
