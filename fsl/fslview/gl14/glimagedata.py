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
# the relevant fsl.fslview.displaycontext.ImageDisplay properties).
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

import OpenGL.GL as gl


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
        self.updateColourBuffer()

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()


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
        
        image = self.image

        # vertex coordinates
        # texture coordinates 

        xdim = image.shape[self.xax]
        ydim = image.shape[self.yax]

        xidxs = np.arange(xdim,        dtype=np.uint16)
        yidxs = np.arange(ydim,        dtype=np.uint16)
        zidxs = np.zeros( xdim * ydim, dtype=np.uint16)
        
        xidxs, yidxs = np.meshgrid(xidxs, yidxs)
        
        xidxs = xidxs.ravel()
        yidxs = yidxs.ravel()

        xidxs = xidxs.repeat(4)
        yidxs = yidxs.repeat(4)
        zidxs = zidxs.repeat(4)
        
        texCoords = np.vstack((xidxs, yidxs, zidxs)).transpose()
        
        geomData  = np.zeros((xdim * ydim * 4, 3), dtype=np.float32)
        
        for i, (xi, yi) in enumerate(zip(xidxs, yidxs)):
            geomData[i * 4 + 0, [xax, yax]] = [0, 0]
            geomData[i * 4 + 1, [xax, yax]] = [1, 0]
            geomData[i * 4 + 2, [xax, yax]] = [0, 1]
            geomData[i * 4 + 3, [xax, yax]] = [1, 1]
            geomData[i * 4:i * 4 + 4, xax] += xi
            geomData[i * 4:i * 4 + 4, yax] += yi
            
        self.vertexData = geomData
        self.texCoords  = texCoords

        
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

        def powerOfTwo(n):
            exp = np.log2(n)
            return 2 ** int(exp) == n

        def nextPowerOfTwo(n):
            nextExp = np.ceil(np.log2(n))
            return 2 ** nextExp
        
        for i in range(len(shape)):
            
            if not powerOfTwo(texShape[i]):
                
                nextPow     = nextPowerOfTwo(texShape[i])
                texPad[  i] = nextPow - texShape[i]
                texShape[i] = nextPow
                
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

        # The image buffer already exists, and it
        # contains the data for the requested volume. 
        if imageBuffer is not None and \
           oldVolume == volume    and \
           oldSRate  == sRate:
            return imageBuffer

        if imageBuffer is None:
            imageBuffer = self._initImageBuffer()

        shape = np.array(imageData.shape)

        log.debug('Populating texture buffer for '
                  'image {} (data shape: {})'.format(
                      image.name,
                      imageData.shape))

        # each dimension is padded so it has length
        # divisible by 4. Ugh. It's a word-alignment
        # thing, I think. This seems to be necessary
        # using the OpenGL 2.1 API on OSX mavericks. 
        if any([s != ts for s, ts in zip(shape, subTexShape)]):
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
        image.setAttribute('glImageBuffer', (volume, sRate, imageData))

        return imageBuffer

        
    def updateColourBuffer(self):
        """
        Regenerates the colour buffer used to colour image voxels.
        """

        display = self.display

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

        self.colourBuffer = colourmap


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
