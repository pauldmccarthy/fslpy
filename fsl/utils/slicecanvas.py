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

vertex_shader = """
#version 120

attribute float rawColour;
varying   vec4  outColour;

void main(void) {

  gl_Position = ftransform();
  outColour   = vec4(rawColour,rawColour,rawColour, 1.0);

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

        self.xax  = dims[0]
        self.yax  = dims[1]
        self.zax  = zax

        self.xdim = image.shape[self.xax]
        self.ydim = image.shape[self.yax]
        self.zdim = image.shape[self.zax]

        if zpos is None:
            zpos = self.zdim / 2

        self._xpos = self.xdim / 2
        self._ypos = self.ydim / 2
        self._zpos = zpos

        # remove this
        dims.insert(0, self.zax)
        image = image.transpose(dims)

        self.image   = image
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

        self.rawColourPos = gl.glGetAttribLocation(self.shaders, 'rawColour')

        nvertices = 4 * self.xdim * self.ydim
        nindices  = 6 * self.xdim * self.ydim

        self.nvertices = nvertices
        self.nindices  = nindices

        geomData = np.zeros((nvertices, 2), dtype=np.float32)

        for xi in range(self.xdim):
            for yi in range(self.ydim):

                off = (xi * self.ydim + yi) * 4

                geomData[off,  :] = [xi,   yi]
                geomData[off+1,:] = [xi+1, yi]
                geomData[off+2,:] = [xi,   yi+1]
                geomData[off+3,:] = [xi+1, yi+1]

        self.geomBuffer = vbo.VBO(geomData, gl.GL_STATIC_DRAW)

        indexData  = np.zeros(nindices, dtype=np.uint32)

        for xi in range(self.xdim):
            for yi in range(self.ydim):

                idxOff  = (xi * self.ydim + yi) * 6
                vertOff = (xi * self.ydim + yi) * 4

                indexData[idxOff:idxOff+6] = np.array([0,1,2,2,1,3])  + vertOff

        self.indexBuffer = vbo.VBO(
            indexData, gl.GL_STATIC_DRAW, gl.GL_ELEMENT_ARRAY_BUFFER)

        self.imageBuffer,_ = self._initImageBuffer()



    def _initImageBuffer(self):
        """
        """

        imageData = np.array(self.image, dtype=np.float32)

        # The image data is normalised to lie between 0.0 and 1.0.
        imageData = (imageData       - imageData.min()) / \
                    (imageData.max() - imageData.min())

        # Finally, we repeat each image value four times,
        # for the four vertices used to represent each voxel.
        imageData = imageData.repeat(4)
        imageData = imageData.reshape(self.zdim * self.nvertices, 1)

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

        imageOffset = self.zpos * self.nvertices

        self.SetCurrent(self.context)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        ###################
        # Draw using custom vertex/fragment shaders
        gl.glUseProgram(self.shaders)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        self.geomBuffer.bind()
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, None)

        self.imageBuffer.bind()
        gl.glVertexAttribPointer(
            self.rawColourPos,
            1,
            gl.GL_FLOAT,
            gl.GL_FALSE,
            0,
            self.imageBuffer + imageOffset*4)
        gl.glEnableVertexAttribArray(self.rawColourPos)

        self.indexBuffer.bind()
        gl.glDrawElements(
            gl.GL_TRIANGLES, self.nindices, gl.GL_UNSIGNED_INT, None)

        gl.glUseProgram(0)
        ###################

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
