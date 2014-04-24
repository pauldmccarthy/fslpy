#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a collection of 3D images.
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


class GLImageData(object):
    """
    A GLImageData object encapsulates the OpenGL information necessary
    to render an image.
    
    A slice from one image is rendered using three buffers and one
    texture. The first buffer, the 'geometry buffer' simply contains four
    vertices, which define the geometry of a single voxel (using triangle
    strips).

    The second buffer, the 'position buffer', contains the location of every
    voxel in one slice of the image (these locations are identical for every
    slice of the image, so we can re-use the location information for every
    slice). The four vertices for each voxel (from the geometry buffer, above)
    are offset by the voxel position, which is read from this position buffer.

    The third buffer, the 'image buffer' contains the image data itself,
    scaled to lie between 0 and 255. It is used to calculate voxel colours.

    Finally, the texture, the 'colour buffer', is used to store a lookup table
    containing colours.
    """
    
    def __init__(self, image, canvas):
        """
        Parameters.
        """

        self.image          = image
        self.canvas         = canvas
        
        self.imageBuffer    = None
        self.colourBuffer   = None
        self.positionBuffer = None
        self.geomBuffer     = None

        # Here, x,y, and z refer to screen
        # coordinates, not image coordinates:
        #   - x: horizontal
        #   - y: vertical
        #   - z: depth
        
        self.xdim = image.shape[ canvas.xax]
        self.ydim = image.shape[ canvas.yax]
        self.zdim = image.shape[ canvas.zax]

        self.xlen = image.pixdim[canvas.xax]
        self.ylen = image.pixdim[canvas.yax]
        self.zlen = image.pixdim[canvas.zax]

        dsize = image.data.dtype.itemsize

        self.xstride = image.data.strides[canvas.xax] / dsize
        self.ystride = image.data.strides[canvas.yax] / dsize
        self.zstride = image.data.strides[canvas.zax] / dsize

        # Maximum number of colours used to draw image data
        self.colourResolution = 256

        self.initGLImageData()


    def initGLImageData(self):
        """
        Creates and initialises the OpenGL data for the given fslimage.Image
        object. The GL data (a GLImageData object - see the top of this
        module) is added as an attribute of the image.
        """

        image = self.image

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

        geomBuffer     = vbo.VBO(geomData,     gl.GL_STATIC_DRAW)
        positionBuffer = vbo.VBO(positionData, gl.GL_STATIC_DRAW)

        # The image buffer, containing the image data itself
        imageBuffer = self.initImageBuffer()

        # The colour buffer, containing a map of
        # colours (stored on the GPU as a 1D texture)
        colourBuffer = gl.glGenTextures(1)

        self.geomBuffer     = geomBuffer
        self.positionBuffer = positionBuffer
        self.imageBuffer    = imageBuffer
        self.colourBuffer   = colourBuffer

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.configDisplayListeners()

        # Create the colour buffer for the given image
        self.updateColourBuffer()

        
    def initImageBuffer(self):
        """
        Initialises the OpenGL buffer used to store the data for the given
        image. The buffer is stored as an attribute of the image and, if it
        has already been created (e.g. by another SliceCanvas object), the
        existing buffer is returned.
        """

        image = self.image

        try:    imageBuffer = image.getAttribute('glBuffer')
        except: imageBuffer = None

        if imageBuffer is not None:
            return imageBuffer

        # The image data is normalised to lie
        # between 0 and 256, and cast to uint8
        imageData = np.array(image.data, dtype=np.float32)
        imageData = 255.0*(imageData       - imageData.min()) / \
                          (imageData.max() - imageData.min())
        imageData = np.array(imageData, dtype=np.uint8)

        # Then flattened, with fortran dimension ordering,
        # so the data, as stored on the GPU, has its first
        # dimension as the fastest changing.
        imageData = imageData.ravel(order='F')
        imageBuffer = vbo.VBO(imageData, gl.GL_STATIC_DRAW)

        image.setAttribute('glBuffer', imageBuffer)

        return imageBuffer


    def configDisplayListeners(self):
        """
        Adds a bunch of listeners to the fslimage.ImageDisplay object
        (accessible as an attribute of the given image called 'display'),
        whcih defines how the given image is to be displayed. This is done
        so we can refresh the image view when image display properties are
        changed. 
        """

        def refreshNeeded(*a):
            """
            The view just needs to be refreshed (e.g. the alpha property
            has changed).
            """
            self.canvas.Refresh()

        def colourUpdateNeeded(*a):
            """
            The colour map for this image needs to be recreated (e.g. the
            colour map has been changed).
            """
            self.updateColourBuffer()
            self.canvas.Refresh()

        display           = self.image.display
        lnrName           = 'SliceCanvas_{{}}_{}'.format(id(self))
        refreshProps      = ['alpha', 'enabled']
        colourUpdateProps = ['displayMin', 'displayMax', 'rangeClip', 'cmap']

        for prop in refreshProps:
            display.addListener(prop, lnrName.format(prop), refreshNeeded)

        for prop in colourUpdateProps:
            display.addListener(prop, lnrName.format(prop), colourUpdateNeeded)


    def updateColourBuffer(self):
        """
        Regenerates the colour buffer used to colour a slice of the
        specified image. 
        """

        display      = self.image.display
        colourBuffer = self.colourBuffer

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

        normMin = (display.displayMin - display.dataMin) / \
                  (display.dataMax    - display.dataMin)
        normMax = (display.displayMax - display.dataMin) / \
                  (display.dataMax    - display.dataMin)

        newStep  = normalStep / (normMax - normMin)
        newRange = (normalRange - normMin) * (newStep / normalStep)

        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map (see fsl.data.fslimage.Image)
        colourmap = display.cmap(newRange)
        
        # The colour data is stored on
        # the GPU as 8 bit rgb triplets
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        gl.glBindTexture(gl.GL_TEXTURE_1D, colourBuffer)
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
    A wx.glcanvas.GLCanvas which may be used to display a single 2D slice from
    a collection of 3D images (see fsl.data.fslimage.ImageList).
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

#        if   zpos >= self.zdim: zpos = self.zdim - 1
#        elif zpos <  0:         zpos = 0

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

#        if   xpos >= self.xdim: xpos = self.xdim - 1
#        elif xpos <  0:         xpos = 0

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

#        if   ypos >= self.ydim: ypos = self.ydim - 1
#        elif ypos <  0:         ypos = 0

        self._ypos = ypos


    def __init__(
            self, parent, imageList, zax=0, zpos=None, context=None, **kwargs):
        """
        Creates a canvas object. The OpenGL data buffers are set up in
        _initGLData the first time that the canvas is displayed/drawn.
        Parameters:
        
          parent    - WX parent object
        
          imageList - a fslimage.ImageList object.
        
          zax       - Axis perpendicular to the plane to be displayed
                      (the 'depth' axis), default 0.

          context   - wx.glcanvas.GLContext object. If None, one is created.
        
          zpos      - Initial slice to be displayed. If not provided, the
                      middle slice is used.
        """

        wxgl.GLCanvas.__init__(self, parent, **kwargs)

        self.name = 'SliceCanvas_{}'.format(id(self))

        # Use the provided shared GL
        # context, or create a new one
        if context is None: self.context = wxgl.GLContext(self)
        else:               self.context = context

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance') 

        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. Allow the caller to specify which
        # axes should be horizontal/vertical.
        dims = range(3)
        dims.pop(zax)

        self.imageList = imageList
        self.xax       = dims[0]
        self.yax       = dims[1]
        self.zax       = zax
        # This flag is set by the _initGLData method when it
        # has finished initialising the OpenGL data buffers
        self.glReady = False

        # All the work is done by the draw method
        self.Bind(wx.EVT_PAINT, self.draw)

        # TODO Fix these numbers
        self._xpos = 200
        self._ypos = 200
        self._zpos = 200

        # When the image list changes, refresh the display
        #
        # TODO When image list changes, update local attributes
        # xdim and ydim, so we know how big to set the viewport
        # in the resize method
        #
        self.imageList.addListener(lambda il: self.Refresh())


    def _initGLShaders(self):
        """
        Compiles the vertex and fragment shader programs, and
        stores references to the shader variables as attributes
        of this SliceCanvas object. This method is only called
        once, on the first draw.
        """

        # A bit hacky. We can only set the GL context (and create
        # the GL data) once something is actually displayed on the
        # screen. The _initGLShaders method is called (asynchronously)
        # by the draw() method if it sees that the glReady flag has
        # not yet been set. But draw() may be called mored than once
        # before _initGLShaders is called. Here, to prevent
        # _initGLShaders from running more than once, the first time
        # it is called it simply overwrites itself with a dummy method.
        self._initGLShaders = lambda s: s
 
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

        self.glReady = True

        
    def resize(self):
        """
        Sets up the GL canvas size, viewport, and
        projection. This method is called by draw(),
        so does not need to be called manually.
        """

        size = self.GetSize()

        # set up 2D drawing
        gl.glViewport(0, 0, size.width, size.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        # TODO fix these numbers (see notes in __init__)
        gl.glOrtho(0, 450, 0, 450, 0, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()


    def draw(self, ev):
        """
        Draws the currently selected slice to the canvas.
        """

        # image data has not been initialised.
        if not self.glReady:
            wx.CallAfter(self._initGLShaders)
            return

        self.context.SetCurrent(self)
        self.resize()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glShadeModel(gl.GL_FLAT)

        gl.glUseProgram(self.shaders)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        for i in range(len(self.imageList)):

            image = self.imageList[i]

            try:
                glImageData = image.getAttribute(self.name)
            except:
                glImageData = GLImageData(image, self)
                image.setAttribute(glImageData, self.name)
            
            imageDisplay   = image.display
            
            geomBuffer     = glImageData.geomBuffer
            imageBuffer    = glImageData.imageBuffer
            positionBuffer = glImageData.positionBuffer
            colourBuffer   = glImageData.colourBuffer

            xdim    = glImageData.xdim
            ydim    = glImageData.ydim
            zdim    = glImageData.zdim
            xstride = glImageData.xstride
            ystride = glImageData.ystride
            zstride = glImageData.zstride 

            if not imageDisplay.enabled:
                continue

            # Set up the colour buffer
            gl.glEnable(gl.GL_TEXTURE_1D)
            gl.glActiveTexture(gl.GL_TEXTURE0) 
            gl.glBindTexture(gl.GL_TEXTURE_1D, colourBuffer)
            gl.glUniform1i(self.colourMapPos, 0) 

            gl.glUniform1f(self.alphaPos, imageDisplay.alpha)

            # We draw each horizontal row of voxels one at a time.
            # This is necessary because, in order to allow image
            # buffers to be shared between different SliceCanvas
            # objects, we cannot re-arrange the image data, as
            # stored in GPU memory. So while the memory offset
            # between values in the same row (or column) is 
            # consistent, the offset between rows (columns) is
            # not. And drawing rows seems to be faster than
            # drawing columns, for reasons unknown to me.
            for yi in range(ydim):

                imageOffset = self.zpos * zstride + yi * ystride
                imageStride = xstride 
                posOffset   = yi * xdim * 4

                # The geometry buffer, which defines the geometry of a
                # single vertex (4 vertices, drawn as a triangle strip)
                geomBuffer.bind()
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
                positionBuffer.bind()
                gl.glVertexAttribPointer(
                    self.inPositionPos,
                    2,
                    gl.GL_UNSIGNED_SHORT,
                    gl.GL_FALSE,
                    0,
                    positionBuffer + posOffset)
                gl.glEnableVertexAttribArray(self.inPositionPos)
                arbia.glVertexAttribDivisorARB(self.inPositionPos, 1)

                # The image buffer, which defines
                # the colour value at each voxel.
                imageBuffer.bind()
                gl.glVertexAttribPointer(
                    self.voxelValuePos,
                    1,
                    gl.GL_UNSIGNED_BYTE,
                    gl.GL_TRUE,
                    imageStride,
                    imageBuffer + imageOffset)

                gl.glEnableVertexAttribArray(self.voxelValuePos)
                arbia.glVertexAttribDivisorARB(self.voxelValuePos, 1)

                # Draw all of the triangles!
                arbdi.glDrawArraysInstancedARB(
                    gl.GL_TRIANGLE_STRIP, 0, 4, xdim)

                gl.glDisableVertexAttribArray(self.inVertexPos)
                gl.glDisableVertexAttribArray(self.inPositionPos)
                gl.glDisableVertexAttribArray(self.voxelValuePos)
                gl.glDisable(gl.GL_TEXTURE_1D)

        gl.glUseProgram(0)

        # A vertical line at xpos, and a horizontal line at ypos
        x = self.xpos + 0.5
        y = self.ypos + 0.5

        # TODO Fix these numbers (see __init__ notes)
        
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex2f(x,         0)
        gl.glVertex2f(x,         450)
        gl.glVertex2f(0,         y)
        gl.glVertex2f(450, y)
        gl.glEnd()

        self.SwapBuffers()
