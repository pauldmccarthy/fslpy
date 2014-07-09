#!/usr/bin/env python
#
# glimagedata.py - Create OpenGL data to render 2D slices of a 3D image.
#
# A GLImageData object encapsulates the OpenGL information necessary
# to render 2D slices of a 3D image.
# 
# A slice from one image is rendered using four buffers and two textures.
#
# The first buffer, the 'geometry buffer' simply contains the 3D
# coordinates (single precision floating point) of four vertices, which
# define the geometry of a single voxel (using triangle strips).
#
# The remaining buffers contain the X, Y, and Z coordinates of the voxels
# in the slice to be displayed. These coordinates are stored as unsigned
# 16 bit integers, and used both to position a voxel, and to look up its
# value in the 3D data texture (see below). 
#
# The image data itself is stored as a 3D texture. Data for signed or
# unsigned 8 or 16 bit integer images is stored on the GPU in the same
# format; all other data types are stored as 32 bit floating point.
#
# Finally, a 1D texture is used is used to store a lookup table containing
# an RGBA8 colour map, to colour each voxel according to its value.
#
# All of these things are created when a GLImageData object is
# instantiated. They are available as attributes of the object:
#
#  - imageBuffer
#  - xBuffer
#  - yBuffer
#  - zBuffer
#  - geomBuffer
#  - colourBuffer
#
# The contents of all of these buffers is is dependent upon the way that
# the image is being displayed.  They are regenerated automatically when
# the image display properties are changed (via listeners registered on
# the relevant fsl.data.image.ImageDisplay properties).
# 
# If the display orientation changes (i.e. the image dimensions that map
# to the screen X/Y axes) the genIndexBuffers method must be called
# manually, to regenerate the voxel indices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy as np

import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

# This extension provides some texture data format identifiers which are 
import OpenGL.GL.ARB.texture_rg as arbrg


class GLImageData(object):

    def __init__(self, image, xax, yax, imageDisplay):
        """
        Initialise the OpenGL data buffers required to render the given image.
        Parameters:
        
          - image:        A fsl.data.image.Image object.
        
          - xax:          The image axis which maps to the screen x axis.
        
          - yax:          The image axis which maps to the screen y axis.
        
          - imageDisplay: A fsl.fslview.displaycontext.ImageDisplay object
                          which describes how the image is to be displayed.
        """
        
        self.image   = image
        self.display = imageDisplay

        self._checkDataType()

        # Buffers for storing image data
        # and voxel coordinates
        self.imageBuffer = self._genImageBuffer()
        self.genIndexBuffers(xax, yax)

        # Maximum number of colours used to draw image data.
        # Keep this to a power of two, as some GL implementations
        # will complain/misbehave if it isn't.
        self.colourResolution = 256

        # The colour buffer, containing a map of
        # colours (stored on the GPU as a 1D texture)
        # This is initialised in the updateColourBuffer
        # method
        self.colourBuffer = gl.glGenTextures(1) 
        self.updateColourBuffer()

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()

        
    def _checkDataType(self):
        """
        This method determines the appropriate OpenGL texture data
        format to use for the image managed by this GLImageData
        object. 
        """

        dtype = self.image.data.dtype

        if   dtype == np.uint8:  self.texIntFmt = arbrg.GL_R8
        elif dtype == np.int8:   self.texIntFmt = arbrg.GL_R8
        elif dtype == np.uint16: self.texIntFmt = arbrg.GL_R16
        elif dtype == np.int16:  self.texIntFmt = arbrg.GL_R16
        else:                    self.texIntFmt = arbrg.GL_R32F

        if   dtype == np.uint8:  self.texExtFmt = gl.GL_UNSIGNED_BYTE
        elif dtype == np.int8:   self.texExtFmt = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint16: self.texExtFmt = gl.GL_UNSIGNED_SHORT
        elif dtype == np.int16:  self.texExtFmt = gl.GL_UNSIGNED_SHORT
        else:                    self.texExtFmt = gl.GL_FLOAT

        if   dtype == np.int8:   self.signed = True
        elif dtype == np.int16:  self.signed = True
        else:                    self.signed = False

        if   dtype == np.uint8:  self.normFactor = 255.0
        elif dtype == np.int8:   self.normFactor = 255.0
        elif dtype == np.uint16: self.normFactor = 65535.0
        elif dtype == np.int16:  self.normFactor = 65535.0
        else:                    self.normFactor = 1.0

        if   dtype == np.int8:   self.normOffset = 128.0
        elif dtype == np.int16:  self.normOffset = 32768.0
        else:                    self.normOffset = 0.0

        log.debug('Image {} (data type {}) is to be '
                  'stored as a 3D texture with '
                  'internal format {}, external format {}, '
                  'norm factor {}, norm offset {}'.format(
                      self.image.name,
                      dtype,
                      self.texIntFmt,
                      self.texExtFmt,
                      self.normFactor,
                      self.normOffset))


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
        self.zax = 3 - xax - yax
        
        zax        = self.zax
        image      = self.image
        sampleRate = self.display.samplingRate


        log.debug('Generating geometry and index buffers for {} '
                  '(sample rate {})'.format(image.name, sampleRate))

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

        log.debug('X{} indices: {}*{} = {}; '
                  'Y{} indices: {}; '
                  'Z{} indices: {}'.format(
                      xax,
                      voxData[xax].size,  image.shape[yax],
                      voxData[xax].size * image.shape[yax],
                      yax, voxData[yax].size,
                      zax, voxData[zax].size))
        
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

        
    def _calculateTextureShape(self, shape):
        """
        Calculates the size required to store an image of the given shape
        as a GL texture. I don't know if it is a problem which affects all
        graphics cards, but on my MacbookPro11,3 (NVIDIA GeForce GT 750M),
        all dimensions of a texture must have length divisible by 4.
        This method returns two values - the first is the adjusted shape,
        and the second is the amount of padding, i.e. the difference
        between the texture shape and the input shape.
        """

        # each dimension of a texture must have length divisble by 4.
        # I don't know why; I presume that they need to be word-aligned.
        texShape = np.array(shape)
        texPad   = np.zeros(len(shape))
        
        for i in range(len(shape)):
            if texShape[i] % 4:
                texPad[  i]  = 4 - (texShape[i] % 4)
                texShape[i] += texPad[i]
                
        return texShape, texPad 


    def _initImageBuffer(self):
        """
        Initialises a single-channel 3D texture which will be used
        to store the image managed by this GLImageData object. The
        texture is not populated with data - this is done by
        _genImageData on an as-needed basis.
        """

        texShape, _ = self._calculateTextureShape(self.image.shape)
        imageBuffer = gl.glGenTextures(1)

        log.debug('Initialising texture buffer for {} ({})'.format(
            self.image.name,
            texShape))
        
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

        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        self.texIntFmt,
                        texShape[0], texShape[1], texShape[2],
                        0,
                        gl.GL_RED,
                        self.texExtFmt,
                        None)

        return imageBuffer


    def _genImageBuffer(self):
        """
        (Re-)Generates the OpenGL buffer used to store the data for the given
        image. The buffer is stored as an attribute of the image and, if it
        has already been created (e.g. by another GLImageData object), the
        existing buffer is returned. 
        """

        image           = self.image
        volume          = self.display.volume
        sRate           = self.display.samplingRate
        imageShape      = np.array(self.image.shape[:3])
        
        fullTexShape, _ = self._calculateTextureShape(imageShape)

        # we only store a single 3D image
        # in GPU memory at any one time
        if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
        else:                    imageData = image.data

        # resample the image according to the current sampling rate
        start     = np.floor(0.5 * sRate)
        imageData = imageData[start::sRate, start::sRate, start::sRate]

        # calculate the required texture shape for that data
        subTexShape, subTexPad = self._calculateTextureShape(imageData.shape)

        # Store the actual image texture shape as an
        # attribute - the vertex shader needs to know
        # about it to perform texture lookups (see
        # fslview/vertex_shader.glsl and
        # slicecanvas.py:SliceCanvas_draw). If we
        # could store textures of an arbitrary size
        # (i.e. without the lengths having to be
        # divisible by 4), we wouldn't need to do this.
        self.fullTexShape  = fullTexShape
        self.subTexShape   = subTexShape
        self.subTexPad     = subTexPad

        # Check to see if the image buffer
        # has already been created
        try:
            oldVolume, oldSRate, imageBuffer = \
                image.getAttribute('glImageBuffer')
        except:
            oldVolume   = None
            oldSRate    = None
            imageBuffer = None

        if imageBuffer is None:
            imageBuffer = self._initImageBuffer()

        # The image buffer already exists, and it
        # contains the data for the requested volume.  
        elif oldVolume == volume and oldSRate == sRate:
            return imageBuffer

        shape = np.array(imageData.shape)

        log.debug('Populating texture buffer for '
                  'image {} (data shape: {})'.format(
                      image.name,
                      imageData.shape))

        # each dimension is padded so it has length
        # divisible by 4. Ugh. It's a word-alignment
        # thing, I think. This seems to be necessary
        # using the OpenGL 2.1 API on OSX mavericks. 
        if np.any(shape % 4):
            log.debug('Padding image {} data '
                      'to shape {}'.format(image.name, subTexShape))
            pad       = zip(np.zeros(len(subTexPad)), subTexPad)
            imageData = np.pad(imageData, pad, 'constant', constant_values=0)

        # Then flattened, with fortran dimension ordering,
        # so the data, as stored on the GPU, has its first
        # dimension as the fastest changing.
        imageData = imageData.ravel(order='F')

        gl.glBindTexture(gl.GL_TEXTURE_3D, imageBuffer)
        gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                           0,
                           0, 0, 0,
                           subTexShape[0], subTexShape[1], subTexShape[2],
                           gl.GL_RED,
                           self.texExtFmt,
                           imageData)

        # Add the index of the currently stored volume and
        # sampling rate, and a reference to the texture as
        # an attribute of the image, so other things which
        # want to render the same volume of the image don't 
        # need to duplicate all of that data.
        image.setAttribute('glImageBuffer', (volume, sRate, imageBuffer))

        return imageBuffer

        
    def updateColourBuffer(self):
        """
        Regenerates the colour buffer used to colour image voxels.
        """

        display      = self.display
        colourBuffer = self.colourBuffer

        log.debug('Generating colour buffer for '
                  'image {} (map: {}; resolution: {})'.format(
                      self.image.name,
                      display.cmap.name,
                      self.colourResolution))
    
        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map
        colourRange = np.linspace(0.0, 1.0, self.colourResolution)
        colourmap   = display.cmap(colourRange)

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

        if display.rangeClip:
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_BORDER) 
            gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_BORDER_COLOR,
                                [1.0, 1.0, 1.0, 0.0])
        else:
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
        Adds a bunch of listeners to the image.ImageDisplay object which
        defines how the given image is to be displayed. This is done so we
        can update the colour texture when image display properties are
        changed. 
        """

        def imageUpdateNeeded(*a):
            self._genImageBuffer()
        
        def colourUpdateNeeded(*a):
            self.updateColourBuffer()

        def indexAndImageUpdateNeeded(*a):
            self._genImageBuffer()
            self.genIndexBuffers(self.xax, self.yax)

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('rangeClip',    lnrName, colourUpdateNeeded)
        display.addListener('cmap',         lnrName, colourUpdateNeeded)
        display.addListener('samplingRate', lnrName, indexAndImageUpdateNeeded)
        display.addListener('volume',       lnrName, imageUpdateNeeded)
