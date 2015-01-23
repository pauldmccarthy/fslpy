#!/usr/bin/env python
#
# textures.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import OpenGL.GL as gl
import numpy     as np

import fsl.fslview.gl.globject as globject
import fsl.utils.transform     as transform

log = logging.getLogger(__name__)


_allTextures = {}


def getImageTexture(image, display, tag):

    tag        = '{}_{}'.format(id(image), tag)
    textureObj = _allTextures.get(tag, None)

    if textureObj is None:
        
        textureObj = ImageTexture(image, display, tag)
        _allTextures[tag] = textureObj

    return textureObj


class ImageTexture(object):
    
    def __init__(self, image, display, tag, normalise=False):

        self.image     = image
        self.display   = display
        self.tag       = '{}_{}'.format(id(image), tag)
        self.dirty     = True
        self.normalise = normalise
        self.texture   = gl.glGenTextures(1)
        
        log.debug('Created GL texture: {}'.format(self.texture))

        self._addListeners()
        self.refreshTexture()


    def destroy(self):

        if self.texture is None:
            return

        self._removeListeners()

        log.debug('Deleting GL texture: {}'.format(self.texture))
        gl.glDeleteTextures(self.texture)
        self.texture = None

    
    def _addListeners(self):

        display = self.display
        image   = self.image
        
        def refreshTexture(*a):
            self.refreshTexture()

        # Whenever some specific display/image properties
        # change, the 3D image texture must be updated.
        display.addListener('interpolation', self.tag, refreshTexture)
        display.addListener('volume',        self.tag, refreshTexture)
        display.addListener('resolution',    self.tag, refreshTexture)
        image  .addListener('data',          self.tag, refreshTexture)

        
    def _removeListeners(self):

        self.display.removeListener('interpolation', self.tag)
        self.display.removeListener('volume',        self.tag)
        self.display.removeListener('resolution',    self.tag)
        self.image  .removeListener('data',          self.tag)


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

        voxValXform = transform.scaleOffsetXform(scale, offset)

        return data, texIntFmt, texExtFmt, voxValXform


    def refreshTexture(self):
        """Generates the OpenGL image texture used to store the data for the
        given image.

        The texture handle is stored as an attribute of the image. If a
        texture handle is already present (i.e. it has been created by another
        GLVolume object representing the same image), it is not recreated.

        The transformation matrix generated by the
        :meth:`_prepareImageTextureData` method is saved as an attribute of
        this :class:`GLVolume` object called :attr:`voxValXform`. This
        transformation needs to be applied to voxel values when they are
        retrieved from the 3D image texture, in order to recover the actual
        voxel value.
        """

        image     = self.image
        display   = self.display
        imageData = globject.subsample(image.data,
                                       display.resolution,
                                       image.pixdim, 
                                       display.volume)

        imageData, texIntFmt, texExtFmt, voxValXform = \
            self._prepareImageTextureData(imageData)

        texDataShape      = imageData.shape
        self.voxValXform  = voxValXform
        self.textureShape = imageData.shape

        log.debug('Refreshing 3D texture (id {}) for '
                  'image {} (data shape: {})'.format(
                      self.texture,
                      image.name,
                      self.textureShape))

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

        gl.glBindTexture(gl.GL_TEXTURE_3D, self.texture)
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
                        texDataShape[0],
                        texDataShape[1],
                        texDataShape[2],
                        0,
                        gl.GL_LUMINANCE, 
                        texExtFmt,
                        imageData)

        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
