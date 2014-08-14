#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 1.4 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides functions which are used by the
:class:`~fsl.fslview.gl.glimage.GLImage` class to render 3D images in an
OpenGL 1.4 compatible manner. (i.e. using immediate mode rendering).

The functions in this module make use of functions in the
:mod:`fsl.fslview.gl.glimage` module to actually generates the vertex and
texture information necessary to render an image.

This module provides three functions:

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`genImageData`: Prepares and returns the 3D image data to be
   rendered.

 - :func:`genColourTexture`: Configures an OpenGL 1D texture with a colour map,
   used for colouring the image data.
"""

import logging
log = logging.getLogger(__name__)

import fsl.fslview.gl.glimage as glimage


def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords = glimage.genVertexData(
        glimg.image, glimg.display, glimg.xax, glimg.yax)

    return worldCoords, texCoords, worldCoords.shape[0]

        
def genImageData(glimg):
    """Retrieves the image data which is to be rendered."""

    image   = glimg.image
    display = glimg.display
    volume  = display.volume

    if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
    else:                    imageData = image.data

    return imageData

        
def genColourTexture(glimg):
    """Generates the colour texture used to colour image voxels. See
    :func:`fsl.fslview.gl.glimage.genVertexData`.
    """

    texCoordXform = glimage.genColourTexture(glimg.image,
                                             glimg.display,
                                             glimg.colourTexture)
    return texCoordXform 
