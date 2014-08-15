#!/usr/bin/env python
#
# glimage.py - OpenGL vertex/texture creation for 2D slice rendering of a 3D
#              image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`GLImage` class, which creates and encapsulates the data
required to render 2D slice of a 3D image.

Two stand-alone functions are also contained in this module, the
:func:`genVertexData` function, and the :func:`genColourTexture`
function. These functions contain the code to actually generate the vertex and
texture information necessary to render an image (which is the same across
OpenGL versions).

The :class:`GLImage` class makes use of the functions defined in the
:mod:`fsl.fslview.gl.gl14.glimage_funcs` or the
:mod:`fsl.fslview.gl.gl21.glimage_funcs` modules, which provide OpenGL version
specific details for creation/storage of the vertex/colour/texture data.
"""

import logging
log = logging.getLogger(__name__)

import numpy          as np
import OpenGL.GL      as gl
import fsl.fslview.gl as fslgl

class GLImage(object):
 
    def __init__(self, image, xax, yax, imageDisplay):
        """Initialise the OpenGL data required to render the given image.

        After initialisation, all of the data requirted to render a slice
        is available as attributes of this object:

          - :attr:`imageData:`     A pointer to the image data being rendered.
                                   Exactly what this is depends upon the OpenGL
                                   version in use.

          - :attr:`colourTexture`: An OpenGL texture handle to a 1D texture
                                   containing the colour map used to colour
                                   the image data.
        
          - :attr:`worldCoords`:   A `(4*N, 3)` numpy array (where `N` is the
                                   number of pixels to be drawn). See the
                                   :func:`fsl.fslview.gl.glimage.genVertexData`
                                   function.

          - :attr:`texCoords`:     A `(4*N, 3)` numpy array (where `N` is the
                                   number of pixels to be drawn). See the
                                   :func:`fsl.fslview.gl.glimage.genVertexData`
                                   function.

        Other attributes, specific to the OpenGL version in use, may also be
        present. See the :mod:`fsl.fslview.gl.gl14.glimage_funcs` and
        :mod:`fsl.fslview.gl.gl21.glimage_funcs` modules for more details.

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

        self.xax     = xax
        self.yax     = yax
        self.image   = image
        self.display = imageDisplay
        
        # Initialise the image data, and
        # generate vertex/texture coordinates
        self.imageData = fslgl.glimage_funcs.genImageData( self)
        wc, tc, nv     = fslgl.glimage_funcs.genVertexData(self)

        self.worldCoords = wc
        self.texCoords   = tc
        self.nVertices   = nv

        # The colour texture, containing a map of
        # colours (stored on the GPU as a 1D texture)
        # This is initialised in the updateColourBuffer
        # method
        self.colourTexture = gl.glGenTextures(1)
        self.texCoordXform = fslgl.glimage_funcs.genColourTexture(self)

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()


    def changeAxes(self, xax, yax):
        """This method should be called when the image display axes change.
        
        It regenerates vertex information accordingly.
        """
        
        self.xax         = xax
        self.yax         = yax
        wc, tc, nv       = fslgl.glimage_funcs.genVertexData(self)
        self.worldCoords = wc
        self.texCoords   = tc
        self.nVertices   = nv 

        
    def _configDisplayListeners(self):
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """ 

        def vertexUpdate(*a):
            wc, tc, nv = fslgl.glimage_funcs.genVertexData(self)
            self.worldCoords = wc
            self.texCoords   = tc
            self.nVertices   = nv

        def imageUpdate(*a):
            self.imageData = fslgl.glimage_funcs.genImageData(self)
        
        def colourUpdate(*a):
            self.texCoordXform = fslgl.glimage_funcs.genColourTexture(self)

        display = self.display
        lnrName = 'GlImage_{}'.format(id(self))

        display.addListener('transform',       lnrName, vertexUpdate)
        display.addListener('interpolation',   lnrName, imageUpdate)
        display.addListener('alpha',           lnrName, colourUpdate)
        display.addListener('displayRange',    lnrName, colourUpdate)
        display.addListener('clipLow',         lnrName, colourUpdate)
        display.addListener('clipHigh',        lnrName, colourUpdate)
        display.addListener('cmap',            lnrName, colourUpdate)
        display.addListener('voxelResolution', lnrName, vertexUpdate)
        display.addListener('worldResolution', lnrName, vertexUpdate)
        display.addListener('volume',          lnrName, imageUpdate)


def genVertexData(image, display, xax, yax):
    """Generates vertex coordinates (for rendering voxels) and
    texture coordinates (for colouring voxels) in world space.

    Generates X/Y vertex coordinates, in the world space of the
    given image, which define a set of pixels for displaying the
    image at an arbitrary position along the world Z dimension.
    Each pixel is defined by four vertices, which are rendered
    as an OpenGL quad primitive.

    For every set of four vertices, a single vertex is also
    created, located in the centre of the four quad vertices. This
    centre vertex is used to look up the appropriate image value,
    which is then used to colour the quad.

    This function returns a tuple of two objects:

      - The first object, the *world coordinate* array, is a numpy
        array of shape `(4*N, 3)`, where `N` is the number of pixels
        to be drawn. This array contains the world coordinates for
        every pixel, with each pixel defined by four vertices (to be
        rendered as an OpenGL quad). The vertex coordinates along the
        world Z axis are all set to zero.

      - The second object, the *texture coordinate* array, is a numpy
        array of shape `(4*N, 3)`, containing contains the coordinates of
        the centre of every quad defined in the world coordinate array.
        These vertices are to be used to look up the value in the image
        data, which may then be used to determine the corresponding
        pixel colour.

    :arg image:   The :class:`~fsl.data.image.Image` object to
                  generate vertex and texture coordinates for.

    :arg display: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                  object which defines how the image is to be
                  rendered.

    :arg xax:     The world space axis which corresponds to the
                  horizontal screen axis (0, 1, or 2).

    :arg yax:     The world space axis which corresponds to the
                  vertical screen axis (0, 1, or 2). 
    """

    zax        = 3 - xax - yax
    worldRes   = display.worldResolution
    voxelRes   = display.voxelResolution
    transform  = display.transform

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = image.imageBounds(xax)
    ymin, ymax = image.imageBounds(yax)

    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # we use the world display resolution
    if transform in ('affine'):

        xpixdim = worldRes
        ypixdim = worldRes

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    else:
        xpixdim = image.pixdim[xax] * voxelRes
        ypixdim = image.pixdim[yax] * voxelRes

    # Number of samples across each dimension,
    # given the current sample rate
    xNumSamples = np.floor((xmax - xmin) / xpixdim)
    yNumSamples = np.floor((ymax - ymin) / ypixdim)

    # the adjusted width/height of our sampled voxels
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/{}, num samples {})'.format(
                  image.name, transform, worldRes, voxelRes,
                  xNumSamples * yNumSamples))

    # The location of every displayed
    # voxel in real world space
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

    # The geometry of a single
    # voxel, rendered as a quad
    voxelGeom = np.array([[-0.5, -0.5],
                          [-0.5,  0.5],
                          [ 0.5,  0.5],
                          [ 0.5, -0.5]], dtype=np.float32)

    # And scaled appropriately
    voxelGeom[:, 0] *= xpixdim
    voxelGeom[:, 1] *= ypixdim

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


def genColourTexture(image,
                     display,
                     texture,
                     colourResolution=256,
                     xform=None):
    """Generates a RGBA colour texture which is used to colour voxels.

    This function initialises the given OpenGL texture according to the
    image display properties contained in the given
    :class:`~fsl.fslview.displaycontext.ImageDisplay` object. An affine
    transformation matrix is returned, which is to be used to transform
    the image data into texture coordinate space, so the correct colour
    for a given image value is used.

    :arg image:            The :class:`~fsl.data.image.Image` object to
                           generate vertex and texture coordinates for.

    :arg display:          A
                           :class:`~fsl.fslview.displaycontext.ImageDisplay`
                           object which defines how the image is
                           to be rendered.

    :arg texture:          A handle to an already-created OpenGL
                           1-dimensional texture (i.e. the result
                           of a call to `gl.glGenTextures(1)`).

    :arg colourResolution: Size of the texture, total number of unique
                           colours in the colour map.

    :arg xform:            Optional. An affine transformation matrix to
                           be applied to the image data before it is used
                           to lookup a colour in the generated texture.
                           For example, the image data may be inadvertently
                           normalised or clamped by OpenGL - this
                           transformation matrix may be used to transform
                           the data back to its native range.
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
    texCoordXform[0, 3] = -imin * texCoordXform[0, 0]
    texCoordXform = texCoordXform.transpose()

    if xform is not None:
        texCoordXform = np.dot(xform, texCoordXform)

    log.debug('Generating colour texture for '
              'image {} (map: {}; resolution: {})'.format(
                  image.name,
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
    gl.glBindTexture(gl.GL_TEXTURE_1D, texture)
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

    return texCoordXform
