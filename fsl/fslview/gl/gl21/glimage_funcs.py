#!/usr/bin/env python
#
# glimage_funcs.py - Functions used by the fsl.fslview.gl.glimage.GLImage class
#                    to render 3D images in an OpenGL 2.1 compatible manner.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A GLImage object encapsulates the OpenGL information necessary
to render 2D slices of a 3D image, in an OpenGL 2.1 compatible manner.

The functions in this module make use of functions in the
:mod:`fsl.fslview.gl.glimage` module to actually generates the vertex and
texture information necessary to render an image.

Vertex and texture coordinates are stored on the GPU as vertex buffer
objects. The image data itself is stored as a 3D texture. Data for signed or
unsigned 8, 16, or 32 bit integer images is stored on the GPU in the same
format; all other data types are stored as 32 bit floating point.

This implementation is dependent upon one OpenGL ARB extension - `texture_rg`,
which allows us to store and retrieve un-clamped floating point values in the
3D image texture.

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

import numpy             as np
import OpenGL.GL         as gl
import OpenGL.arrays.vbo as vbo

# This extension provides the GL_R32F texture data format,
# which is standard in more modern versions of OpenGL.
import OpenGL.GL.ARB.texture_rg as arbrg

import fsl.fslview.gl.glimage as glimage


def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render the
    image, and associates them with OpenGL VBOs . See
    :func:`fsl.fslview.gl.glimage.genVertexData`.
    """ 
    xax = glimg.xax
    yax = glimg.yax

    worldCoords, texCoords = glimage.genVertexData(
        glimg.image, glimg.display, xax, yax)

    worldCoords = worldCoords[:, [xax, yax]]
    texCoords   = texCoords[  :, [xax, yax]]

    worldCoordBuffer = vbo.VBO(worldCoords.ravel('C'), gl.GL_STATIC_DRAW)
    texCoordBuffer   = vbo.VBO(texCoords  .ravel('C'), gl.GL_STATIC_DRAW)

    return worldCoordBuffer, texCoordBuffer, worldCoords.shape[0]

        
def _checkDataType(glimg):
    """This method determines the appropriate OpenGL texture data
    format to use for the image managed by this :class`GLImage`
    object. 
    """

    dtype = glimg.image.data.dtype

    if   dtype == np.uint8:  texExtFmt = gl.GL_UNSIGNED_BYTE
    elif dtype == np.int8:   texExtFmt = gl.GL_UNSIGNED_BYTE
    elif dtype == np.uint16: texExtFmt = gl.GL_UNSIGNED_SHORT
    elif dtype == np.int16:  texExtFmt = gl.GL_UNSIGNED_SHORT
    elif dtype == np.uint32: texExtFmt = gl.GL_UNSIGNED_INT
    elif dtype == np.int32:  texExtFmt = gl.GL_UNSIGNED_INT
    else:                    texExtFmt = gl.GL_FLOAT

    if   dtype == np.uint8:  texIntFmt = gl.GL_INTENSITY
    elif dtype == np.int8:   texIntFmt = gl.GL_INTENSITY
    elif dtype == np.uint16: texIntFmt = gl.GL_INTENSITY
    elif dtype == np.int16:  texIntFmt = gl.GL_INTENSITY
    elif dtype == np.uint32: texIntFmt = gl.GL_INTENSITY
    elif dtype == np.int32:  texIntFmt = gl.GL_INTENSITY
    else:                    texIntFmt = arbrg.GL_R32F

    if   dtype == np.int8:   signed = True
    elif dtype == np.int16:  signed = True
    elif dtype == np.int32:  signed = True
    else:                    signed = False

    if   dtype == np.uint8:  normFactor = 255.0
    elif dtype == np.int8:   normFactor = 255.0
    elif dtype == np.uint16: normFactor = 65535.0
    elif dtype == np.int16:  normFactor = 65535.0
    elif dtype == np.uint32: normFactor = 4294967295.0
    elif dtype == np.int32:  normFactor = 4294967295.0
    else:                    normFactor = 1.0

    if   dtype == np.int8:   normOffset = 128.0
    elif dtype == np.int16:  normOffset = 32768.0
    elif dtype == np.int32:  normOffset = 2147483648.0
    else:                    normOffset = 0.0

    xform = np.identity(4)
    xform[0, 0] =  normFactor
    xform[0, 3] = -normOffset

    # The fragment shader needs to know whether the data is signed
    # or unsigned, so it can perform texture coordinate transformation
    # correctly. The transformation matrix from image data range to
    # [0, 1] is used by the genColourTexture function.
    glimg.signed        = signed
    glimg.dataTypeXform = xform.transpose()

    log.debug('Image {} (data type {}) is to be '
              'stored as a 3D texture with '
              'internal format {}, external format {}, '
              'norm factor {}, norm offset {}'.format(
                  glimg.image.name,
                  dtype,
                  texIntFmt,
                  texExtFmt,
                  normFactor,
                  normOffset))

    return texIntFmt, texExtFmt

        
def genImageData(glimg):
    """Generates the OpenGL image texture used to store the data for the
    given image.

    The texture handle is stored as an attribute of the image and returned.
    If a texture handle has already been created (e.g. by another
    :class:`GLImage` object which is managing the same image), the existing
    texture handle is returned.
    """

    # figure out how to store
    # the image as a 3D texture.
    texIntFmt, texExtFmt = _checkDataType(glimg)

    image   = glimg.image 
    display = glimg.display
    volume  = display.volume

    if display.interpolation: interp = gl.GL_LINEAR
    else:                     interp = gl.GL_NEAREST

    # we only store a single 3D image
    # in GPU memory at any one time
    if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
    else:                    imageData = image.data

    # Check to see if the image texture
    # has already been created
    try:
        displayHash, imageTexture = image.getAttribute('glImageTexture')
    except:
        displayHash  = None
        imageTexture = None

    # otherwise, create a new one
    if imageTexture is None:
        imageTexture = gl.glGenTextures(1)

    # The image buffer already exists, and it
    # contains the data for the requested volume.  
    elif displayHash == hash(display):
        return imageTexture

    log.debug('Creating 3D texture for '
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
    # with appropriate interpolation method
    gl.glBindTexture(gl.GL_TEXTURE_3D, imageTexture)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_MAG_FILTER,
                       interp)
    gl.glTexParameteri(gl.GL_TEXTURE_3D,
                       gl.GL_TEXTURE_MIN_FILTER,
                       interp)
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

    # create the texture according to the format
    # calculated by the checkDataType method.
    gl.glTexImage3D(gl.GL_TEXTURE_3D,
                    0,
                    texIntFmt,
                    image.shape[0], image.shape[1], image.shape[2],
                    0,
                    gl.GL_RED,
                    texExtFmt,
                    imageData)

    # Add the ImageDisplay hash, and a reference to the
    # texture as an attribute of the image, so other
    # things which want to render the same volume of the
    # image don't need to duplicate all of that data.
    image.setAttribute('glImageTexture', (hash(display), imageTexture))

    return imageTexture

    
def genColourTexture(glimg):
    """Generates the colour texture used to colour image voxels. See
    :func:`fsl.fslview.gl.glimage.genVertexData`.

    OpenGL does different things to 3D texture data depending on its type -
    integer types are normalised from [0, INT_MAX] to [0, 1], whereas floating
    point types are left un-normalised (because we are using the
    ARB.texture_rg.GL_R32F data format - without this, floating point data is
    *clamped*, not normalised, to the range [0, 1]!). The
    :func:`_checkDataType` method calculates an appropriate transformation
    matrix to transform the image data to the appropriate texture coordinate
    range, which is then passed by this function to the
    :func:`fsl.fslview.gl.glimage.genVertexData` function.
    """ 

    texCoordXform = glimage.genColourTexture(glimg.image,
                                             glimg.display,
                                             glimg.colourTexture,
                                             xform=glimg.dataTypeXform)
    return texCoordXform
