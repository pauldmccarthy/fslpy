#!/usr/bin/env python
#
# glimage.py - OpenGL vertex/texture creation for 2D slice rendering of a 3D
#              image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`GLImage` class, which creates and encapsulates the data
and logic required to render 2D slice of a 3D image. The :class:`GLImage` class
provides the interface defined in the :mod:`~fsl.fslview.gl.globject` module.

One stand-alone function is also contained in this module, the
:func:`genVertexData` function. This function contains the code to actually
generate the vertex information necessary to render an image (which is the
same across OpenGL versions).

The :class:`GLImage` class makes use of the functions defined in the
:mod:`fsl.fslview.gl.gl14.glimage_funcs` or the
:mod:`fsl.fslview.gl.gl21.glimage_funcs` modules, which provide OpenGL version
specific details for creation/storage of the vertex/colour/texture data.

These version dependent modules must provide the following functions:

  - `init(GLImage, xax, yax)`: Perform any necessary initialisation.

  - `genVertexData(GLImage)`: Create and prepare vertex and texture
     coordinates, using the :func:`genVertexData` function. 
                               
  - `genImageData(GLImage)`: Retrieve and prepare the image data to be
    displayed.

  - `genColourMap(GLImage)`: Create and prepare the colour map used to
    colour image voxels.

  - `draw(GLImage, zpos, xform=None)`: Draw a slice of the image at the given
    Z position. If xform is not None, it must be applied as a transformation
    on the vertex coordinates.

  - `destroy(GLimage)`: Perform any necessary clean up.

"""

import logging
log = logging.getLogger(__name__)

import numpy          as np
import OpenGL.GL      as gl
import fsl.fslview.gl as fslgl
import                   globject

class GLImage(object):
    """The :class:`GLImage` class encapsulates the data and logic required to
    render 2D slices of a 3D image.
    """
 
    def __init__(self, image, display):
        """Creates a GLImage object bound to the given image, and associated
        image display.

        :arg image:        A :class:`~fsl.data.image.Image` object.
        
        :arg imageDisplay: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                           object which describes how the image is to be
                           displayed.
        """

        self.image   = image
        self.display = display
        self._ready  = False


    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised, and the
        image is ready to be drawn, `False` before.
        """
        return self._ready

        
    def init(self, xax, yax):
        """Initialise the OpenGL data required to render the given image.

        The real initialisation takes place in this method - it must
        only be called after an OpenGL context has been created.
        """
        
        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()

        self.setAxes(xax, yax)
        fslgl.glimage_funcs.init(self, xax, yax)

        # Initialise the image data, and
        # generate vertex/texture coordinates
        self.imageData = fslgl.glimage_funcs.genImageData(self)

        # The colour map, used for converting 
        # image data to a RGBA colour.
        self.colourResolution = 256
        self.colourMap        = self.genColourMap(self.colourResolution)
        
        self._ready = True


    def setAxes(self, xax, yax):
        """This method should be called when the image display axes change.
        
        It regenerates vertex information accordingly.
        """
        
        self.xax         = xax
        self.yax         = yax
        self.zax         = 3 - xax - yax
        wc, tc, idxs, nv = fslgl.glimage_funcs.genVertexData(self)
        self.worldCoords = wc
        self.texCoords   = tc
        self.indices     = idxs
        self.nVertices   = nv

        
    def draw(self, zpos, xform=None):
        """Draws a 2D slice of the image at the given real world Z location.
        This is performed via a call to the OpenGL version-dependent `draw`
        function, contained in one of the :mod:`~fsl.fslview.gl.gl14` or
        :mod:`~fsl.fslview.gl.gl21` packages.

        If `xform` is not None, it is applied as an affine transformation to
        the vertex coordinates of the rendered image data.
        """
        fslgl.glimage_funcs.draw(self, zpos, xform)


    def destroy(self):
        """This should be called when this :class:`GLImage` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles).
        """
        fslgl.glimage_funcs.destroy(self)


    def genVertexData(self):
        return genVertexData(self.image, self.display, self.xax, self.yax)

        
    def genColourMap(self, colourResolution=256):
        return fslgl.glimage_funcs.genColourMap(self,
                                                self.display,
                                                colourResolution)

        
    def _configDisplayListeners(self):
        """Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.ImageDisplay` object which defines
        how the given image is to be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """ 

        def vertexUpdate(*a):
            wc, tc, idx, nv = fslgl.glimage_funcs.genVertexData(self)
            self.worldCoords = wc
            self.texCoords   = tc
            self.indices     = idx
            self.nVertices   = nv

        def imageUpdate(*a):
            self.imageData = fslgl.glimage_funcs.genImageData(self)
        
        def colourUpdate(*a):
            self.colourMap = fslgl.glimage_funcs.genColourMap(
                self,
                self.display,
                self.colourResolution)

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

    Generates X/Y vertex coordinates, in the world space of the given image,
    which define a set of pixels for displaying the image at an arbitrary
    position along the world Z dimension.  Each pixel is defined by four
    vertices, which are rendered as an OpenGL quad primitive. The
    :func:`~fsl.fslview.gl.globject.calculateSamplePoints` function is used
    to calculate the coordinate locations.

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
    
    worldCoords, xpixdim, ypixdim, xlen, ylen = \
      globject.calculateSamplePoints(
          image, display, xax, yax)

    # All voxels are rendered using a triangle strip,
    # with rows connected via degenerate vertices
    worldCoords, texCoords, indices = globject.samplePointsToTriangleStrip(
        worldCoords, xpixdim, ypixdim, xlen, ylen, xax, yax)

    worldCoords = np.array(worldCoords, dtype=np.float32)
    texCoords   = np.array(texCoords,   dtype=np.float32)
    indices     = np.array(indices,     dtype=np.uint32)

    return worldCoords, texCoords, indices
