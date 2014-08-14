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

import fsl.fslview.gl.glimage as glimage


def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords = glimage.genVertexData(
        glimg.image, glimg.display, glimg.xax, glimg.yax)

    return worldCoords, texCoords, worldCoords.shape[0]

        
def genImageData(glimg):
    """Retrieves the image data which is to be rendered. 
    """

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
