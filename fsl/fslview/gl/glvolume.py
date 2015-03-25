#!/usr/bin/env python
#
# glvolume.py - OpenGL vertex/texture creation for 2D slice rendering of a 3D
#               image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`GLVolume` class, which creates and encapsulates the
data and logic required to render 2D slice of a 3D image. The
:class:`GLVolume` class provides the interface defined in the
:class:`~fsl.fslview.gl.globject.GLObject` class.

A :class:`GLVolume` instance may be used to render an
:class:`~fsl.data.image.Image` instance which has an ``imageType`` of
``volume``. It is assumed that this ``Image`` instance is associated with a
:class:`~fsl.fslview.displaycontext.Display` instance which contains a
:class:`~fsl.fslview.displaycontext.volumeopts.VolumeOpts` instance,
containing display options specific to volume rendering.

The :class:`GLVolume` class makes use of the functions defined in the
:mod:`fsl.fslview.gl.gl14.glvolume_funcs` or the
:mod:`fsl.fslview.gl.gl21.glvolume_funcs` modules, which provide OpenGL 
version specific details for creation/storage of vertex data, and for
rendering.

These version dependent modules must provide the following functions:

  - ``init(GLVolume)``: Perform any necessary initialisation.

  - ``destroy(GLVolume)``: Perform any necessary clean up.

  - ``genVertexData(GLVolume)``: Create and prepare vertex coordinates, using
    the :meth:`GLVolume.genVertexData` method.

  - ``preDraw()``: Initialise the GL state, ready for drawing.

  - ``draw(GLVolume, zpos, xform=None)``: Draw a slice of the image at the
    given Z position. If xform is not None, it must be applied as a 
    transformation on the vertex coordinates.

  - ``postDraw()``: Clear the GL state after drawing.

Images are rendered in essentially the same way, regardless of which OpenGL
version-specific module is used.  The image data itself is stored on the GPU
as a 3D texture, and the current colour map as a 1D texture. A slice through
the texture is rendered using four vertices, located at the respective corners
of the image bounds.

"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL               as gl
import numpy                   as np

import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.textures as fsltextures
import fsl.fslview.gl.globject as globject


class GLVolume(globject.GLImageObject):
    """The :class:`GLVolume` class encapsulates the data and logic required to
    render 2D slices of a 3D image.
    """
 
    def __init__(self, image, display):
        """Creates a GLVolume object bound to the given image, and associated
        image display.

        :arg image:   A :class:`~fsl.data.image.Image` object.
        
        :arg display: A :class:`~fsl.fslview.displaycontext.Display`
                      object which describes how the image is to be
                      displayed. 
        """

        globject.GLImageObject.__init__(self, image, display)
        
        self._ready = False


    def ready(self):
        """Returns `True` when the OpenGL data/state has been initialised,
        and the image is ready to be drawn, `False` before.
        """
        return self._ready

        
    def init(self):
        """Initialise the OpenGL data required to render the given image.

        The real initialisation takes place in this method - it must
        only be called after an OpenGL context has been created.
        """
        
        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.addDisplayListeners()

        fslgl.glvolume_funcs.init(self)

        self.imageTexture = fsltextures.getTexture(
            self.image, type(self).__name__, self.display)

        # The colour map, used for converting 
        # image data to a RGBA colour.
        self.colourTexture = gl.glGenTextures(1)
        log.debug('Created GL texture: {}'.format(self.colourTexture))
        
        self.colourResolution = 256
        self.refreshColourTexture(self.colourResolution)
        
        self._ready = True


    def setAxes(self, xax, yax):
        """This method should be called when the image display axes change.
        
        It regenerates vertex information accordingly.
        """
        
        self.xax         = xax
        self.yax         = yax
        self.zax         = 3 - xax - yax
        wc, idxs, nverts = fslgl.glvolume_funcs.genVertexData(self)
        self.worldCoords = wc
        self.indices     = idxs
        self.nVertices   = nverts


    def preDraw(self):
        """Sets up the GL state to draw a slice from this :class:`GLVolume`
        instance.
        """
        
        if not self.display.enabled:
            return

        # Set up the image data texture 
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glEnable(gl.GL_TEXTURE_3D)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.imageTexture.texture)

        # Set up the colour map texture
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glEnable(gl.GL_TEXTURE_1D)
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.colourTexture)
        
        fslgl.glvolume_funcs.preDraw(self)

        
    def draw(self, zpos, xform=None):
        """Draws a 2D slice of the image at the given real world Z location.
        This is performed via a call to the OpenGL version-dependent `draw`
        function, contained in one of the :mod:`~fsl.fslview.gl.gl14` or
        :mod:`~fsl.fslview.gl.gl21` packages.

        If `xform` is not None, it is applied as an affine transformation to
        the vertex coordinates of the rendered image data.

        Note: Calls to this method must be preceded by a call to
        :meth:`preDraw`, and followed by a call to :meth:`postDraw`.
        """
        
        if not self.display.enabled:
            return
        
        fslgl.glvolume_funcs.draw(self, zpos, xform)

        
    def drawAll(self, zposes, xforms):
        """Calls the module-specific ``drawAll`` function. """
        
        if not self.display.enabled:
            return
        fslgl.glvolume_funcs.drawAll(self, zposes, xforms)

        
    def postDraw(self):
        """Clears the GL state after drawing from this :class:`GLVolume`
        instance.
        """
        if not self.display.enabled:
            return

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
        gl.glDisable(gl.GL_TEXTURE_3D)
        
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)
        gl.glDisable(gl.GL_TEXTURE_1D)
        
        fslgl.glvolume_funcs.postDraw(self) 


    def destroy(self):
        """This should be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles).
        """

        fsltextures.deleteTexture(self.imageTexture)
        self.removeDisplayListeners()
        fslgl.glvolume_funcs.destroy(self)


    def genVertexData(self):
        """Generates coordinates at the corners of the image bounds, along the
        xax/yax plane, which define a slice through the 3D image.

        This method is provided for use by the version-dependent
        :mod:`fsl.fslview.gl.gl14.glvolume_funcs` and 
        :mod:`fsl.fslview.gl.gl21.glvolume_funcs` modules, in their
        implemntation of the ``genVertexData` function.

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

        return globject.slice2D(
            self.image.shape,
            self.xax,
            self.yax,
            self.display.getTransform('voxel', 'display'))

    
    def refreshColourTexture(self, colourResolution):
        """Configures the colour texture used to colour image voxels.

        Also createss a transformation matrix which transforms an image voxel
        value to the range (0-1), which may then be used as a texture
        coordinate into the colour map texture. This matrix is stored as an
        attribute of this :class:`GLVolume` object called
        :attr:`colourMapXForm`. See also the :meth:`genImageTexture` method
        for more details.
        """

        opts = self.displayOpts

        imin = opts.displayRange[0]
        imax = opts.displayRange[1]

        # This transformation is used to transform voxel values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
        if imax == imin: scale = 1
        else:            scale = imax - imin
        
        cmapXform = np.identity(4, dtype=np.float32)
        cmapXform[0, 0] = 1.0 / scale
        cmapXform[3, 0] = -imin * cmapXform[0, 0]

        self.colourMapXform = cmapXform

        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map
        if opts.invert: colourRange = np.linspace(1.0, 0.0, colourResolution)
        else:           colourRange = np.linspace(0.0, 1.0, colourResolution)
        
        colourmap = opts.cmap(colourRange)

        # Make out-of-range values transparent
        # if clipping is enabled 
        if opts.clipLow:  colourmap[ 0, 3] = 0.0
        if opts.clipHigh: colourmap[-1, 3] = 0.0

        # The colour data is stored on
        # the GPU as 8 bit rgba tuples
        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel(order='C')

        # GL texture creation stuff
        gl.glBindTexture(gl.GL_TEXTURE_1D, self.colourTexture)
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

        
    def addDisplayListeners(self):
        """Called by :meth:`init`.

        Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.Display` object, and the
        associated :class:`~fsl.fslview.displaycontext.volumeopts.VolumeOpts`
        instance, which define how the image should be displayed.

        This is done so we can update the colour, vertex, and image data when
        display properties are changed.
        """

        display = self.display
        opts    = self.displayOpts

        lName = self.name
        
        def vertexUpdate(*a):
            self.setAxes(self.xax, self.yax)

        def colourUpdate(*a):
            self.refreshColourTexture(self.colourResolution)

        display.addListener('transform',     lName, vertexUpdate)
        opts   .addListener('displayRange',  lName, colourUpdate)
        opts   .addListener('clipLow',       lName, colourUpdate)
        opts   .addListener('clipHigh',      lName, colourUpdate)
        opts   .addListener('cmap',          lName, colourUpdate)
        opts   .addListener('invert',        lName, colourUpdate)


    def removeDisplayListeners(self):
        """Called by :meth:`destroy`. Removes all the property listeners that
        were added by :meth:`addDisplayListeners`.
        """

        display = self.display
        opts    = self.displayOpts

        lName = self.name

        display.removeListener('transform',     lName)
        opts   .removeListener('displayRange',  lName)
        opts   .removeListener('clipLow',       lName)
        opts   .removeListener('clipHigh',      lName)
        opts   .removeListener('cmap',          lName)
        opts   .removeListener('invert',        lName)
