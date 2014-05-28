#!/usr/bin/env python
#
# glimagedata.py - Create OpenGL data to render 2D slices of a 3D image.

# A GLImageData object encapsulates the OpenGL information necessary
# to render 2D slices of a 3D image.
# 
# A slice from one image is rendered using four buffers and two textures.

# The first buffer, the 'geometry buffer' simply contains the 3D
# coordinates (single precision floating point) of four vertices, which
# define the geometry of a single voxel (using triangle strips).

# The remaining buffers contain the X, Y, and Z coordinates of the voxels
# in the slice to be displayed. These coordinates are stored as single
# precision floating points, and used both to position a voxel, and to
# look up its value in the 3D data texture (see below). 

# The image data itself is stored as a 3D texture, with each voxel value
# stored as a single unsigned byte in the range 0-255.  

# Finally, a 1D texture is used is used to store a lookup table containing
# an RGBA8 colour map, to colour each voxel according to its value.
#
# All of these things are created when a GLImageData object is
# instantiated. They are available as attributes of the object:
#
#  - dataBuffer
#  - xBuffer
#  - yBuffer
#  - zBuffer
#  - geomBuffer
#  - colourBuffer
#
# The contents of the x, y, z, geom and colour buffers is dependent upon
# the way that the image is being displayed.  They are regenerated
# automatically when the image display properties are changed (via
# listeners registered on the relevant fsl.data.fslimage.ImageDisplay
# properties).  If the display orientation changes (i.e. the image
# dimensions that map to the screen X/Y axes) the genIndexBuffers method
# must be called to regenerate the voxel indices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy as np

import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

# This extension provides the GL_R8 constant,
# which is built into modern versions of OpenGL.
import OpenGL.GL.ARB.texture_rg as arbrg

class GLImageData(object):

    def __init__(self, image, xax, yax, imageDisplay=None):
        """
        Initialise the OpenGL data buffers required to render the given image.
        Parameters:
        
          - image:        A fsl.data.fslimage.Image object.
        
          - xax:          The image axis which maps to the screen x axis.
        
          - yax:          The image axis which maps to the screen y axis.
        
          - imageDisplay: Optional. A fsl.data.fslimage.ImageDisplay object
                          which describes how the image is to be displayed.
                          If not provided, the default image.display instance
                          is used (see fsl.data.fslimage.ImageDisplay for
                          details).
        """

        self.image = image
        self.xax   = xax
        self.yax   = yax 

        if imageDisplay is not None: self.display = imageDisplay
        else:                        self.display = image.display

        # Maximum number of colours used to draw image data.
        # Keep this to a power of two, as some GL implementations
        # will complain/misbehave if it isn't.
        self.colourResolution = 256

        self.genIndexBuffers(xax, yax)
        self._initGLImageData()


    def _initGLImageData(self):
        """
        Creates and initialises the OpenGL data for the fslimage.Image
        object that was passed to the GLImageData constructor.
        """

        # The colour buffer, containing a map of
        # colours (stored on the GPU as a 1D texture)
        # This is initialised in the updateColourBuffer
        # method
        colourBuffer = gl.glGenTextures(1) 

        self.dataBuffer   = self._genImageBuffer(self.display.volume)
        self.colourBuffer = colourBuffer

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()

        # Create the colour buffer for the given image
        self.updateColourBuffer() 

        
    def genIndexBuffers(self, xax, yax):
        """
        (Re-)Generates data buffers containing X, Y, and Z coordinates,
        used for indexing into the image. Also generates the geometry
        buffer, which defines the geometry of a single voxel. If a
        sampling rate other than 1 is passed in, the generated index
        buffers will contain a sampling of the full coordinate space
        for the X and Y dimensions, and the vertices in the geometry
        buffer will be scaled accordingly.
        """

        self.xax = xax
        self.yax = yax

        image      = self.image
        sampleRate = self.display.samplingRate
        zax        = 3 - xax - yax 

        # The geometry buffer defines the geometry of
        # a single voxel, rendered as a triangle strip.
        geomData = np.zeros((4, 3), dtype=np.float32)
        geomData[:, [xax, yax]] = [[-0.5, -0.5],
                                   [ 0.5, -0.5],
                                   [-0.5,  0.5],
                                   [ 0.5,  0.5]]

        # Scale the voxel by the sampling rate
        geomData   = geomData * sampleRate
        geomData   = geomData.ravel('C')
        geomBuffer = vbo.VBO(geomData, gl.GL_STATIC_DRAW)
        
        # x/y/z coordinates are stored as VBO arrays
        xdim    = image.shape[xax]
        ydim    = image.shape[yax]
        zdim    = image.shape[zax]
        voxData = [None] * 3

        start = np.floor(0.5 * sampleRate)
        voxData[xax] = np.arange(start, xdim, sampleRate, dtype=np.uint16)
        voxData[yax] = np.arange(start, ydim, sampleRate, dtype=np.uint16)
        voxData[zax] = np.arange(0,     zdim,             dtype=np.uint16)
        
        # the screen x coordinate data has to be repeated (ydim) times -
        # we are drawing row-wise, and opengl does not allow us to loop
        # over a VBO in a single instance rendering call
        voxData[xax] = np.tile(voxData[xax], image.shape[yax])
        
        xBuffer = vbo.VBO(voxData[0], gl.GL_STATIC_DRAW)
        yBuffer = vbo.VBO(voxData[1], gl.GL_STATIC_DRAW)
        zBuffer = vbo.VBO(voxData[2], gl.GL_STATIC_DRAW)

        self.voxXBuffer   = xBuffer
        self.voxYBuffer   = yBuffer
        self.voxZBuffer   = zBuffer
        self.geomBuffer   = geomBuffer
        self.xdim         = len(voxData[xax]) / len(voxData[yax])
        self.ydim         = len(voxData[yax])
        self.zdim         = len(voxData[zax])

        
    def _genImageBuffer(self, volume):
        """
        (Re-)Generates the OpenGL buffer used to store the data for the given
        image. The buffer is stored as an attribute of the image and, if it
        has already been created (e.g. by another SliceCanvas object), the
        existing buffer is returned. 
        """

        image   = self.image
        display = self.display

        # we only store a single 3D image
        # in GPU memory at any one time
        shape = image.shape[:3]
        
        if len(shape) == 3: imageData = image.data[:, :, :, display.volume]
        else:               imageData = image.data

        # Calculate the dimensions of the 3D texture;
        # each dimension must have a power-of-two
        # length - see below. 
        texShape = 2 ** (np.ceil(np.log2(shape)))
        pad      = [(0, l - s) for (l, s) in zip(texShape, shape)]

        # Store the actual image texture shape as an
        # attribute - the vertex shader needs to know
        # about it to perform texture lookups (see
        # fslview/vertex_shader.glsl and
        # slicecanvas.py:SliceCanvas_draw). If we
        # can figure out how to avoid the power-of-two
        # length thing, we won't need to do this.
        self.imageTexShape = texShape 

        # Check to see if the image buffer
        # has already been created
        try:    oldVolume, imageBuffer = image.getAttribute('glImageBuffer')
        except: imageBuffer = None

        # The image buffer already exists, and it
        # contains the data for the requested volume.  
        if imageBuffer is not None and oldVolume == volume:
            return imageBuffer

        # The image data is normalised to lie
        # between 0 and 255, and cast to uint8
        imageData = np.array(imageData, dtype=np.float32)
        imageData = 255.0 * (imageData       - imageData.min()) / \
                            (imageData.max() - imageData.min())

        # and each dimension is padded so it has a
        # power-of-two length. Ugh. This is a horrible,
        # but as far as I'm aware, necessary hack.  At
        # least it's necessary using the OpenGL 2.1
        # API on OSX mavericks. It massively increases
        # image load time, too, so is a real sticking
        # point for me.
        imageData = np.pad(imageData, pad, 'constant', constant_values=0)
        imageData = np.array(imageData, dtype=np.uint8)

        # Then flattened, with fortran dimension ordering,
        # so the data, as stored on the GPU, has its first
        # dimension as the fastest changing.
        imageData = imageData.ravel(order='F') 

        # Are we creating a new texture or
        # updating an existing texture?
        createTexture = False
        if imageBuffer is None:
            imageBuffer   = gl.glGenTextures(1)
            createTexture = True

        # Set up image texture sampling thingos
        gl.glBindTexture(gl.GL_TEXTURE_3D, imageBuffer)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_EDGE)

        if createTexture:
            gl.glTexImage3D(gl.GL_TEXTURE_3D,
                            0,
                            arbrg.GL_R8,
                            texShape[0], texShape[1], texShape[2],
                            0,
                            gl.GL_RED,
                            gl.GL_UNSIGNED_BYTE,
                            imageData)
        else:
            gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                               0,
                               0, 0, 0,
                               texShape[0], texShape[1], texShape[2],
                               gl.GL_RED,
                               gl.GL_UNSIGNED_BYTE,
                               imageData)

        # Add the index of the currently stored volume and
        # a reference to the texture as an attribute of the
        # image, so other things which want to render the
        # same volume of the image  don't need to duplicate
        # all of that data.
        image.setAttribute('glImageBuffer', (volume, imageBuffer))

        return imageBuffer

        
    def updateColourBuffer(self):
        """
        Regenerates the colour buffer used to colour image voxels.
        """

        display      = self.display
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
        # colour map
        colourmap = display.cmap(newRange)
        
        # The colour data is stored on
        # the GPU as 8 bit rgba tuples
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        gl.glBindTexture(gl.GL_TEXTURE_1D, colourBuffer)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE) 
        
        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        self.colourResolution,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        colourmap)


    def _configDisplayListeners(self):
        """
        Adds a bunch of listeners to the fslimage.ImageDisplay object which
        defines how the given image is to be displayed. This is done so we
        can update the colour texture when image display properties are
        changed. 
        """

        def imageDataUpdateNeeded(*a):
            self._genImageBuffer(self.display.volume)
        
        def colourUpdateNeeded(*a):
            self.updateColourBuffer()

        def indexUpdateNeeded(*a):
            self.genIndexBuffers(self.xax, self.yax)

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('displayMin',   lnrName, colourUpdateNeeded)
        display.addListener('displayMax',   lnrName, colourUpdateNeeded)
        display.addListener('rangeClip',    lnrName, colourUpdateNeeded)
        display.addListener('cmap',         lnrName, colourUpdateNeeded)
        display.addListener('samplingRate', lnrName, indexUpdateNeeded)
        display.addListener('volume',       lnrName, imageDataUpdateNeeded)
