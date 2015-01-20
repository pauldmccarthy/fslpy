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

The :class:`GLImage` class makes use of the functions defined in the
:mod:`fsl.fslview.gl.gl14.glimage_funcs` or the
:mod:`fsl.fslview.gl.gl21.glimage_funcs` modules, which provide OpenGL version
specific details for creation/storage of vertex data, and for rendering.

These version dependent modules must provide the following functions:

  - `init(GLImage, xax, yax)`: Perform any necessary initialisation.

  - `destroy(GLimage)`: Perform any necessary clean up.

  - `genVertexData(GLImage)`: Create and prepare vertex and texture
    coordinates, using the :meth:`GLImage.genVertexData` method. 

  - `draw(GLImage, zpos, xform=None)`: Draw a slice of the image at the given
    Z position. If xform is not None, it must be applied as a transformation
    on the vertex coordinates.

Images rendered in essentially the same way, regardless of which OpenGL
version-specific module is used.  The image data itself is stored on the GPU
as a 3D texture, and the current colour map as a 1D texture. A slice through
the texture is rendered using four vertices, located at the respective corners
of the image bounds.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL           as gl
import numpy               as np

import fsl.fslview.gl      as fslgl
import fsl.utils.transform as transform


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

        # Whenever some specific display/image properties
        # change, the 3D image texture must be updated.
        # An attribute is set on the image object so the
        # genImageTexture method can figure out whether
        # or not the image texture needs to be updated
        def markImage(*a):
            image.setAttribute('GLImageDirty', True)

        # Only one 'GLImageDirty' listener, for all GLImage
        # instances, is registered on ecah image/display,
        # so the GLImageDirty attribute is only set once.
        try:    display.addListener('interpolation', 'GLImageDirty', markImage)
        except: pass
        try:    display.addListener('volume',        'GLImageDirty', markImage)
        except: pass
        try:    display.addListener('resolution',    'GLImageDirty', markImage)
        except: pass
        try:    image  .addListener('data',          'GLImageDirty', markImage)
        except: pass


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

        fslgl.glimage_funcs.init(self, xax, yax)

        # Initialise the image data, and
        # generate vertex/texture coordinates
        self.setAxes(xax, yax)

        self.genImageTexture()

        # The colour map, used for converting 
        # image data to a RGBA colour.
        self.colourTexture = gl.glGenTextures(1)

        log.debug('Created GL texture: {}'.format(self.colourTexture))
        
        self.colourResolution = 256
        self.genColourTexture(self.colourResolution)
        
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


    def preDraw(self):
        """Sets up the GL state to draw a slice from this :class:`GLImage`
        instance.
        """
        fslgl.glimage_funcs.preDraw(self)

        
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
        fslgl.glimage_funcs.draw(self, zpos, xform)

        
    def postDraw(self):
        """Clears the GL state after drawing from this :class:`GLImage`
        instance.
        """ 
        fslgl.glimage_funcs.postDraw(self) 


    def destroy(self):
        """This should be called when this :class:`GLImage` object is no
        longer needed. It performs any needed clean up of OpenGL data (e.g.
        deleting texture handles).
        """
        log.debug('Deleting GL texture: {}'.format(self.colourTexture))
        gl.glDeleteTextures(1, self.colourTexture)

        # Another GLImage object may have
        # already deleted the image texture
        try:
            imageTexture = self.image.delAttribute('GLImageTexture')
            log.debug('Deleting GL texture: {}'.format(imageTexture))
            gl.glDeleteTextures(1, imageTexture)
            
        except KeyError:
            pass
        
        fslgl.glimage_funcs.destroy(self)


    def genVertexData(self):
        """Generates coordinates at the corners of the image bounds, along the
        xax/yax plane, which define a slice through the 3D image.

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

        image        = self.image
        xax          = self.xax
        yax          = self.yax
        transformMat = self.display.voxToDisplayMat 
        
        xmin, xmax = transform.axisBounds(image.shape, transformMat, xax)
        ymin, ymax = transform.axisBounds(image.shape, transformMat, yax)

        worldCoords = np.zeros((4, 3), dtype=np.float32)

        worldCoords[0, [xax, yax]] = (xmin, ymin)
        worldCoords[1, [xax, yax]] = (xmin, ymax)
        worldCoords[2, [xax, yax]] = (xmax, ymin)
        worldCoords[3, [xax, yax]] = (xmax, ymax)

        indices = np.arange(0, 4, dtype=np.uint32)

        return worldCoords, None, indices

    
    def _prepareImageTextureData(self, data):
        """Figures out how the image data should be stored as an OpenGL 3D
        texture, and what transformation, if any, will be required to map
        the data into the range (0, 1) for subsequent colour map texture
        lookup.

        OpenGL does different things to 3D texture data depending on its type:
        unsigned integer types are normalised from [0, INT_MAX] to [0, 1].
        This method calculates an appropriate transformation matrix to
        transform the image data to the appropriate texture coordinate range,
        which is then returned by this function, and subsequently used in the
        :func:`draw` function.

        As an aside, floating point texture data types are, by default,
        *clamped* (not normalised), to the range [0, 1]! This can be overcome
        by using a more recent versions of OpenGL, or by using the
        ARB.texture_rg.GL_R32F data format.

        Returns a tuple containing the following:
        
          - The image data, possibly converted to a different type
        
          - An OpenGL identifier to be used as the internal texture type.
        
          - An OpenGL identifier to be used as the external texture type.
        
          - A transformation matrix which should be applied to individual
            voxel values before they are used as lookup values into the
            colour map texture.
        """

        dtype = data.dtype

        # Signed data types are a pain in the arse.
        #
        # TODO It would be nice if you didn't have
        # to perform the data conversion/offset
        # for signed types.
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
            data = (data - dmin) / (dmax - dmin)
            data = np.round(data * 65535)
            data = np.array(data, dtype=np.uint16)

        if   dtype == np.uint8:  offset =  0
        elif dtype == np.int8:   offset = -128
        elif dtype == np.uint16: offset =  0
        elif dtype == np.int16:  offset = -32768
        else:                    offset =  dmin

        if   dtype == np.uint8:  scale = 255
        elif dtype == np.int8:   scale = 255
        elif dtype == np.uint16: scale = 65535
        elif dtype == np.int16:  scale = 65535
        else:                    scale = dmax - dmin

        voxValXform = np.eye(4, dtype=np.float32)
        voxValXform[0, 0] = scale
        voxValXform[3, 0] = offset

        return data, texIntFmt, texExtFmt, voxValXform


    def genImageTexture(self):
        """Generates the OpenGL image texture used to store the data for the
        given image.

        The texture handle is stored as an attribute of the image. If a
        texture handle is already present (i.e. it has been created by another
        GLImage object representing the same image), it is not recreated.

        The transformation matrix generated by the
        :meth:`_prepareImageTextureData` method is saved as an attribute of
        this :class:`GLImage` object called :attr:`voxValXform`. This
        transformation needs to be applied to voxel values when they are
        retrieved from the 3D image texture, in order to recover the actual
        voxel value.
        """

        image   = self.image
        display = self.display
        volume  = display.volume

        resolution = display.resolution

        xstep = np.round(resolution / image.pixdim[0])
        ystep = np.round(resolution / image.pixdim[1])
        zstep = np.round(resolution / image.pixdim[2])

        if xstep < 1: xstep = 1
        if ystep < 1: ystep = 1
        if zstep < 1: zstep = 1

        xstart = xstep / 2
        ystart = ystep / 2
        zstart = zstep / 2

        # we only store a single 3D image
        # in GPU memory at any one time
        if len(image.shape) > 3: imageData = image.data[xstart::xstep,
                                                        ystart::ystep,
                                                        zstart::zstep,
                                                        volume]
        else:                    imageData = image.data[xstart::xstep,
                                                        ystart::ystep,
                                                        zstart::zstep]

        imageData, texIntFmt, texExtFmt, voxValXform = \
            self._prepareImageTextureData(imageData)

        shape                  = imageData.shape
        self.voxValXform       = voxValXform
        self.imageTextureShape = imageData.shape
        self.imageShape        = image.data.shape

        # Check to see if the image texture
        # has already been created
        try:    imageTexture = image.getAttribute('GLImageTexture')
        except: imageTexture = None

        # otherwise, create a new one
        if imageTexture is None:
            imageTexture = gl.glGenTextures(1)
            log.debug('Created GL texture: {}'.format(imageTexture))

        # The image buffer already exists, and is valid
        elif not image.getAttribute('GLImageDirty'):
            self.imageTexture      = imageTexture
            self.imageTextureShape = shape
            return
        
        self.imageTexture      = imageTexture
        self.imageTextureShape = shape

        log.debug('Configuring 3D texture (id {}) for '
                  'image {} (data shape: {})'.format(
                      imageTexture,
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
        if display.interpolation == 'none': interp = gl.GL_NEAREST
        else:                               interp = gl.GL_LINEAR
 
        gl.glBindTexture(gl.GL_TEXTURE_3D, imageTexture)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           interp)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           interp)

        # Make everything outside
        # of the image transparent
        gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            np.array([0, 0, 0, 0], dtype=np.float32))
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_BORDER)

        # create the texture according to
        # the format determined by the
        # _prepareImageTextureData method.
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        texIntFmt,
                        shape[0],
                        shape[1],
                        shape[2],
                        0,
                        gl.GL_LUMINANCE, 
                        texExtFmt,
                        imageData)

        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

        # Add a reference to the texture as an attribute
        # of the image, and mark it as up to date, so other
        # things which want to render the same image data
        # don't need to regenerate the texture
        image.setAttribute('GLImageTexture', imageTexture)
        image.setAttribute('GLImageDirty',   False)

    
    def genColourTexture(self, colourResolution):
        """Configures the colour texture used to colour image voxels.

        Also createss a transformation matrix which transforms an image voxel
        value to the range (0-1), which may then be used as a texture
        coordinate into the colour map texture. This matrix is stored as an
        attribute of this :class:`GLImage` object called
        :attr:`colourMapXForm`. See also the :meth:`genImageTexture` method
        for more details.
        """

        display = self.display
        opts    = display.getDisplayOpts()

        imin = opts.displayRange[0]
        imax = opts.displayRange[1]

        # This transformation is used to transform voxel values
        # from their native range to the range [0.0, 1.0], which
        # is required for texture colour lookup. Values below
        # or above the current display range will be mapped
        # to texture coordinate values less than 0.0 or greater
        # than 1.0 respectively.
        cmapXform = np.identity(4, dtype=np.float32)
        cmapXform[0, 0] = 1.0 / (imax - imin)
        cmapXform[3, 0] = -imin * cmapXform[0, 0]

        self.colourMapXform = cmapXform

        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map
        colourRange     = np.linspace(0.0, 1.0, colourResolution)
        colourmap       = opts   .cmap(colourRange)
        colourmap[:, 3] = display.alpha

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
            self.genImageTexture()
        
        def colourUpdate(*a):
            self.genColourTexture(self.colourResolution)

        image   = self.image
        display = self.display
        opts    = display.getDisplayOpts()
        lnrName = 'GlImage_{}'.format(id(self))

        display.addListener('transform',       lnrName, vertexUpdate)
        display.addListener('interpolation',   lnrName, imageUpdate)
        display.addListener('alpha',           lnrName, colourUpdate)
        opts   .addListener('displayRange',    lnrName, colourUpdate)
        opts   .addListener('clipLow',         lnrName, colourUpdate)
        opts   .addListener('clipHigh',        lnrName, colourUpdate)
        opts   .addListener('cmap',            lnrName, colourUpdate)
        display.addListener('resolution',      lnrName, imageUpdate)
        display.addListener('volume',          lnrName, imageUpdate)
        image  .addListener('data',            lnrName, imageUpdate)
