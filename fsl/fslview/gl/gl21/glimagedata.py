#!/usr/bin/env python
#
# glimagedata.py - Create OpenGL data to render 2D slices of a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLImageData object encapsulates the OpenGL information necessary
 to render 2D slices of a 3D image, in an OpenGL 2.1 compatible manner.

A slice from one image is rendered using four buffers and two textures.

The first buffer, the 'geometry buffer' simply contains the 3D
coordinates (single precision floating point) of four vertices, which
define the geometry of a single voxel (using triangle strips).

The remaining buffers contain the X, Y, and Z coordinates of the voxels
in the slice to be displayed. These coordinates are stored as unsigned
16 bit integers, and used both to position a voxel, and to look up its
value in the 3D data texture (see below). 

The image data itself is stored as a 3D texture. Data for signed or
unsigned 8 or 16 bit integer images is stored on the GPU in the same
format; all other data types are stored as 32 bit floating point.

Finally, a 1D texture is used is used to store a lookup table containing
an RGBA8 colour map, to colour each voxel according to its value.

All of these things are created when a GLImageData object is
instantiated. They are available as attributes of the object:

 - imageBuffer
 - xBuffer
 - yBuffer
 - zBuffer
 - geomBuffer
 - colourBuffer

The contents of all of these buffers is is dependent upon the way that
the image is being displayed.  They are regenerated automatically when
the image display properties are changed (via listeners registered on
the relevant fsl.fslview.displaycontext.ImageDisplay properties).

If the display orientation changes (i.e. the image dimensions that map
to the screen X/Y axes) the genVertexData method must be called
manually, to regenerate the voxel indices.
"""

import logging
log = logging.getLogger(__name__)

import itertools as it
import numpy as np

import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

# This extension provides some texture data format identifiers
# which are standard in more modern OpenGL versions.
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
        self.genVertexData(xax, yax)

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
        
        image      = self.image
        sampleRate = self.display.samplingRate

        xdim       = image.shape[self.xax]
        ydim       = image.shape[self.yax]

        # These values give the min/max x/y values
        # of a bounding box which encapsulates
        # the entire image
        xmin, xmax = image.imageBounds(self.xax)
        ymin, ymax = image.imageBounds(self.yax)

        # These values give the length
        # of the image along the x/y axes
        xlen = image.axisLength(self.xax)
        ylen = image.axisLength(self.yax)
        
        xpixdim    = xlen / xdim
        ypixdim    = ylen / ydim

        xSampleLen = xpixdim * sampleRate
        ySampleLen = ypixdim * sampleRate

        xNumSamples = (xmax - xmin) / xSampleLen
        yNumSamples = (ymax - ymin) / ySampleLen
        
        log.debug('Generating geometry and index buffers for {} '
                  '(sample rate {})'.format(image.name, sampleRate))

        worldX = np.linspace(xmin + 0.5 * xpixdim,
                             xmax - 0.5 * xpixdim,
                             xNumSamples)
        worldY = np.linspace(ymin + 0.5 * ypixdim,
                             ymax - 0.5 * ypixdim,
                             yNumSamples)

        worldX, worldY = np.meshgrid(worldX, worldY)

        worldX  = worldX.flatten()
        worldY  = worldY.flatten()
        nVoxels = len(worldX)

        # The geometry of a single voxel, rendered as a quad
        voxelGeom = np.array([[0, 0],
                              [0, 1],
                              [1, 1],
                              [1, 0]], dtype=np.float32)

        # Then transformed to world space
        # and shifted to the origin
        voxelGeom = image.voxToWorld(voxelGeom, axes=[self.xax, self.yax])
        voxelGeom[:, 0] -= voxelGeom[:, 0].mean() 
        voxelGeom[:, 1] -= voxelGeom[:, 1].mean()

        voxelGeom[:, 0] *= xSampleLen
        voxelGeom[:, 1] *= ySampleLen

        worldX = worldX.repeat(4) 
        worldY = worldY.repeat(4)
        
        texCoords = np.vstack((worldX, worldY))
        texCoords = np.array(texCoords, dtype=np.float32)
 
        worldX = worldX + np.tile(voxelGeom[:, 0], nVoxels)
        worldY = worldY + np.tile(voxelGeom[:, 1], nVoxels)
 
        worldCoords = np.vstack((worldX, worldY))
        worldCoords = np.array(worldCoords, dtype=np.float32)

        worldCoordBuffer = vbo.VBO(worldCoords.ravel('F'), gl.GL_STATIC_DRAW)
        texCoordBuffer   = vbo.VBO(texCoords  .ravel('F'), gl.GL_STATIC_DRAW)

        self.nVertices        = worldCoords.shape[1]
        self.worldCoordBuffer = worldCoordBuffer
        self.texCoordBuffer   = texCoordBuffer

        
    def _genImageBuffer(self):
        """
        (Re-)Generates the OpenGL buffer used to store the data for the given
        image. The buffer is stored as an attribute of the image and, if it
        has already been created (e.g. by another GLImageData object), the
        existing buffer is returned. 
        """

        image   = self.image
        display = self.display
        volume  = self.display.volume
        sRate   = self.display.samplingRate

        # we only store a single 3D image
        # in GPU memory at any one time
        if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
        else:                    imageData = image.data

        # resample the image according to the current sampling rate
        start      = np.floor(0.5 * sRate)
        imageData  = imageData[start::sRate, start::sRate, start::sRate]
        imageShape = np.array(imageData.shape)
        
        self.imageShape = imageShape

        # Check to see if the image buffer
        # has already been created
        try:
            displayHash, imageBuffer = image.getAttribute('glImageBuffer')
        except:
            displayHash = None
            imageBuffer = None

        if imageBuffer is None:
            imageBuffer = gl.glGenTextures(1)

        # The image buffer already exists, and it
        # contains the data for the requested volume.  
        elif displayHash == hash(display):
            return imageBuffer

        log.debug('Populating texture buffer for '
                  'image {} (data shape: {})'.format(
                      image.name,
                      imageData.shape))

        # The image data is flattened, with fortran dimension
        # ordering, so the data, as stored on the GPU, has its
        # first dimension as the fastest changing.
        imageData = imageData.ravel(order='F')

        # Enable storage of tightly packed data of any size (i.e.
        # our texture shape does not have to be divisible by 4).
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)
        
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
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            [0, 0, 0, 0])

        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        self.texIntFmt,
                        imageShape[0], imageShape[1], imageShape[2],
                        0,
                        gl.GL_RED,
                        self.texExtFmt,
                        imageData)

        # Add the ImageDisplay hash, and a reference to the
        # texture as an attribute of the image, so other
        # things which want to render the same volume of the
        # image don't need to duplicate all of that data.
        image.setAttribute('glImageBuffer', (hash(display), imageBuffer))

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
        colourRange     = np.linspace(0.0, 1.0, self.colourResolution)
        colourmap       = display.cmap(colourRange)
        colourmap[:, 3] = display.alpha

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
            self.genVertexData(self.xax, self.yax)

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('alpha',        lnrName, colourUpdateNeeded)
        display.addListener('displayRange', lnrName, colourUpdateNeeded)
        display.addListener('rangeClip',    lnrName, colourUpdateNeeded)
        display.addListener('cmap',         lnrName, colourUpdateNeeded)
        display.addListener('samplingRate', lnrName, indexAndImageUpdateNeeded)
        display.addListener('volume',       lnrName, imageUpdateNeeded)
