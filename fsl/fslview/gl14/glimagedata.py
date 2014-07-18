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

        self.imageBuffer = self._genImageBuffer()
        self.genVertexData(xax, yax)

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()


    def genVertexData(self, xax, yax):
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
        xdim  = image.shape[self.xax]
        ydim  = image.shape[self.yax]
        zdim  = image.shape[self.zax]

        xidxs = np.arange(xdim, dtype=np.float32)
        yidxs = np.arange(ydim, dtype=np.float32)
        
        xidxs, yidxs = np.meshgrid(xidxs, yidxs)
        
        xidxs = xidxs.ravel()
        yidxs = yidxs.ravel()

        geomData  = np.zeros((xdim * ydim * 4, 3), dtype=np.float32)
        
        for i, (xi, yi) in enumerate(zip(xidxs, yidxs)):
            geomData[i * 4 + 0, [xax, yax]] = [-0.5, -0.5]
            geomData[i * 4 + 1, [xax, yax]] = [-0.5,  0.5]
            geomData[i * 4 + 2, [xax, yax]] = [ 0.5,  0.5]
            geomData[i * 4 + 3, [xax, yax]] = [ 0.5, -0.5]
            geomData[i * 4:i * 4 + 4, xax] += xi
            geomData[i * 4:i * 4 + 4, yax] += yi


        xidxs = (xidxs + 0.5) / self.fullTexShape[self.xax]
        yidxs = (yidxs + 0.5) / self.fullTexShape[self.yax]

        xidxs = xidxs.repeat(4)
        yidxs = yidxs.repeat(4)
        zidxs = np.zeros(len(xidxs), dtype=np.float32)

        allIdxs           = [None] * 3
        allIdxs[self.xax] = xidxs
        allIdxs[self.yax] = yidxs
        allIdxs[self.zax] = zidxs
        
        texCoords       = np.vstack(allIdxs).transpose() 

        self.texCoords  = texCoords
        self.vertexData = geomData
        self.xdim       = image.shape[self.xax]
        self.ydim       = image.shape[self.yax]
        self.zdim       = image.shape[self.zax]

        
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
                        gl.GL_RGBA8,
                        texShape[0], texShape[1], texShape[2],
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
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
        display         = self.display
        volume          = display.volume
        sRate           = display.samplingRate
        imageShape      = np.array(image.shape[:3])
        
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
            displayHash, imageBuffer = \
                image.getAttribute('glImageBuffer')
        except:
            displayHash = None
            imageBuffer = None

        if imageBuffer is None:
            imageBuffer = self._initImageBuffer()

        # The image buffer already exists, and it
        # contains the data for the requested volume.  
        elif displayHash == hash(display):
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

        # Each voxel value is converted to a RGBA 4-tuple.
        # First we normalise the data to lie between 0.0 and 1.0
        imin      = float(display.displayRange.xlo)
        imax      = float(display.displayRange.xhi)
        imageData = (imageData - imin) / (imax - imin)

        # Then transform the values to RGBA
        # using the current colour map
        imageData = display.cmap(imageData)

        # Scaled to lie between 0 and 255, cast
        # to unsigned byte, and transposed so
        # the dimension order is (colour, X, Y, Z)
        imageData = np.floor(imageData * 255)
        imageData = np.array(imageData, dtype=np.uint8)

        imageData = imageData.transpose((3, 0, 1, 2))

        # Then flattened, with fortran dimension ordering,
        # so the data, as stored on the GPU, has its first
        # dimension as the fastest changing. 
        imageData = imageData.ravel(order='F')

        gl.glBindTexture(gl.GL_TEXTURE_3D, imageBuffer)
        gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                           0,
                           0, 0, 0,
                           subTexShape[0], subTexShape[1], subTexShape[2],
                           gl.GL_RGBA,
                           gl.GL_UNSIGNED_BYTE,
                           imageData)

        # Add the index of the currently stored volume and
        # sampling rate, and a reference to the texture as
        # an attribute of the image, so other things which
        # want to render the same volume of the image don't 
        # need to duplicate all of that data.
        image.setAttribute('glImageBuffer', (hash(self.display), imageBuffer))

        return imageBuffer


    def _configDisplayListeners(self):
        """
        Adds a bunch of listeners to the image.ImageDisplay object which
        defines how the given image is to be displayed. This is done so we
        can update the colour texture when image display properties are
        changed. 
        """

        def vertexUpdateNeeded(*a):
            self.genVertexData(self.xax, self.yax)

        def imageUpdateNeeded(*a):
            self._genImageBuffer()

        def imageAndVertexUpdateNeeded(*a):
            self.genVertexData(self.xax, self.yax)
            self._genImageBuffer()

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('transform',    lnrName, vertexUpdateNeeded)
        display.addListener('alpha',        lnrName, imageUpdateNeeded)
        display.addListener('displayRange', lnrName, imageUpdateNeeded)
        display.addListener('samplingRate',
                            lnrName,
                            imageAndVertexUpdateNeeded) 
        display.addListener('rangeClip',    lnrName, imageUpdateNeeded)
        display.addListener('cmap',         lnrName, imageUpdateNeeded)
        display.addListener('volume',       lnrName, imageUpdateNeeded)
        display.addListener('transform',    lnrName, vertexUpdateNeeded)
