#!/usr/bin/env python
#
# glimagedata.py - Create OpenGL data to render 2D slices of a 3D image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLImageData object encapsulates the OpenGL information necessary to
render 2D slices of a 3D image, in an OpenGL 1.4 compatible manner (i.e. using
immediate mode rendering).


World cordinates
Image data
"""

import logging
log = logging.getLogger(__name__)

import numpy as np

import OpenGL.GL as gl

def genVertexData(image, display, xax, yax):
    """
    (Re-)Generates data buffers containing X, Y, and Z coordinates,
    used for indexing into the image. Also generates the geometry
    buffer, which defines the geometry of a single voxel. If a
    sampling rate other than 1 is passed in, the generated index
    buffers will contain a sampling of the full coordinate space
    for the X and Y dimensions, and the vertices in the geometry
    buffer will be scaled accordingly.
    """

    zax        = 3 - xax - yax
    sampleRate = display.samplingRate
    transform  = display.transform
    xdim       = image.shape[xax]
    ydim       = image.shape[yax]

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = image.imageBounds(xax)
    ymin, ymax = image.imageBounds(yax)

    # These values give the length
    # of the image along the x/y axes
    xlen = image.axisLength(xax)
    ylen = image.axisLength(yax)

    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # the display resolution is somewhat
    # arbitrary.
    if transform == 'affine':

        # This 'arbitrary' sample size selection doesn't
        # make any sense, as there is no correspondence
        # between image dimensions and real world
        # dimensions. Think of a better solution.
        xpixdim = xlen / xdim
        ypixdim = ylen / ydim
        xpixdim = min(xpixdim, ypixdim)
        ypixdim = xpixdim * 2

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    else:
        xpixdim = image.pixdim[xax]
        ypixdim = image.pixdim[yax] 

    # the width/height of our sampled voxels,
    # given the current sampling rate
    xSampleLen = xpixdim * sampleRate
    ySampleLen = ypixdim * sampleRate

    # The number of samples we need to draw,
    # through the entire bounding box
    xNumSamples = np.floor((xmax - xmin)) / xSampleLen
    yNumSamples = np.floor((ymax - ymin)) / ySampleLen

    log.debug('Generating coordinate buffers for {} '
              '(sample rate {}, num samples {})'.format(
                  image.name, sampleRate, xNumSamples * yNumSamples))

    # The location of every displayed
    # voxel in real world space
    worldX = np.linspace(xmin + 0.5 * xSampleLen,
                         xmax - 0.5 * ySampleLen,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * xSampleLen,
                         ymax - 0.5 * ySampleLen,
                         yNumSamples)

    worldX, worldY = np.meshgrid(worldX, worldY)

    worldX  = worldX.flatten()
    worldY  = worldY.flatten()
    nVoxels = len(worldX)

    # The geometry of a single
    # voxel, rendered as a quad
    voxelGeom = np.array([[-0.5, -0.5],
                          [-0.5,  0.5],
                          [ 0.5,  0.5],
                          [ 0.5, -0.5]], dtype=np.float32)

    # And scaled appropriately
    voxelGeom[:, 0] *= xSampleLen
    voxelGeom[:, 1] *= ySampleLen

    worldX = worldX.repeat(4) 
    worldY = worldY.repeat(4)
    worldZ = np.zeros(len(worldX))

    worldCoords = [None] * 3
    texCoords   = [None] * 3

    # The texture coordinates are in the centre of each
    # set of 4 vertices, so allow us to look up the
    # colour for every vertex coordinate
    texCoords[xax] = worldX
    texCoords[yax] = worldY
    texCoords[zax] = worldZ

    # The world coordinates define a bunch of sets
    # of 4 vertices, each rendered as a quad
    worldX = worldX + np.tile(voxelGeom[:, 0], nVoxels)
    worldY = worldY + np.tile(voxelGeom[:, 1], nVoxels)
    
    worldCoords[xax] = worldX
    worldCoords[yax] = worldY
    worldCoords[zax] = worldZ

    worldCoords = np.array(worldCoords, dtype=np.float32).transpose()
    texCoords   = np.array(texCoords,   dtype=np.float32).transpose()

    return worldCoords, texCoords


class GLImageData(object):

    def __init__(self, image, xax, yax, imageDisplay):
        """
        Initialise the OpenGL data required to render the given image.
        
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
        """
        
        self.xax = xax
        self.yax = yax

        worldCoords, texCoords = genVertexData(
            self.image, self.display, xax, yax)

        self.worldCoords = worldCoords
        self.texCoords   = texCoords

        
    def genImageData(self):
        """(Re-)Generates the image data which is passed to the GPU for
        rendering. The data (a numpy array) is stored as an attribute of
        the image and, if it has already been created (e.g. by another
        GLImageData object), the existing buffer is returned.
        """

        image           = self.image
        display         = self.display
        volume          = display.volume

        if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
        else:                    imageData = image.data

        self.imageData = imageData


    def genColourTexture(self):
        """Generates a 1D texture containing the colour map used to
        colour voxels.
        """
        
        display       = self.display
        colourTexture = self.colourTexture
        imin          = display.displayRange[0]
        imax          = display.displayRange[1]

        # This transformation is used to transform voxel values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup.
        texCoordXform = np.identity(4, dtype=np.float32)
        texCoordXform[0, 0] = 1.0 / (imax - imin)
        texCoordXform[0, 3] = -imin * texCoordXform[0, 0]
        texCoordXform = texCoordXform.transpose()
        
        self.texCoordXform = texCoordXform

        log.debug('Generating colour texture for '
                  'image {} (map: {}; resolution: {})'.format(
                      self.image.name,
                      display.cmap.name,
                      self.colourResolution))
    
        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map
        colourRange = np.linspace(0.0, 1.0, self.colourResolution)
        colourmap   = display.cmap(colourRange)
        colourmap[:, 3] = display.alpha

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

        # Values out of range are made transparent
        if display.rangeClip:
            gl.glTexParameteri(gl.GL_TEXTURE_1D,
                               gl.GL_TEXTURE_WRAP_S,
                               gl.GL_CLAMP_TO_BORDER) 
            gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                                gl.GL_TEXTURE_BORDER_COLOR,
                                [1.0, 1.0, 1.0, 0.0])

        # Or clamped to the min/max colours
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
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.

        This is done so we can update the colour texture and image data when
        display properties are changed.
        """

        def vertexUpdate(*a):
            self.genVertexData(self.xax, self.yax)

        def imageUpdate(*a):
            self.genImageData()

        def imageAndVertexUpdate(*a):
            vertexUpdate()
            self.genImageData()

        def colourUpdate(*a):
            self.genColourTexture()

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('transform',    lnrName, vertexUpdate)
        display.addListener('alpha',        lnrName, colourUpdate)
        display.addListener('displayRange', lnrName, colourUpdate)
        display.addListener('rangeClip',    lnrName, colourUpdate)
        display.addListener('cmap',         lnrName, colourUpdate)
        display.addListener('samplingRate', lnrName, imageAndVertexUpdate) 
        display.addListener('volume',       lnrName, imageUpdate)
