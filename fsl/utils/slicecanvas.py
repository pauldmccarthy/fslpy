#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools         as it

import numpy             as np
import matplotlib.colors as mplcolors
import matplotlib.cm     as mplcm

import                      wx
import wx.glcanvas       as wxgl

import OpenGL.GL         as gl
import OpenGL.GL.shaders as shaders
import OpenGL.arrays.vbo as vbo

# Under OS X, I don't think I can request an OpenGL 3.2 core profile
# using wx - I'm stuck with OpenGL 2.1 I'm using these ARB extensions
# for functionality which is standard in 3.2.
import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi

import fsl.data.fslimage as fslimage

# A slice is rendered using three buffers and one texture. The first
# buffer, the 'geometry buffer' simply contains four vertices, which
# define the geometry of a single voxel (using triangle strips).

# The second buffer, the 'position buffer', contains the location of
# every voxel in one slice of the image (these locations are identical
# for every slice of the image, so we can re-use the location
# information for every slice).

# The third buffer, the 'image buffer' contains the image data itself,
# scaled to lie between 0.0 and 1.0. It is used to calculate voxel
# colours, and may be shared between multiple SliceCanvas objects
# which are displaying the same image.
#
# Finally, the texture, the 'colour buffer', is used to store a
# lookup table containing colours. 


# The vertex shader positions and colours a single vertex.
vertex_shader = """
#version 120

uniform   float alpha;          /* Opacity - constant for a whole image          */

attribute vec2  inVertex;       /* Current vertex                                */
attribute vec2  inPosition;     /* Position of the current voxel                 */
attribute float voxelValue;     /* Value of the current voxel (in range [0,1])   */

varying   float fragVoxelValue; /* Voxel value passed through to fragment shader */ 

void main(void) {

    /*
     * Offset the vertex by the current voxel position
     * (and perform standard transformation from data
     * coordinates to screen coordinates).
     */
    gl_Position = gl_ModelViewProjectionMatrix * \
        vec4(inVertex+inPosition, 0.0, 1.0);

    /* Pass the voxel value through to the shader. */
    fragVoxelValue = voxelValue;
}
"""


# Fragment shader. Given the current voxel value, looks
# up the appropriate colour in the colour buffer.
fragment_shader = """
#version 120

uniform float     alpha; 
uniform sampler1D colourMap;      /* RGB colour map, stored as a 1D texture */
varying float     fragVoxelValue;

void main(void) {

    vec4  voxTexture = texture1D(colourMap, fragVoxelValue);
    vec3  voxColour  = voxTexture.rgb;
    float voxAlpha   = voxTexture.a;

    if (voxAlpha > alpha) {
        voxAlpha = alpha;
    }

    gl_FragColor = vec4(voxColour, voxAlpha);
}
"""


class SliceCanvas(wxgl.GLCanvas):
    """
    A wx.glcanvas.GLCanvas which may be used to display a single
    2D slice from a 3D image (see fsl.data.fslimage.Image).
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
        Change the slice being displayed. You will need to manually call
        Refresh() after changing the zpos.
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
        Change the x cursor position. You will need to manually call
        Refresh() after changing the xpos.
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
        Change the y cursor position. You will need to manually call
        Refresh() after changing the ypos.
        """ 

        ypos = int(round(ypos))

        if   ypos >= self.ydim: ypos = self.ydim - 1
        elif ypos <  0:         ypos = 0

        self._ypos = ypos


    @property
    def colourResolution(self):
        """
        Total number of possible colours that will be used when rendering
        a slice.
        """
        return self._colourResolution

    @colourResolution.setter
    def colourResolution(self, colourResolution):
        """
        Updates the colour resolution. You will need to manually call
        updateColourBuffer(), and then Refresh(), after changing the
        colour resolution.
        """

        if colourResolution <= 0:    return
        if colourResolution >  4096: return # this upper limit is arbitrary.
        
        self._colourResolution = colourResolution


    def __init__(
            self, parent, image, zax=0, zpos=None, context=None, **kwargs):
        """
        Creates a canvas object. The OpenGL data buffers are set up in
        _initGLData the first time that the canvas is displayed/drawn.
        Parameters:
        
          parent - WX parent object
        
          image  - A fsl.data.fslimage.Image object, or a
                   fsl.data.fslimage.ImageDisplay object, or a 3D numpy
                   array.
        
          zax    - Axis perpendicular to the plane to be displayed
                   (the 'depth' axis), default 0.

          context - 
        
          zpos   - Initial slice to be displayed. If not provided, the
                   middle slice is used.
        """

        realImage    = None
        imageDisplay = None

        if isinstance(image, fslimage.ImageDisplay):
            realImage    = image.image
            imageDisplay = image
            
        elif isinstance(image, fslimage.Image):
            realImage    = image
            imageDisplay = fslimage.ImageDisplay(image)

        elif isinstance(image, np.ndarray):
            realImage    = fslimage.Image(image)
            imageDisplay = fslimage.ImageDisplay(realImage)
        
        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        if context is None: context = wxgl.GLContext(self)

        self.context = context

        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.pop(zax)

        self.image        = realImage
        self.imageDisplay = imageDisplay
        self.xax          = dims[0]
        self.yax          = dims[1]
        self.zax          = zax

        self.xdim = self.image.data.shape[self.xax]
        self.ydim = self.image.data.shape[self.yax]
        self.zdim = self.image.data.shape[self.zax]

        dsize = self.image.data.dtype.itemsize

        self.xstride = self.image.data.strides[self.xax] / dsize
        self.ystride = self.image.data.strides[self.yax] / dsize
        self.zstride = self.image.data.strides[self.zax] / dsize

        if zpos is None:
            zpos = self.zdim / 2

        self._xpos = self.xdim / 2
        self._ypos = self.ydim / 2
        self._zpos = zpos

        self._colourResolution = 256

        # This flag is set by the _initGLData method
        # when it has finished initialising the OpenGL
        # data buffers
        self.glReady = False

        self.Bind(wx.EVT_PAINT, self.draw)

        # Add a bunch of listeners to the image display
        # object, so we can update the view when image
        # display properties are changed.
        def refreshNeeded(*a):
            self.Refresh()
            
        def colourUpdateNeeded(*a):
            self.updateColourBuffer()
            self.Refresh()

        lnrName = 'SliceCanvas_{{}}_{}'.format(id(self))

        self.imageDisplay.addListener(
            'alpha', lnrName.format('alpha'), refreshNeeded)
        
        self.imageDisplay.addListener(
            'displayMin', lnrName.format('displayMin'), colourUpdateNeeded)
        
        self.imageDisplay.addListener(
            'displayMax', lnrName.format('displayMax'), colourUpdateNeeded)
        
        self.imageDisplay.addListener(
            'rangeClip', lnrName.format('rangeClip'), colourUpdateNeeded)
        
        self.imageDisplay.addListener(
            'cmap', lnrName.format('cmap'), colourUpdateNeeded) 


    def _initGLData(self):
        """
        Initialises the GL buffers which are copied to the GPU,
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

        # Indices of all vertex/fragment shader parameters 
        self.inVertexPos   = gl.glGetAttribLocation( self.shaders, 'inVertex')
        self.voxelValuePos = gl.glGetAttribLocation( self.shaders, 'voxelValue')
        self.inPositionPos = gl.glGetAttribLocation( self.shaders, 'inPosition')
        self.alphaPos      = gl.glGetUniformLocation(self.shaders, 'alpha')
        self.colourMapPos  = gl.glGetUniformLocation(self.shaders, 'colourMap')

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
        yidxs,xidxs  = np.meshgrid(np.arange(self.ydim),
                                   np.arange(self.xdim),
                                   indexing='ij')
        positionData[:,0] = xidxs.ravel()
        positionData[:,1] = yidxs.ravel()

        self.geomBuffer     = vbo.VBO(geomData,     gl.GL_STATIC_DRAW)
        self.positionBuffer = vbo.VBO(positionData, gl.GL_STATIC_DRAW)

        # The image buffer, containing the image data itself
        self.imageBuffer = self._initImageBuffer()

        # The colour buffer, containing a map of
        # colours (stored on the GPU as a 1D texture)
        self.colourBuffer = gl.glGenTextures(1)
        self.updateColourBuffer()

        self.glReady = True

        
    def _initImageBuffer(self):
        """
        Initialises the buffer used to store the image data. If a 'master'
        canvas was set when this SliceCanvas object was constructed, its
        image buffer is used instead.
        """

        # If a master canvas was passed to the
        # constructor, let's share its image data.
        if self.image.glBuffer is not None:
            return self.image.glBuffer

        # The image data is cast to single precision floating
        # point, and normalised to lie between 0.0 and 1.0
        imageData = np.array(self.image.data, dtype=np.float32)
        imageData = (imageData       - imageData.min()) / \
                    (imageData.max() - imageData.min())

        # Then flattened, with fortran dimension ordering,
        # so the data, as stored on the GPU, has its first
        # dimension as the fastest changing.
        imageData = imageData.ravel(order='F')
        imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)

        self.image.glBuffer = imageBuffer

        return imageBuffer


    def updateColourBuffer(self):
        """
        Regenerates the colour buffer used to colour a slice. After
        calling this method, you will need to call Refresh() for the
        change to take effect.
        """

        iDisplay = self.imageDisplay

        # Here we are creating a range of values to be passed
        # to the matplotlib.colors.Colormap instance of the
        # image display. We scale this range such that data
        # values which lie outside the configured display range
        # will map to values below 0.0 or above 1.0. It is
        # assumed that the Colormap instance is configured to
        # generate appropriate colours for these out-of-range
        # values.
        
        normalRange = np.linspace(0.0, 1.0, self.colourResolution)
        normalStep  = 1.0 / (self.colourResolution - 1) 

        normMin = (iDisplay.displayMin - iDisplay.dataMin) / \
                  (iDisplay.dataMax    - iDisplay.dataMin)
        normMax = (iDisplay.displayMax - iDisplay.dataMin) / \
                  (iDisplay.dataMax    - iDisplay.dataMin)

        newStep  = normalStep / (normMax - normMin)
        newRange = (normalRange - normMin) * (newStep / normalStep)

        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map (see fsl.data.fslimage.Image)
        colourmap = iDisplay.cmap(newRange)
        
        # The colour data is stored on
        # the GPU as 8 bit rgb triplets
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.colourBuffer)
        gl.glTexParameteri(
            gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(
            gl.GL_TEXTURE_1D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(
            gl.GL_TEXTURE_1D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE) 
        
        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        self.colourResolution,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        colourmap)

        
    def resize(self):
        """
        Sets up the GL canvas size, viewport, and
        projection. This method is called by draw(),
        so does not need to be called manually.
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
        if not self.glReady:
            wx.CallAfter(self._initGLData)
            return

        self.resize()
        self.context.SetCurrent(self)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glUseProgram(self.shaders)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # Set up the colour buffer
        gl.glEnable(gl.GL_TEXTURE_1D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.colourBuffer)
        gl.glUniform1i(self.colourMapPos, 0) 
         
        gl.glUniform1f(self.alphaPos, self.imageDisplay.alpha)

        # We draw each horizontal row of voxels one at a time.
        # This is necessary because, in order to allow image
        # buffers to be shared between different SliceCanvas
        # objects, we cannot re-arrange the image data, as
        # stored in GPU memory. So while the memory offset
        # between values in the same row (or column) is 
        # consistent, the offset between rows (columns) is
        # not. And drawing rows seems to be faster than
        # drawing columns, for reasons unknown to me.
        for yi in range(self.ydim):

            imageOffset = self.zpos * self.zstride + yi * self.ystride
            imageStride = self.xstride 
            posOffset   = yi * self.xdim * 4

            # The geometry buffer, which defines the geometry of a
            # single vertex (4 vertices, drawn as a triangle strip)
            self.geomBuffer.bind()
            gl.glVertexAttribPointer(
                self.inVertexPos,
                2,
                gl.GL_UNSIGNED_BYTE,
                gl.GL_FALSE,
                0,
                None)
            gl.glEnableVertexAttribArray(self.inVertexPos)
            arbia.glVertexAttribDivisorARB(self.inVertexPos, 0)

            # The position buffer, which defines
            # the location of every voxel
            self.positionBuffer.bind()
            gl.glVertexAttribPointer(
                self.inPositionPos,
                2,
                gl.GL_UNSIGNED_SHORT,
                gl.GL_FALSE,
                0,
                self.positionBuffer + posOffset)
            gl.glEnableVertexAttribArray(self.inPositionPos)
            arbia.glVertexAttribDivisorARB(self.inPositionPos, 1)

            # The image buffer, which defines
            # the colour value at each voxel.
            self.imageBuffer.bind()
            gl.glVertexAttribPointer(
                self.voxelValuePos,
                1,
                gl.GL_FLOAT,
                gl.GL_FALSE,
                imageStride*4,
                self.imageBuffer + imageOffset*4)

            gl.glEnableVertexAttribArray(self.voxelValuePos)
            arbia.glVertexAttribDivisorARB(self.voxelValuePos, 1)

            # Draw all of the triangles!
            arbdi.glDrawArraysInstancedARB(
                gl.GL_TRIANGLE_STRIP, 0, 4, self.xdim)
            
            gl.glDisableVertexAttribArray(self.inVertexPos)
            gl.glDisableVertexAttribArray(self.inPositionPos)
            gl.glDisableVertexAttribArray(self.voxelValuePos)
            gl.glDisable(gl.GL_TEXTURE_1D)

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
