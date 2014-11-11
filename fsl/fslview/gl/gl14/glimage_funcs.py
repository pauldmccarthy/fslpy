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
:mod:`fsl.fslview.gl.glimage` module to actually generate the vertex and
texture information necessary to render an image.

This module provides the following functions:

 - :func:`init`: Does nothing - no initialisation is necessary for OpenGL 1.4.

 - :func:`genVertexData`: Generates and returns vertex and texture coordinates
   for rendering a single 2D slice of a 3D image.

 - :func:`genImageData`: Prepares and returns the 3D image data to be
   rendered.

 - :func:`genColourMap`: Configures a `matplotlib.colors.Colormap` instance
   for generating voxel colours from image data.

 - :func:`draw`: Draws the image using OpenGL.

 - :func:`destroy`: Deletes the texture handle for the colour map texture.
"""

import logging
log = logging.getLogger(__name__)

import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp

import fsl.utils.transform as transform


_glimage_vertex_program = """!!ARBvp1.0

# Transform the vertex coordinates from the display
# coordinate system to the screen coordinate system
TEMP vertexPos;
DP4 vertexPos.x, state.matrix.mvp.row[0], vertex.position;
DP4 vertexPos.y, state.matrix.mvp.row[1], vertex.position;
DP4 vertexPos.z, state.matrix.mvp.row[2], vertex.position;
DP4 vertexPos.w, state.matrix.mvp.row[3], vertex.position;

MOV result.position, vertexPos;

# Set the vertex texture coordinate
# to the vertex position
MOV result.texcoord[0], vertex.position;

END
"""


_glimage_fragment_program = """!!ARBfp1.0
TEMP dispTexCoord;
TEMP voxTexCoord;
TEMP voxValue;

# This matrix scales the voxel value to
# lie in a range which is appropriate to
# the current display range 
PARAM voxValXform[4] = { state.matrix.texture[1] };

# This matrix transforms coordinates
# from the display coordinate system
# to image voxel coordinates
PARAM dispToVoxMat[4] = { state.matrix.texture[0] };

# retrieve the 3D texture coordinates
# (which are in terms of the display
# coordinate system)
MOV dispTexCoord, fragment.texcoord[0];

# Transform said coordinates
# into voxel coordinates
DP4 voxTexCoord.x, dispToVoxMat[0], dispTexCoord;
DP4 voxTexCoord.y, dispToVoxMat[1], dispTexCoord;
DP4 voxTexCoord.z, dispToVoxMat[2], dispTexCoord;

# look up image voxel value from 3D image texture
TEX voxValue, voxTexCoord, texture[0], 3D;

# Scale voxel value according
# to the current display range
MUL voxValue, voxValue, voxValXform[0].x;
ADD voxValue, voxValue, voxValXform[0].w;

# look up the appropriate colour in the 1D colour map
# texture, and apply it to the fragment output colour
TEX result.color, voxValue.x, texture[1], 1D;
END
"""


def init(glimg, xax, yax):
    """No initialisation is necessary for OpenGL 1.4."""
    glimg.colourTexture = gl.glGenTextures(1)

    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB) 
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    
    glimg.fragmentProgram = arbfp.glGenProgramsARB(1)
    glimg.vertexProgram   = arbvp.glGenProgramsARB(1) 

    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glimg.fragmentProgram)

    arbfp.glProgramStringARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                             arbfp.GL_PROGRAM_FORMAT_ASCII_ARB,
                             len(_glimage_fragment_program),
                             _glimage_fragment_program)

    if (gl.glGetError() == gl.GL_INVALID_OPERATION):

        position = gl.glGetIntegerv(arbfp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbfp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling fragment program '
                           '({}): {}'.format(position, message))


    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glimg.vertexProgram)

    arbvp.glProgramStringARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                             arbvp.GL_PROGRAM_FORMAT_ASCII_ARB,
                             len(_glimage_vertex_program),
                             _glimage_vertex_program)

    if (gl.glGetError() == gl.GL_INVALID_OPERATION):

        position = gl.glGetIntegerv(arbvp.GL_PROGRAM_ERROR_POSITION_ARB)
        message  = gl.glGetString(  arbvp.GL_PROGRAM_ERROR_STRING_ARB)

        raise RuntimeError('Error compiling vertex program '
                           '({}): {}'.format(position, message)) 
                  
    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    
def destroy(glimg):
    """Deletes the colour map texture handle."""
    gl.glDeleteTextures(1, glimg.colourTexture)

    
def genVertexData(glimg):
    """Generates vertex and texture coordinates required to render
    the image. See :func:`fsl.fslview.gl.glimage.genVertexData`.
    """
    
    worldCoords, texCoords, indices = glimg.genVertexData()

    return worldCoords, texCoords, indices, indices.shape[0]


def _prepareImageTextureData(glimg, data):

    dtype = data.dtype

    if   dtype == np.uint8:  texExtFmt = gl.GL_UNSIGNED_BYTE
    elif dtype == np.int8:   texExtFmt = gl.GL_UNSIGNED_BYTE
    elif dtype == np.uint16: texExtFmt = gl.GL_UNSIGNED_SHORT
    elif dtype == np.int16:  texExtFmt = gl.GL_UNSIGNED_SHORT
    else:                    texExtFmt = gl.GL_UNSIGNED_SHORT

    if   dtype == np.uint8:  texIntFmt = gl.GL_LUMINANCE8
    elif dtype == np.int8:   texIntFmt = gl.GL_LUMINANCE8
    elif dtype == np.uint16: texIntFmt = gl.GL_LUMINANCE16
    elif dtype == np.int16:  texIntFmt = gl.GL_LUMINANCE16
    else:                    texIntFmt = gl.GL_LUMINANCE16

    if   dtype == np.uint8:  pass
    elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
    elif dtype == np.uint16: pass
    elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)
    else:
        dmin = float(data.min())
        dmax = float(data.max())
        data = (data - dmin) / (dmax - dmin) * 65535
        data = np.round(data)
        data = np.array(data, dtype=np.uint16)

    if   dtype == np.uint8:  offset = 0
    elif dtype == np.int8:   offset = -128
    elif dtype == np.uint16: offset = 0
    elif dtype == np.int16:  offset = -32768
    else:                    offset = -dmin

    if   dtype == np.uint8:  scale = 255
    elif dtype == np.int8:   scale = 255
    elif dtype == np.uint16: scale = 65535
    elif dtype == np.int16:  scale = 65535
    else:                    scale = dmax - dmin

    voxValXform = np.eye(4, dtype=np.float32)
    voxValXform[0, 0] = scale
    voxValXform[3, 0] = offset

    return data, texIntFmt, texExtFmt, voxValXform


def genImageData(glimg):
    """Generates the OpenGL image texture used to store the data for the
    given image.

    The texture handle is stored as an attribute of the image and returned.
    If a texture handle has already been created (e.g. by another
    :class:`GLImage` object which is managing the same image), the existing
    texture handle is returned.
    """

    image   = glimg.image 
    display = glimg.display
    volume  = display.volume

    if   display.interpolation == 'spline': interp = gl.GL_LINEAR
    elif display.interpolation == 'linear': interp = gl.GL_LINEAR
    else:                                   interp = gl.GL_NEAREST

    # we only store a single 3D image
    # in GPU memory at any one time
    if len(image.shape) > 3: imageData = image.data[:, :, :, volume]
    else:                    imageData = image.data


    imageData, texIntFmt, texExtFmt, voxValXform = \
        _prepareImageTextureData(glimg, imageData)
    glimg.voxValXform = voxValXform 

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
                    gl.GL_LUMINANCE, 
                    texExtFmt,
                    imageData)

    # Add the ImageDisplay hash, and a reference to the
    # texture as an attribute of the image, so other
    # things which want to render the same volume of the
    # image don't need to duplicate all of that data.
    image.setAttribute('glImageTexture', (hash(display), imageTexture))

    return imageTexture

    
def genColourMap(glimg, display, colourResolution):
    """Generates the colour texture used to colour image voxels. See
    :func:`fsl.fslview.gl.glimage.genVertexData`.

    OpenGL does different things to 3D texture data depending on its type -
    integer types are normalised from [0, INT_MAX] to [0, 1], whereas floating
    point types are left un-normalised (because we are using the
    ARB.texture_rg.GL_R32F data format - without this, floating point data is
    *clamped*, not normalised, to the range [0, 1]!). The
    :func:`_checkDataType` method calculates an appropriate transformation
    matrix to transform the image data to the appropriate texture coordinate
    range, which is then returned by this function, and subsequently used in
    the :func:`draw` function.
    """

    imin = display.displayRange[0]
    imax = display.displayRange[1]

    # This transformation is used to transform voxel values
    # from their native range to the range [0.0, 1.0], which
    # is required for texture colour lookup. Values below
    # or above the current display range will be mapped
    # to texture coordinate values less than 0.0 or greater
    # than 1.0 respectively.
    texCoordXform = np.identity(4, dtype=np.float32)
    texCoordXform[0, 0] = 1.0 / (imax - imin)
    texCoordXform[3, 0] = -imin * texCoordXform[0, 0]

    log.debug('Generating colour texture for '
              'image {} (map: {}; resolution: {})'.format(
                  glimg.image.name,
                  display.cmap.name,
                  colourResolution))

    # Create [self.colourResolution] rgb values,
    # spanning the entire range of the image
    # colour map
    colourRange     = np.linspace(0.0, 1.0, colourResolution)
    colourmap       = display.cmap(colourRange)
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
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)
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
                    colourResolution,
                    0,
                    gl.GL_RGBA,
                    gl.GL_UNSIGNED_BYTE,
                    colourmap)
    gl.glBindTexture(gl.GL_TEXTURE_1D, 0)

    return texCoordXform


def draw(glimg, zpos, xform=None):
    """Draws a slice of the image at the given Z location using immediate
    mode rendering.
    """

    display = glimg.display
    
    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    worldCoords = glimg.worldCoords
    indices     = glimg.indices

    worldCoords[:, glimg.zax] = zpos

    # enable the vertex and fragment programs
    gl.glEnable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glEnable(arbvp.GL_VERTEX_PROGRAM_ARB)
    arbfp.glBindProgramARB(arbfp.GL_FRAGMENT_PROGRAM_ARB,
                           glimg.fragmentProgram)
    arbvp.glBindProgramARB(arbvp.GL_VERTEX_PROGRAM_ARB,
                           glimg.vertexProgram) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glBindTexture(gl.GL_TEXTURE_3D, glimg.imageData)

    # Set up the colour map texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)

    # Configure the texture coordinate
    # transform for the colour map
    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPushMatrix()
    colourXForm = transform.concat(glimg.voxValXform, glimg.colourMap)
    gl.glLoadMatrixf(colourXForm)
    
    # And for the image texture
    mat = np.eye(4, dtype=np.float32)
    mat[0, 0] = 1.0 / glimg.image.shape[0]
    mat[1, 1] = 1.0 / glimg.image.shape[1]
    mat[2, 2] = 1.0 / glimg.image.shape[2]
    mat = transform.concat(display.displayToVoxMat, mat)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPushMatrix()
    gl.glLoadMatrixf(mat)
    
    worldCoords = worldCoords.ravel('C')

    if xform is not None: 
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glMultMatrixf(xform)

    gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
    gl.glVertexPointer(3, gl.GL_FLOAT, 0, worldCoords)

    gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                      len(indices),
                      gl.GL_UNSIGNED_INT,
                      indices)

    gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

    gl.glDisable(arbfp.GL_FRAGMENT_PROGRAM_ARB)
    gl.glDisable(arbvp.GL_VERTEX_PROGRAM_ARB)

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE0)
    gl.glPopMatrix()

    gl.glMatrixMode(gl.GL_TEXTURE)
    gl.glActiveTexture(gl.GL_TEXTURE1)
    gl.glPopMatrix() 

    if xform is not None:
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
