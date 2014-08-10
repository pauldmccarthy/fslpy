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

import fsl.fslview.gl.glimage as glimage

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

        worldCoords, texCoords = glimage.genVertexData(
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
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
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

        # Make out-of-range values transparent
        # if clipping is enabled
        if display.clipLow:  colourmap[ 0, 3] = 0.0
        if display.clipHigh: colourmap[-1, 3] = 0.0 

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

        display.addListener('transform',       lnrName, vertexUpdate)
        display.addListener('alpha',           lnrName, colourUpdate)
        display.addListener('displayRange',    lnrName, colourUpdate)
        display.addListener('clipLow',         lnrName, colourUpdate)
        display.addListener('clipHigh',        lnrName, colourUpdate)
        display.addListener('cmap',            lnrName, colourUpdate)
        display.addListener('worldResolution', lnrName, vertexUpdate)
        display.addListener('voxelResolution', lnrName, vertexUpdate) 
        display.addListener('volume',          lnrName, imageUpdate)
