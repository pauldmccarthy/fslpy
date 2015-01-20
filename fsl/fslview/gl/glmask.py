#!/usr/bin/env python
#
# glmask.py - OpenGL rendering of a binary mask image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`GLMask` class, which provides functionality
for OpenGL rendering of a 3D volume as a binary mask.

When created, a :class:`GLMask` instance assumes that the provided
:class:`~fsl.data.image.Image` instance has an ``imageType`` of ``mask``, and
that its associated :class:`~fsl.fslview.displaycontext.Display` instance
contains a :class:`~fsl.fslview.displatcontext.maskopts.MaskOpts` instance,
containing mask-specific display properties.

The :class:`GLMask` class is closely based on the
:class:`~fsl.fslview.gl.glvolume.GLVolume` class.
"""

import logging


import numpy                          as np
import OpenGL.GL                      as gl
import OpenGL.GL.ARB.fragment_program as arbfp
import OpenGL.GL.ARB.vertex_program   as arbvp


import fsl.fslview.gl.globject            as globject
import fsl.fslview.gl.gl14.glvolume_funcs as glvolume_funcs
import fsl.utils.transform                as transform


log = logging.getLogger(__name__)


_glmask_vertex_program = glvolume_funcs._glvolume_vertex_program


_glmask_fragment_program = """!!ARBfp1.0


"""


class GLMask(globject.GLObject):
    """
    """
    
    def __init__(self, image, display):
        globject.GLObject.__init__(self, image, display)
        
        self._ready = False

        # Multiple GLMask instances may manage a single image
        # texture - see the comments in GLVolume.__init__.
        def markImage(*a):
            image.setAttribute('GLMaskDirty', True)

        opts = self.displayOpts

        try:    display.addListener('interpolation', 'GLMaskDirty', markImage)
        except: pass
        try:    display.addListener('resolution',    'GLMaskDirty', markImage)
        except: pass
        try:    display.addListener('data',          'GLMaskDirty', markImage)
        except: pass
        try:    opts   .addListener('threshold',     'GLMaskDirty', markImage)
        except: pass 

        
    def ready(self):
        return self._ready


    def init(self, xax, yax):

        image   = self.image
        display = self.display
        opts    = self.displayOpts
        
        self.setAxes(xax, yax)
        self.genImageTexture()

        lName = '{}_{}'.format(type(self).__name__, id(self))
        display.addListener('transform',     lName, self.genVertexData)
        display.addListener('resolution',    lName, self.genImageTexture)
        display.addListener('interpolation', lName, self.genImageTexture)
        display.addListener('volume',        lName, self.genImageTexture)
        opts   .addListener('threshold',     lName, self.genImageTexture)
        image  .addListener('data',          lName, self.genImageTexture)
        
        self._ready = True

    
    def destroy(self):
        """
        """
        # Another GLMask object may have
        # already deleted the image texture
        try:
            imageTexture = self.image.delAttribute('GLMaskTexture')
            log.debug('Deleting GL texture: {}'.format(imageTexture))
            gl.glDeleteTextures(1, imageTexture)
            
        except KeyError:
            pass

        lName = '{}_{}'.format(type(self).__name__, id(self))
        self.display.removeListener('transform',     lName)
        self.display.removeListener('resolution',    lName)
        self.display.removeListener('interpolation', lName)
        self.display.removeListener('volume',        lName)
        self.image  .removeListener('data',          lName) 

    
    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax
        self.genVertexData()

        
    def genImageTexture(self, *a):

        image      = self.image
        display    = self.display
        opts       = self.displayOpts
        volume     = display.volume
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

        if len(image.shape) > 3: texData = image.data[xstart::xstep,
                                                      ystart::ystep,
                                                      zstart::zstep,
                                                      volume]
        else:                    texData = image.data[xstart::xstep,
                                                      ystart::ystep,
                                                      zstart::zstep]
        texData = np.array(texData)
        
        try:    imageTexture = image.getAttribute('GLMaskTexture')
        except: imageTexture = None
        
        if imageTexture is None:
            imageTexture = gl.glGenTextures(1)
            log.debug('Created GL texture: {}'.format(imageTexture))

        elif not image.getAttribute('GLMaskDirty'):
            self.imageTexture = imageTexture
            return

        self.imageTexture = imageTexture

        print 'Regen: {}'.format(opts.threshold)

        mask = texData >= opts.threshold

        texShape       = texData.shape
        texData[ mask] = 255
        texData[~mask] = 0
        texData        = np.array(texData, dtype=np.uint8)
        texData        = texData.ravel(order='F')
        
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        gl.glPixelStorei(gl.GL_PACK_ALIGNMENT,   1)

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
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        gl.GL_ALPHA8,
                        texShape[0],
                        texShape[1],
                        texShape[2],
                        0,
                        gl.GL_ALPHA, 
                        gl.GL_UNSIGNED_BYTE,
                        texData)

        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
        
        image.setAttribute('GLMaskTexture', imageTexture)
        image.setAttribute('GLMaskDirty',   False) 
            

    def genVertexData(self, *a):
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

        self.worldCoords = worldCoords
        self.indices     = indices
    

    def preDraw(self):
        
        display = self.display
        opts    = self.displayOpts
        if not display.enabled:
            return

        colour = np.array(opts.colour + [display.alpha], dtype=np.float32)

        if opts.invert: opAlpha = gl.GL_ONE_MINUS_SRC_ALPHA
        else:           opAlpha = gl.GL_SRC_ALPHA 

        gl.glEnable(gl.GL_TEXTURE_3D)
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.imageTexture)

        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_TEXTURE_ENV_MODE, gl.GL_COMBINE)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_COMBINE_RGB,      gl.GL_MODULATE)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_COMBINE_ALPHA,    gl.GL_MODULATE)

        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_SOURCE0_RGB, gl.GL_PRIMARY_COLOR)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_SOURCE0_ALPHA, gl.GL_TEXTURE)
        gl.glTexEnvf(gl.GL_TEXTURE_ENV, gl.GL_OPERAND0_ALPHA, opAlpha)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        
        gl.glColor4f(*colour)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        self.mvmat = gl.glGetFloatv(gl.GL_MODELVIEW_MATRIX)

    
    def draw(self, zpos, xform=None):
        
        display = self.display
        if not display.enabled:
            return
        
        worldCoords  = self.worldCoords
        indices      = self.indices
        worldCoords[:, self.zax] = zpos

        texCoords = transform.transform(worldCoords, display.displayToVoxMat)

        texCoords[:, self.xax] /= self.image.shape[self.xax]
        texCoords[:, self.yax] /= self.image.shape[self.yax]
        texCoords[:, self.zax] /= self.image.shape[self.zax]

        worldCoords = worldCoords.ravel('C')
        texCoords   = texCoords  .ravel('C')

        # TODO need to transform texture coordinates properly,
        # from display to vox, then from vox to sub-sampled
        # vox

        if xform is not None:
            xform = transform.concat(xform, self.mvmat)
            gl.glLoadMatrixf(xform) 

        gl.glVertexPointer(  3, gl.GL_FLOAT, 0, worldCoords)
        gl.glTexCoordPointer(3, gl.GL_FLOAT, 0, texCoords)

        gl.glDrawElements(gl.GL_TRIANGLE_STRIP,
                          len(indices),
                          gl.GL_UNSIGNED_INT,
                          indices) 

    
    def postDraw(self):
        
        display = self.display
        if not display.enabled:
            return

        gl.glPopMatrix()

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)
        gl.glDisableClientState(gl.GL_TEXTURE_COORD_ARRAY)
        gl.glDisable(gl.GL_TEXTURE_3D)
