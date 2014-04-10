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

        self.context = wxgl.GLContext(self)

        # these attributes are created by _initGLData,
        # which is called on the first EVT_PAIN event
        self.imageBuffer = None
        self.indexBuffer = None
        self.geomBuffer  = None
        self.nvertices   = 0

        self.Bind(wx.EVT_PAINT, self.draw)
        self.Bind(wx.EVT_SIZE,  self.resize)


    def _initGLData(self):

        self.SetCurrent(self.context)

        # Here we are setting up three buffers which will be copied to
        # the GPU memory - a geometry buffer containing points which
        # will be used to draw each voxel, an index buffer containing
        # identifiers for every point, and an image buffer containing
        # image data which is used to colour each voxel. Every 2D slice
        # of our 3D image has the same geometry, and hence the same
        # number of vertices. So we only need to create geometry and
        # index information for a single slice, but we can use that
        # same information to render every slice.
        #
        # A single slice of M*N voxels is represented by M*2*(N + 1)
        # vertices. For example, this image represents a 4*3 slice,
        # with periods representing vertex locations:
        #
        #  .___..___..___..____.
        #  |    |    |    |    |
        #  .___..___..__ ..____.
        #  |    |    |    |    |
        #  .___..___..___..____.
        #  |    |    |    |    |
        #  .___..___..___..____.
        #
        #
        # Two periods are next to each other (i.e. '..') indicates that
        # those two vertices represent the same point in space. We have
        # to repeat these inner vertices in order to achieve accurate
        # colouring of each voxel.

        nvertices = self.xdim * 2 * (self.ydim + 1)

        # The first buffer is an array of vertices (x/y coordinate
        # pairs), one at every point in our 2D slice. We are drawing
        # each vertical column of voxels one by one, using two
        # triangles to draw each voxel. In order to eliminate the need
        # to specify six vertices for every voxel, and hence to reduce
        # the amount of memory used, we are using a triangle strip to
        # draw each column of voxels. This image depicts a triangle
        # strip used to draw a column of two voxels (periods represent
        # vertex locations).
        #
        #  2.----.
        #     \
        #      \
        #  1.----.
        #     \
        #      \
        #  0.----.
        #   0    1
        #
        # In order to use a single OpenGL call to draw multiple
        # non-contiguous voxel columns, between every column we
        # add a couple of 'dummy' vertices, which will then be
        # interpreted by OpenGL as 'degenerate triangles', and will
        # not be drawn. So in reality, a 4*3 slice would be drawn
        # as follows:
        #
        # 3   .----...----...----...----.
        #       \      \      \      \
        #        \      \      \      \
        # 2   .----. .----. .----. .----.
        #       \      \      \      \
        #        \      \      \      \
        # 1   .----. .----. .----. .----.
        #       \      \      \      \
        #        \      \      \      \
        # 0   .----...----...----...----.
        #
        #     0    1      2      3      4

        nvertices = nvertices + 2 * (self.xdim - 1)
        self.nvertices = nvertices

        # See these links for good overviews of triangle strips and
        # degenerate triangles in OpenGL:
        #
        #  - http://www.learnopengles.com/tag/degenerate-triangles/
        #  - http://en.wikipedia.org/wiki/Triangle_strip

        geomData = np.zeros((nvertices, 2), dtype=np.float32)

        for xi in range(self.xdim):

            xoff = xi * (2*self.ydim + 4)

            # two vertices for each voxel, plus an
            # extra two at the top of each column
            for yi in range(self.ydim + 1):
                verti = xoff + 2*yi
                geomData[verti,  :] = [xi,   yi]
                geomData[verti+1,:] = [xi+1, yi]

            yi = self.ydim

            # vertices for degenerate triangles,
            # between each column of voxels
            if xi < self.xdim - 1:
                verti = xoff + 2*yi
                geomData[verti+2, :] = [xi+1, yi]
                geomData[verti+3, :] = [xi+1, 0]

        # The next buffer is an array of colour data, derived from the
        # image voxel data, and consisting of three values (r,g,b) for
        # each vertex. Ultimately, each voxel is going to be represented
        # by two triangles, using a triangle strip. In OpenGL, when using
        # a flat colouring scheme (i.e. not smoothed/interpolated between
        # vertices), the colour of each triangle is defined by the first
        # vertex which defines that triangle. This, combined with the use
        # of a triangle strip geometry, means that we need to repeat each
        # voxel value twice, once for each triangle which makes up the
        # voxel. We also need to take into account

        imageData = np.array(self.image, dtype=np.float32)

        # The image data is normalised to lie between 0.0 and 1.0.
        imageData = (imageData       - imageData.min()) / \
                    (imageData.max() - imageData.min())

        # Repeat the values at the end of each voxel column, to
        # to take into account one of the two extra vertices at
        # the top of each column. Then, repeat every value in the
        # image, as we have two vertices for every voxel (plus
        # the extra two at the top).
        imageData = np.dstack((imageData, imageData[:,:,-1]))
        imageData = imageData.repeat(2, axis=2)

        # Repeat the values at the end of each voxel column again,
        # to take into account the first degenerate vertex.
        imageData = np.dstack((imageData, imageData[:,:,-1]))

        # Now, to take into account the second degenerate vertex,
        # we take the values at the start of each column, offset them
        # by one column (i.e. the first value of the second column
        # is used as the value for the second degenerate vertex of
        # the first column), and put them on the end of each column.
        degenTwo  = imageData[:,:,0]
        degenTwo  = np.roll(degenTwo, 1, 1)
        imageData = np.dstack((imageData, degenTwo))

        # One final note: the degenerate vertices added above
        # are required to link columns together. Therefore,
        # they are not actually required for the final column.
        # So here, we chop off the last two values of every
        # slice, which correspond to the unneeded values for
        # the final column of each slice..
        imageData = imageData.reshape(self.nslices, nvertices + 2)
        imageData = imageData[:,:-2]

        # Finally, we repeat each image value three times,
        # as colours must be specified by (r,g,b) 3-tuples.
        imageData = imageData.repeat(3)
        imageData = imageData.reshape(self.nslices * nvertices,3)

        # The third buffer, indexData/indexBuffer is simply an array
        # of vertex indices (i.e. [0,1,2,3,...,n-1] for n vertices)
        # for a single slice of the image
        indexData = np.arange(nvertices, dtype=np.uint32)

        # Finally, we can tell OpenGL to store this data on the GPU
        self.indexBuffer = vbo.VBO(
            indexData, gl.GL_STATIC_DRAW, gl.GL_ELEMENT_ARRAY_BUFFER)

        self.imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)
        self.geomBuffer  = vbo.VBO(geomData,  gl.GL_STATIC_DRAW)


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

        if not self.imageBuffer:
            wx.CallAfter(self._initGLData)
            return

        imageBuf = self.imageBuffer
        geomBuf  = self.geomBuffer
        indexBuf = self.indexBuffer

        imageOffset = self.index * self.nvertices

        self.SetCurrent(self.context)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glEnableClientState(gl.GL_COLOR_ARRAY)
        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)

        geomBuf.bind()
        gl.glVertexPointer(2, gl.GL_FLOAT, 0, None)
        imageBuf.bind()
        gl.glColorPointer(3, gl.GL_FLOAT, 0, imageBuf + imageOffset*4*3)

        indexBuf.bind()
        gl.glDrawElements(
            gl.GL_TRIANGLE_STRIP, self.nvertices, gl.GL_UNSIGNED_INT, None)

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
