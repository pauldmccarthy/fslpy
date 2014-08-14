#!/usr/bin/env python
#
# glvolume.py - A class which encapsulates the data required to render
#               a 2D slice of a 3D volume in an OpenGL 1.4 compatible
#               manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the GLVolume object, which which encapsulates the data required to render
#               a 2D slice of a 3D volume in an OpenGL 1.4 compatible
#               manner.

A GL object encapsulates the OpenGL information necessary to
render 2D slices of a 3D image, in an OpenGL 1.4 compatible manner (i.e. using
immediate mode rendering).


World cordinates
Image data
"""

import logging
log = logging.getLogger(__name__)

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
        """
        Regenerates the colour texture used to colour image voxels.
        """

        texCoordXform = glimage.genColourTexture(self.image,
                                                 self.display,
                                                 self.colourTexture)
        self.texCoordXform = texCoordXform 


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
