#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a 3D numpy array.
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

class SliceCanvas(wxgl.GLCanvas):
    """
    A wx.glcanvas.GLCanvas which may be used to display a single
    2D slice from a 3D numpy array.
    """

    @property
    def index(self):
        """
        The slice currently being displayed.
        """
        return self._index

    @index.setter
    def index(self, index):

        index = int(round(index))

        if   index >= self.nslices: index = self.nslices - 1
        elif index <  0:            index = 0

        self._index = index

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


    def __init__(self, parent, image, axis=0, index=None, **kwargs):

        # reshape the image so the axis being displayed is
        # the first axis.
        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.insert(0, dims.pop(axis))
        image = image.transpose(dims)

        if index is None:
            index = image.shape[0] / 2

        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        self.image   = image
        self.nslices = image.shape[0]
        self.xdim    = image.shape[1]
        self.ydim    = image.shape[2]
        self.axis    = axis

        self._index = index
        self._xpos  = image.shape[1] / 2
        self._ypos  = image.shape[2] / 2

        self.imageBuffer = None
        self.context = wxgl.GLContext(self)

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE,  self.resize)


    def _initGLData(self):

        self.SetCurrent(self.context)

        # Here we are setting up three buffers which will be copied to
        # the GPU memory. A single  slice of M*N voxels is represented
        # by M*(2*N + 4) vertices for reasons which will be explained
        # below.  Every 2D slice of our 3D image has the same geometry,
        # and hence the same number of vertices. So we only need to
        # create geometry information for a single slice, but we can
        # use it to render every slice,.
        nvertices = self.xdim * (2 * self.ydim + 4)

        # The first buffer, indexData/indexBuffer is simply an array
        # of vertex indices (i.e. [0,1,2,3,...,n-1] for n vertices)
        # for a single slice of the image
        indexData = np.arange(nvertices, dtype=np.uint32)

        # The second buffer is an array of colour data, derived from the
        # image data, and consisting of three values (r,g,b) for each
        # vertex. The image data is normalised to lie between 0.0 and 1.0.
        imageData = np.array(self.image, dtype=np.float32)
        imageData = (imageData - imageData.min()) / imageData.max()

        # Duplicate the last value of every column of voxels, on every
        # slice, to take care of that pesky '+ 4' in the number of vertices.
        print 'imageData:  {}'.format(imageData.shape)
        imageData = np.dstack((
            imageData,
            imageData[:,:,-2:].reshape(self.nslices, self.xdim, 2)))

        # Repeat each image value 6 times (2 vertices
        # per voxel * 3 colour values per vertex).

        print 'image:      {}'.format(self.image.shape)
        print 'nslices:    {}'.format(self.nslices)
        print 'nvertices:  {}'.format(nvertices)
        print 'imageData2: {}'.format(imageData.shape)

        imageData = imageData.repeat(6)

        print 'imageData2: {}'.format(imageData.shape)

        imageData = imageData.reshape(self.nslices * nvertices,3)

        # The third bffer is an array of vertices (x/y coordinate pairs),
        # representing the locations of all voxels in a single 2D slice.
        # Using a triangle strip, we can represent each vertical column
        # of N voxels with 2*N + 2 vertices. But in order to link each
        # row together, we need to create some dummy vertices at the
        # end of every row, which OpenGL will interpret as 'degenerate'
        # triangles.
        geomData = np.zeros((nvertices,2), dtype=np.float32)

        for xi in range(self.xdim):

            offset = xi*(nvertices/self.xdim)

            # dummy vertex to generate a degenerate triangle
            if xi > 0:
                geomData[offset, :] = [xi, 0]
                offset = offset + 1

            for yi in range(self.ydim + 1):

                geomData[offset + 2*yi    , :] = [xi,   yi]
                geomData[offset + 2*yi + 1, :] = [xi+1, yi]

            # dummy vertex to generate a degenerate triangle
            if xi < self.xdim-1: geomData[offset + 2*yi + 2, :] = [xi+1, yi-1]


        # Finally, we can tell OpenGL to store this data on the GPU
        self.indexBuffer = vbo.VBO(
            indexData, gl.GL_STATIC_DRAW, gl.GL_ELEMENT_ARRAY_BUFFER)

        self.imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)
        self.geomBuffer  = vbo.VBO(geomData,  gl.GL_STATIC_DRAW)

    def resize(self, ev):

        try:    self.SetCurrent(self.context)
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

        if not self.imageBuffer:
            wx.CallAfter(self._initGLData)
            return

        imageBuf = self.imageBuffer
        geomBuf  = self.geomBuffer
        indexBuf = self.indexBuffer

        nvertices   = self.xdim * (2 * self.ydim + 4)
        imageOffset = self.index * nvertices

        self.SetCurrent(self.context)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        geomBuf.bind()
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, None)
        imageBuf.bind()
        gl.glColorPointer(3, gl.GL_FLOAT, 0, imageBuf + imageOffset*4*3)

        indexBuf.bind()
        gl.glDrawElements(gl.GL_TRIANGLE_STRIP, nvertices, gl.GL_UNSIGNED_INT, None)

        # a vertical line at horizPos, and a horizontal line at vertPos
        x = self.xpos + 0.5
        y = self.ypos  + 0.5
        gl.glBegin(gl.GL_LINES)

        gl.glColor3f(0,1,0)
        gl.glVertex2f(x, 0)
        gl.glVertex2f(x, self.ydim)

        gl.glColor3f(0,1,0)
        gl.glVertex2f(0,         y)
        gl.glVertex2f(self.xdim, y)

        gl.glEnd()

        gl.glUseProgram(0)

        self.SwapBuffers()
