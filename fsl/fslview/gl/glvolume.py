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

import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.textures as textures
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

        
    def init(self):
        """Initialise the OpenGL data required to render the given image.

        The real initialisation takes place in this method - it must
        only be called after an OpenGL context has been created.
        """
        
        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self.addDisplayListeners()

        fslgl.glvolume_funcs.init(self)

        texName = '{}_{}'.format(id(self.image), type(self).__name__)

        self.imageTexture = textures.getTexture(
            textures.ImageTexture,
            texName,
            self.image,
            self.display)

        self.colourTexture = textures.ColourMapTexture(texName)
        
        self.refreshColourTexture()


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

        # Set up the image and colour textures
        self.imageTexture .bindTexture(gl.GL_TEXTURE0)
        self.colourTexture.bindTexture(gl.GL_TEXTURE1)

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

        self.imageTexture .unbindTexture()
        self.colourTexture.unbindTexture()
        
        fslgl.glvolume_funcs.postDraw(self) 


    def destroy(self):
        """This should be called when this :class:`GLVolume` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles).
        """

        textures.deleteTexture(self.imageTexture)
        
        self.colourTexture.destroy()
        self.imageTexture  = None
        self.colourTexture = None
        
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

    
    def refreshColourTexture(self):
        """Configures the colour texture used to colour image voxels.

        Also createss a transformation matrix which transforms an image voxel
        value to the range (0-1), which may then be used as a texture
        coordinate into the colour map texture. This matrix is stored as an
        attribute of this :class:`GLVolume` object called
        :attr:`colourMapXForm`. See also the :meth:`genImageTexture` method
        for more details.
        """

        display = self.display
        opts    = self.displayOpts

        alpha  = display.alpha / 100.0
        cmap   = opts.cmap
        invert = opts.invert
        dmin   = opts.displayRange[0]
        dmax   = opts.displayRange[1]

        self.colourTexture.set(cmap=cmap,
                               invert=invert,
                               alpha=alpha,
                               displayRange=(dmin, dmax))

        
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
            self.refreshColourTexture()

        display.addListener('transform',     lName, vertexUpdate)
        display.addListener('alpha',         lName, colourUpdate)
        opts   .addListener('displayRange',  lName, colourUpdate)
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
        display.removeListener('alpha',         lName)
        opts   .removeListener('displayRange',  lName)
        opts   .removeListener('cmap',          lName)
        opts   .removeListener('invert',        lName)
