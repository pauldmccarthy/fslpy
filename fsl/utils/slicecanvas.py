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
import OpenGL.GL.shaders as shaders
import OpenGL.arrays.vbo as vbo

# Under OS X, I don't think I can request an OpenGL 3.2 core profile
# - I'm stuck with OpenGL 2.1 I'm using these ARB extensions for
# functionality which is standard in 3.2.
import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi

# A slice is rendered using three buffers. The first buffer,
# the 'geometry buffer' simply contains four vertices, which
# define the geometry of a single voxel (using triangle
# strips).

# The second buffer, the 'position buffer', contains the location
# of every voxel in one slice of the image (these locations are
# identical for every slice of the image, so we can re-use the
# location information for every slice).  The third buffer, the
# 'image buffer' contains data for the entire image, and is used
# to colour each voxel. This image buffer may be shared between
# multiple SliceCanvas objects which are displaying the same
# image - see the 'master' parameter to the SliceCanvas constructor.
#

# The vertex shader positions and colours a single vertex.
vertex_shader = """
#version 120

attribute vec2  inVertex;   /* Current vertex                   */
attribute vec2  inPosition; /* Position of the current voxel    */
attribute float inColour;   /* Value of the current voxel       */
varying   vec4  outColour;  /* Colour, generated from the value */

void main(void) {

    /*
     * Offset the vertex by the current voxel position
     * (and perform standard transformation from data
     * coordinates to screen coordinates).
     */
    gl_Position = gl_ModelViewProjectionMatrix * \
        vec4(inVertex+inPosition, 0.0, 1.0);

    /* Greyscale only for the time being. */
    outColour = vec4(inColour, inColour, inColour, 1.0);
}
"""

# Default fragment shader, does nothing special.
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
        """
        Change the slice being displayed. You need to manually call Refresh().
        """

        zpos = int(round(zpos))

        if   zpos >= self.zdim: zpos = self.zdim - 1
        elif zpos <  0:         zpos = 0

        self._zpos = zpos

    @property
    def xpos(self):
        """
        The current X (horizontal) location of the cursor. 
        """
        return self._xpos

    @xpos.setter
    def xpos(self, xpos):
        """
        Change the x cursor position. You need to manually call Refresh().
        """ 

        xpos = int(round(xpos))

        if   xpos >= self.xdim: xpos = self.xdim - 1
        elif xpos <  0:         xpos = 0

        self._xpos = xpos

    @property
    def ypos(self):
        """
        The current Y (vertical) location of the cursor.
        """
        return self._ypos

    @ypos.setter
    def ypos(self, ypos):
        """
        Change the y cursor position. You need to manually call Refresh().
        """ 

        ypos = int(round(ypos))

        if   ypos >= self.ydim: ypos = self.ydim - 1
        elif ypos <  0:         ypos = 0

        self._ypos = ypos


    def __init__(self, parent, image, zax=0, zpos=None, master=None, **kwargs):
        """
        Creates a canvas object. The OpenGL data buffers are set up in
        _initGLData the first time that the canvas is displayed/drawn.
        Parameters:
        
          parent - WX parent object
          image  - 3D numpy array to be displayed
          zax    - Axis to be displayed (the 'depth' axis), default 0
          zpos   - Initial slice to be displayed. If not provided, the
                   middle slice is used.
          master - Another SliceCanvas object with which to share the
                   GL context and the image buffer data.
        """

        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.pop(zax)

        if master is not None: context = master.context
        else:                  context = wxgl.GLContext(self)

        self.master  = master
        self.context = context

        self.image = image
        self.xax   = dims[1]
        self.yax   = dims[0]
        self.zax   = zax

        self.xdim = self.image.shape[self.xax]
        self.ydim = self.image.shape[self.yax]
        self.zdim = self.image.shape[self.zax]

        dsize = self.image.dtype.itemsize

        self.xstride = self.image.strides[self.xax] / dsize
        self.ystride = self.image.strides[self.yax] / dsize
        self.zstride = self.image.strides[self.zax] / dsize

        if zpos is None:
            zpos = self.zdim / 2

        self._xpos = self.xdim / 2
        self._ypos = self.ydim / 2
        self._zpos = zpos

        # these attributes are created by _initGLData,
        # which is called on the first EVT_PAINT event
        self.geomBuffer     = None
        self.positionBuffer = None
        self.imageBuffer    = None

        self.Bind(wx.EVT_PAINT, self.draw)


    def _initGLData(self):
        """
        Initialises the GL buffers which are  copied to the GPU,
        and used to render the voxel data.
        """

        # A bit hacky. We can only set the GL context (and create
        # the GL data) once something is actually displayed on the
        # screen. The _initGLData method is called (asynchronously)
        # by the draw() method if it sees that the image buffer has
        # not yet been initialised. But draw() may be called more
        # than once before _initGLData is called. Here, to prevent
        # _initGLData from running more than once, the first time it
        # is called it simply overwrites itself with a dummy method.
        self._initGLData = lambda s: s
 
        self.context.SetCurrent(self)

        self.shaders = shaders.compileProgram(
            shaders.compileShader(vertex_shader,   gl.GL_VERTEX_SHADER),
            shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER))

        self.rawVertexPos   = gl.glGetAttribLocation(self.shaders, 'inVertex')
        self.rawColourPos   = gl.glGetAttribLocation(self.shaders, 'inColour')
        self.rawPositionPos = gl.glGetAttribLocation(self.shaders, 'inPosition')

        # Data stored in the geometry buffer. Defines
        # the geometry of a single voxel, rendered as
        # a triangle strip.
        geomData = np.array([0, 0,
                             1, 0,
                             0, 1,
                             1, 1], dtype=np.uint8)

        # Data stored in the position buffer. Defines
        # the location of every voxel in a single slice.
        positionData = np.zeros((self.xdim*self.ydim, 2), dtype=np.uint16)
        xidxs,yidxs  = np.meshgrid(np.arange(self.xdim),
                                   np.arange(self.ydim),
                                   indexing='ij')
        positionData[:,0] = xidxs.ravel()
        positionData[:,1] = yidxs.ravel()

        self.geomBuffer     = vbo.VBO(geomData,     gl.GL_STATIC_DRAW)
        self.positionBuffer = vbo.VBO(positionData, gl.GL_STATIC_DRAW)

        # The image buffer, containing the image data itself
        self.imageBuffer = self._initImageBuffer()


    def _initImageBuffer(self):
        """
        Initialises the buffer used to store the image data. If a 'master'
        canvas was set when this SliceCanvas object was constructed, its
        image buffer is used instead.
        """

        imageData = self.image
        del self.image 

        if self.master is not None:
            return self.master.imageBuffer
 
        # The image data is normalised to lie between 0 and 256
        imageData = 255.0*(imageData       - imageData.min()) / \
                    (imageData.max() - imageData.min())

        # Then cast to uint8
        imageData = np.array(imageData, dtype=np.uint8)

        # and flattened
        imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)

        return imageBuffer


    def resize(self):
        """
        Sets up the GL canvas size, viewport, and
        projection. This method is called by draw().
        """

        try: self.context.SetCurrent(self)
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
        Draws the currently selected slice to the canvas.
        """

        # image data has not been initialised.
        if not self.imageBuffer:
            wx.CallAfter(self._initGLData)
            return

        self.resize()
        self.context.SetCurrent(self)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glUseProgram(self.shaders)

        # We draw each vertical column of voxels one at a time.
        # This is necessary because, in order to allow image
        # buffers to be shared between different SliceCanvas
        # objects, we cannot re-arrange the image data, as
        # stored in GPU memory. So while the memory offset
        # between values in the same column (or row) is 
        # consistent, the offset between columns (rows) is not.
        for xi in range(self.xdim):

            imageOffset = (self.zpos * self.zstride + xi * self.xstride) 
            imageStride = self.ystride 
            posOffset   = xi * self.ydim * 4

            # The geometry buffer, which defines the geometry of a
            # single vertex (4 vertices, drawn as a triangle strip)
            self.geomBuffer.bind()
            gl.glVertexAttribPointer(
                self.rawVertexPos,
                2,
                gl.GL_UNSIGNED_BYTE,
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
                gl.GL_UNSIGNED_SHORT,
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
                gl.GL_UNSIGNED_BYTE,
                gl.GL_TRUE,
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

        # A vertical line at xpos, and a horizontal line at ypos
        x = self.xpos + 0.5
        y = self.ypos + 0.5
        
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex2f(x,         0)
        gl.glVertex2f(x,         self.ydim)
        gl.glVertex2f(0,         y)
        gl.glVertex2f(self.xdim, y)
        gl.glEnd()

        self.SwapBuffers()
