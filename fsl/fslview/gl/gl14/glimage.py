#!/usr/bin/env python
#
# glimage.py - A class which encapsulates the data required to render
#              a 2D slice of a 3D image in an OpenGL 1.4 compatible
#              manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the GLImage class, which which encapsulates the data required to
render a 2D slice of a 3D image in an OpenGL 1.4 compatible manner.

A GLImage object encapsulates the OpenGL information necessary to render 2D
slices of a 3D image, in an OpenGL 1.4 compatible manner (i.e. using immediate
mode rendering).

This class makes use of the functions in the :mod:`fsl.fslview.gl.glimage`
module, which actually generates the vertex and texture information necessary
to render an image.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL as gl

import fsl.fslview.gl.glimage as glimage

class GLImage(object):

    def __init__(self, image, xax, yax, imageDisplay):
        """Initialise the OpenGL data required to render the given image.

        After initialisation, all of the data requirted to render a slice
        is available as attributes of this object:

          - :attr:`imageData:`     The 3D image data.

          - :attr:`colourTexture`: An OpenGL texture handle to a 1D texture
                                   containing the colour map used to colour
                                   the image data.
        
          - :attr:`worldCoords`:   A `(3,4*N)` numpy array (where `N` is the
                                   number of pixels to be drawn). See the
                                   :func:`fsl.fslview.gl.glimage.genVertexData`
                                   function.

          - :attr:`texCoords`:     A `(3,N)` numpy array (where `N` is the
                                   number of pixels to be drawn). See the
                                   :func:`fsl.fslview.gl.glimage.genVertexData`
                                   function.

        As part of initialisation, this object registers itself as a listener
        on several properties of the given
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object so that, when
        any display properties change, the image data, colour texture, and
        vertex data are automatically updated.
        
        :arg image:        A :class:`~fsl.data.image.Image` object.
        
        :arg xax:          The image world axis which corresponds to the
                           horizontal screen axis.

        :arg xax:          The image world axis which corresponds to the
                           vertical screen axis.        
        
        :arg imageDisplay: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                           object which describes how the image is to be
                           displayed.
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
        """Generates vertex and texture coordinates required to render
        the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
        """
        
        self.xax = xax
        self.yax = yax

        worldCoords, texCoords = glimage.genVertexData(
            self.image, self.display, xax, yax)

        self.worldCoords = worldCoords
        self.texCoords   = texCoords

        
    def genImageData(self):
        """Retrieves the image data which is to be rendered. 
        """

        image   = self.image
        display = self.display
        volume  = display.volume

        if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
        else:                    imageData = image.data

        self.imageData = imageData

        
    def genColourTexture(self):
        """Generates the colour texture used to colour image voxels. See
        :func:`fsl.fslview.gl.glimage.genVertexData`.
        """

        texCoordXform = glimage.genColourTexture(self.image,
                                                 self.display,
                                                 self.colourTexture)
        self.texCoordXform = texCoordXform 


    def _configDisplayListeners(self):
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.

        This is done so we can update the colour, vertex, and image data when
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
