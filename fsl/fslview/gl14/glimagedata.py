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

        self.genImageData()
        self.genVertexData(xax, yax)

        # Maximum number of colours used to draw image data.
        self.colourResolution = 256 

        self.colourTexture = gl.glGenTextures(1)
        self.genColourTexture()

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
        
        image      = self.image
        sampleRate = self.display.samplingRate
        xdim       = image.shape[self.xax]
        ydim       = image.shape[self.yax]

        start = np.floor(0.5 * sampleRate)
        xidxs = np.arange(start, xdim, sampleRate, dtype=np.float32)
        yidxs = np.arange(start, ydim, sampleRate, dtype=np.float32)

        xdim = len(xidxs)
        ydim = len(yidxs)

        xidxs, yidxs = np.meshgrid(xidxs, yidxs)
        
        xidxs = xidxs.ravel()
        yidxs = yidxs.ravel()

        geomData = np.zeros((4, 3), dtype=np.float32)
        geomData[:, [xax, yax]] = [[-0.5, -0.5],
                                   [-0.5,  0.5],
                                   [ 0.5,  0.5],
                                   [ 0.5, -0.5]]
        
        geomData = geomData * sampleRate

        vertices = np.zeros((xdim * ydim * 4, 3), dtype=np.float32)
        
        for i, (xi, yi) in enumerate(zip(xidxs, yidxs)):
            
            start = i * 4
            end   = start + 4
            
            vertices[start:end, :]    = geomData
            vertices[start:end, xax] += xi
            vertices[start:end, yax] += yi

        self.vertexData = vertices
        self.xdim       = xdim
        self.ydim       = ydim
        self.zdim       = image.shape[self.zax]

        
    def genImageData(self):
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

        # Check to see if the image buffer
        # has already been created
        try:
            displayHash, imageData = image.getAttribute('glImageBuffer')
        except:
            displayHash = None
            imageData   = None

        # The image buffer already exists, and it
        # contains the data for the requested volume.  
        if imageData is not None and displayHash == hash(display):
            self.imageData = imageData
            return
        
        # we only store a single 3D image
        # in GPU memory at any one time
        if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
        else:                    imageData = image.data

        # resample the image according to the current sampling rate
        start     = np.floor(0.5 * sRate)
        imageData = imageData[start::sRate, start::sRate, start::sRate]

        if imageData.dtype != np.float32:
            imageData = np.array(imageData, dtype=np.float32)

        # First we normalise the data to lie between 0.0 and 1.0
        imin      = imageData.min()
        imax      = imageData.max()
        imageData = (imageData - imin) / (imax - imin)

        # Add the index of the currently stored volume and
        # sampling rate, and a reference to the texture as
        # an attribute of the image, so other things which
        # want to render the same volume of the image don't 
        # need to duplicate all of that data.
        image.setAttribute('glImageBuffer', (hash(self.display), imageData))

        self.imageData = imageData


    def genColourTexture(self):
        
        display       = self.display
        colourTexture = self.colourTexture

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
        gl.glBindTexture(gl.GL_TEXTURE_1D, colourTexture)
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

        def vertexUpdate(*a):
            self.genVertexData(self.xax, self.yax)

        def imageUpdate(*a):
            self.genImageData()

        def imageAndVertexUpdate(*a):
            self.genVertexData(self.xax, self.yax)
            self.genImageData()

        def colourUpdate(*a):
            self.genColourTexture()

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('transform',    lnrName, vertexUpdate)
        display.addListener('alpha',        lnrName, colourUpdate)
        display.addListener('displayRange', lnrName, colourUpdate)
        display.addListener('samplingRate', lnrName, imageAndVertexUpdate) 
        display.addListener('rangeClip',    lnrName, colourUpdate)
        display.addListener('cmap',         lnrName, colourUpdate)
        display.addListener('volume',       lnrName, imageUpdate)
        display.addListener('transform',    lnrName, vertexUpdate)
