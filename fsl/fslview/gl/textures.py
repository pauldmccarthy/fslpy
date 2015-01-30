#!/usr/bin/env python
#
# textures.py - Management of OpenGL image textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for creating OpenGL 3D textures, which contain
3D image data, and which will potentially be shared between multiple GL
canvases.

The main interface to this module comprises two functions:

  - :func:`getTexture`:    Return an :class:`ImageTexture` instance for a
                           particular :class:`~fsl.data.image.Image` instance,
                           creating one if it does not already exist.

  - :func:`deleteTexture`: Cleans up the resources used by an
                           :class:`ImageTexture` instance when it is no longer
                           needed.
"""

import logging

import OpenGL.GL as gl
import numpy     as np

import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform

log = logging.getLogger(__name__)


_allTextures = {}
"""This dictionary contains all of the textures which currently exist. The
key is the texture tag (see :func:`getTexture`), and the value is the
corresponding :class:`ImageTexture` object.
"""


def getTexture(image, tag, *args, **kwargs):
    """Retrieve an :class:`ImageTexture` object for the given image (with
    the given tag), creating one if it does not exist.

    :arg image: A :class:`~fsl.data.image.Image` instance for which a texture
                is needed.
    
    :arg tag:   An application-unique string associated with the given image.
                Future requests for a texture with the same image and tag
                will return the same :class:`ImageTexture` instance.
    """

    tag        = '{}_{}'.format(id(image), tag)
    textureObj = _allTextures.get(tag, None)

    if textureObj is None:
        textureObj = ImageTexture(image, tag, *args, **kwargs)
        _allTextures[tag] = textureObj

    return textureObj


def deleteTexture(texture):
    """Releases the OpenGL memory associated with the given
    :class:`ImageTexture` instance, and removes it from the
    :attr:`_allTextures` dictionary.
    """
    
    texture.destroy()
    _allTextures.pop(texture.tag, None)


class ImageTexture(object):
    """This class contains the logic required to create and manage a 3D
    texture which represents a :class:`~fsl.data.image.Image` instance.

    On creation, an ``ImageTexture`` instance registers some listeners on the
    properties of the :class:`~fsl.data.image.Image` instance (and the
    :class:`~fsl.fslview.displaycontext.Display` instance if one is provided),
    so that it may re-generate the texture data when these properties
    change. For example, if the
    :attr:`~fsl.fslview.displaycontext.Display.resolution` property changes,
    the image data is re-sampled accordingly.

    Once created, the following attributes are available on an
    :class:`ImageTexture` object:

     - ``texture``:     The OpenGL texture identifier. 

     - ``voxValXform``: An affine transformation matrix which encodes an
                        offset and scale, for transforming from the
                        texture values [0.0, 1.0] to the actual data values.
    """
    
    def __init__(self,
                 image,
                 tag,
                 display=None,
                 nvals=1,
                 normalise=False,
                 prefilter=None):
        """Create an :class:`ImageTexture`.

        :arg image:     The :class:`~fsl.data.image.Image` instance.
        
        :arg tag:       The texture tag (see the :func:`getTexture` function).
        
        :arg display:   A :class:`~fsl.fslview.displaycontext.Display`
                        instance which defines how the image is to be
                        displayed, or ``None`` if this image has no display.
          
        :arg nvals:     Number of values per voxel. For example. a normal MRI
                        or fMRI image contains only one value for each voxel.
                        However, DTI data contains three values per voxel.
        
        :arg normalise: If ``True``, the image data is normalised to lie in the
                        range [0.0, 1.0].
        
        :arg prefilter: An optional function which may perform any 
                        pre-processing on the data before it is copied to the 
                        GPU - see the :meth:`_prepareTextureData` method.
        """

        try:
            if nvals > 1 and image.shape[3] != nvals:
                raise RuntimeError()
        except:
            raise RuntimeError('Data shape mismatch: texture '
                               'size {} requested for '
                               'image shape {}'.format(nvals, image.shape))

        self.image     = image
        self.display   = display
        self.tag       = tag
        self.nvals     = nvals
        self.prefilter = prefilter

        dtype = image.data.dtype

        # If the normalise flag is true, or the data is
        # of a type which cannot be stored natively as
        # an OpenGL texture, the data is cast to a
        # standard type, and normalised - see
        # _determineTextureType  and _prepareTextureData
        self.normalise = normalise or dtype not in (np.uint8,
                                                    np.int8,
                                                    np.uint16,
                                                    np.int16)

        texFmt, intFmt, texDtype, voxValXform = self._determineTextureType()

        self.texFmt      = texFmt
        self.texIntFmt   = intFmt
        self.texDtype    = texDtype
        self.voxValXform = voxValXform
        self.texture     = gl.glGenTextures(1)
        
        log.debug('Created GL texture for {}: {}'.format(self.tag,
                                                         self.texture)) 

        self._addListeners()
        self.refreshTexture()


    def destroy(self):
        """Deletes the texture identifier, and removes any property
        listeners which were registered on the ``Image`` and ``Display``
        instances.
        """

        if self.texture is None:
            return

        self._removeListeners()

        log.debug('Deleting GL texture for {}: {}'.format(self.tag,
                                                          self.texture))
        gl.glDeleteTextures(self.texture)
        self.texture = None

    
    def _addListeners(self):
        """Adds listeners to some properties of the ``Image`` and ``Display``
        instances, so this ``ImageTexture`` can re-generate texture data
        when necessary.
        """

        display = self.display
        image   = self.image
        
        def refreshTexture(*a):
            self.refreshTexture()

        name = '{}_{}'.format(type(self).__name__, id(self))

        image.addListener('data', name, refreshTexture)

        if display is not None:
            display.addListener('interpolation', name, refreshTexture)
            display.addListener('volume',        name, refreshTexture)
            display.addListener('resolution',    name, refreshTexture)

        
    def _removeListeners(self):
        """Called by the :meth:`destroy` method. Removes the property
        listeners which were configured by the :meth:`_addListeners`
        method.
        """

        name = '{}_{}'.format(type(self).__name__, id(self))
        
        self.image.removeListener('data', name)

        if self.display is not None:
            self.display.removeListener('interpolation', name)
            self.display.removeListener('volume',        name)
            self.display.removeListener('resolution',    name)


    def _determineTextureType(self):
        """Figures out how the image data should be stored as an OpenGL 3D
        texture.

        Regardless of its native data type, the image data is stored in an
        unsigned integer format. This method figures out the best data type
        to use - if the data is already in an unsigned integer format, it
        may be used as-is. Otherwise, the data needs to be cast and
        potentially normalised before it can be used as texture data.
        
        Internally (e.g. in GLSL shader code), the GPU automatically
        normalises texture data to the range [0.0, 1.0]. This method therefore
        calculates an appropriate transformation matrix which may be used to
        transform these normalised values back to the raw data values.

        .. note::
        
           OpenGL does different things to 3D texture data depending on its
           type: unsigned integer types are normalised from [0, INT_MAX] to
           [0, 1].

           Floating point texture data types are, by default,
           *clamped* (not normalised), to the range [0, 1]! This could be
           overcome by using a more recent versions of OpenGL, or by using
           the ARB.texture_rg.GL_R32F data format. Here, we simply cast
           floating point data to an unsigned integer type, normalise it
           to the appropriate range, and calculate a transformation matrix
           to transform back to the data range.

        This method returns a tuple containing the following:

          - The texture format (e.g. ``GL_RGB``, ``GL_LUMINANCE``)

          - The internal texture format used by OpenGL for storage (e.g.
            ``GL_RGB16``, ``GL_LUMINANCE8``).

          - The raw type of the texture data (e.g. ``GL_UNSIGNED_SHORT``)

          - An affine transformation matrix which encodes an offset and a
            scale, which may be used to transform the texture data from
            the range [0.0, 1.0] to its original range.
        """        

        data  = self.image.data
        dtype = data.dtype
        dmin  = float(data.min())
        dmax  = float(data.max()) 

        # Signed data types are a pain in the arse.
        #
        # TODO It would be nice if you didn't have
        # to perform the data conversion/offset
        # for signed types.

        # Texture data type
        if   self.normalise:     texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint8:  texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.int8:   texDtype = gl.GL_UNSIGNED_BYTE
        elif dtype == np.uint16: texDtype = gl.GL_UNSIGNED_SHORT
        elif dtype == np.int16:  texDtype = gl.GL_UNSIGNED_SHORT

        # The texture format
        if   self.nvals == 1: texFmt = gl.GL_LUMINANCE
        elif self.nvals == 2: texFmt = gl.GL_LUMINANCE_ALPHA
        elif self.nvals == 3: texFmt = gl.GL_RGB
        elif self.nvals == 4: texFmt = gl.GL_RGBA
        else:
            raise ValueError('Cannot create texture representation '
                             'for {} (nvals: {})'.format(self.tag,
                                                         self.nvals))

        # Internal texture format
        if self.nvals == 1:

            if   self.normalise:     intFmt = gl.GL_LUMINANCE8
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16

        elif self.nvals == 2:
            if   self.normalise:     intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.uint8:  intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.int8:   intFmt = gl.GL_LUMINANCE8_ALPHA8
            elif dtype == np.uint16: intFmt = gl.GL_LUMINANCE16_ALPHA16
            elif dtype == np.int16:  intFmt = gl.GL_LUMINANCE16_ALPHA16

        elif self.nvals == 3:
            if   self.normalise:     intFmt = gl.GL_RGB8
            elif dtype == np.uint8:  intFmt = gl.GL_RGB8
            elif dtype == np.int8:   intFmt = gl.GL_RGB8
            elif dtype == np.uint16: intFmt = gl.GL_RGB16
            elif dtype == np.int16:  intFmt = gl.GL_RGB16
            
        elif self.nvals == 4:
            if   self.normalise:     intFmt = gl.GL_RGBA8
            elif dtype == np.uint8:  intFmt = gl.GL_RGBA8
            elif dtype == np.int8:   intFmt = gl.GL_RGBA8
            elif dtype == np.uint16: intFmt = gl.GL_RGBA16
            elif dtype == np.int16:  intFmt = gl.GL_RGBA16 

        # Offsets/scales which can be used to transform from
        # the texture data (which may be offset or normalised)
        # back to the original voxel data
        if   self.normalise:     offset =  dmin
        elif dtype == np.uint8:  offset =  0
        elif dtype == np.int8:   offset = -128
        elif dtype == np.uint16: offset =  0
        elif dtype == np.int16:  offset = -32768

        if   self.normalise:     scale = dmax - dmin
        elif dtype == np.uint8:  scale = 255
        elif dtype == np.int8:   scale = 255
        elif dtype == np.uint16: scale = 65535
        elif dtype == np.int16:  scale = 65535

        voxValXform = transform.scaleOffsetXform(scale, offset)

        return texFmt, intFmt, texDtype, voxValXform


    def _prepareTextureData(self):
        """This method prepares and returns the image data, ready to be
        used as GL texture data.
        
        This process potentially involves:
        
          - Resampling to a different resolution (see the
            :mod:`~fsl.fslview.gl.globject.subsample` function).
        
          - Pre-filtering (see the ``prefilter`` parameter to
            :meth:`__init__`).
        
          - Normalising (if the ``normalise`` parameter to :meth:`__init__`
            was True, or if the image data type cannot be used as-is).
        
          - Casting to a different data type (if the image data type cannot
            be used as-is).
        """

        dtype = self.image.data.dtype

        if self.display is None:
            data = self.image.data
            
        else:
            if self.nvals == 1 and self.image.is4DImage():
                data = globject.subsample(self.image.data,
                                          self.display.resolution,
                                          self.image.pixdim, 
                                          self.display.volume)
            else:
                data = globject.subsample(self.image.data,
                                          self.display.resolution,
                                          self.image.pixdim)

        if self.prefilter is not None:
            data = self.prefilter(data)
        
        if self.normalise:
            dmin = float(data.min())
            dmax = float(data.max())
            if dmax != dmin:
                data = (data - dmin) / (dmax - dmin)
            data = np.round(data * 255)
            data = np.array(data, dtype=np.uint8)
            
        if   dtype == np.uint8:  pass
        elif dtype == np.int8:   data = np.array(data + 128,   dtype=np.uint8)
        elif dtype == np.uint16: pass
        elif dtype == np.int16:  data = np.array(data + 32768, dtype=np.uint16)

        return data

        
    def refreshTexture(self):
        """(Re-)generates the OpenGL image texture used to store the image
        data.
        """

        display   = self.display
        data      = self._prepareTextureData()

        # It is assumed that, for textures with more than one
        # value per voxel (e.g. RGB textures), the data is
        # arranged accordingly, i.e. with the voxel value
        # dimension the fastest changing
        if len(data.shape) == 4: self.textureShape = data.shape[1:]
        else:                    self.textureShape = data.shape

        log.debug('Refreshing 3D texture (id {}) for '
                  '{} (data shape: {})'.format(
                      self.texture,
                      self.tag,
                      self.textureShape))

        # The image data is flattened, with fortran dimension
        # ordering, so the data, as stored on the GPU, has its
        # first dimension as the fastest changing.
        data = data.ravel(order='F')

        # Enable storage of tightly packed data of any size (i.e.
        # our texture shape does not have to be divisible by 4).
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

        # Set up image texture sampling thingos
        # with appropriate interpolation method
        if display is None or display.interpolation == 'none':
            interp = gl.GL_NEAREST
        else:
            interp = gl.GL_LINEAR

        gl.glBindTexture(gl.GL_TEXTURE_3D, self.texture)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           interp)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           interp)

        # Clamp texture borders to the edge
        # values - it is the responsibility
        # of the rendering logic to not draw
        # anything outside of the image space
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_EDGE)

        # create the texture according to
        # the format determined by the
        # _determineTextureType method.
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        self.texIntFmt,
                        self.textureShape[0],
                        self.textureShape[1],
                        self.textureShape[2],
                        0,
                        self.texFmt,
                        self.texDtype,
                        data)

        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
