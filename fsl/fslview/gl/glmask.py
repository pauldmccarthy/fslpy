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

The :class:`GLMask` class uses the functionality of the
:class:`~fsl.fslview.gl.glvolume.GLVolume` class through inheritance.
"""

import logging


import numpy                   as np
import OpenGL.GL               as gl

import fsl.fslview.gl.glvolume as glvolume


log = logging.getLogger(__name__)


class GLMask(glvolume.GLVolume):
    """The :class:`GLMask` class encapsulates logic to render 2D slices of a
    :class:`~fsl.data.image.Image` instance as a binary mask in OpenGL.

    ``GLMask`` is a subclass of the :class:`~fsl.fslview.gl.glvolume.GLVolume
    class. It overrides a few key methods of ``GLVolume``, but most of the
    logic is provided by ``GLVolume``.
    """


    def addDisplayListeners(self):
        """Overrides
        :meth:`~fsl.fslview.gl.glvolume.GLVolume.addDisplayListeners`.

        Adds a bunch of listeners to the
        :class:`~fsl.fslview.displaycontext.Display` object, and the
        associated :class:`~fsl.fslview.displaycontext.maskopts.MaskOpts`
        instance, which define how the mask image should be displayed.
        """
        def vertexUpdate(*a):
            self.setAxes(self.xax, self.yax)

        def imageUpdate(*a):
            self.genImageTexture()
        
        def colourUpdate(*a):
            self.genColourTexture(self.colourResolution)

        lnrName = '{}_{}'.format(type(self).__name__, id(self))

        self.display    .addListener('transform',     lnrName, vertexUpdate)
        self.display    .addListener('interpolation', lnrName, imageUpdate)
        self.display    .addListener('alpha',         lnrName, colourUpdate)
        self.display    .addListener('resolution',    lnrName, imageUpdate)
        self.display    .addListener('volume',        lnrName, imageUpdate)
        self.image      .addListener('data',          lnrName, imageUpdate)
        self.displayOpts.addListener('colour',        lnrName, colourUpdate)
        self.displayOpts.addListener('threshold',     lnrName, colourUpdate)
        self.displayOpts.addListener('invert',        lnrName, colourUpdate)


    def removeDisplayListeners(self):
        """Overrides
        :meth:`~fsl.fslview.gl.glvolume.GLVolume.removeDisplayListeners`.

        Removes all the listeners added by :meth:`addDisplayListeners`.
        """
        
        lnrName = '{}_{}'.format(type(self).__name__, id(self))

        self.display    .removeListener('transform',     lnrName)
        self.display    .removeListener('interpolation', lnrName)
        self.display    .removeListener('alpha',         lnrName)
        self.display    .removeListener('resolution',    lnrName)
        self.display    .removeListener('volume',        lnrName)
        self.image      .removeListener('data',          lnrName)
        self.displayOpts.removeListener('colour',        lnrName)
        self.displayOpts.removeListener('threshold',     lnrName)
        self.displayOpts.removeListener('invert',        lnrName) 

        
    def genColourTexture(self, *a):
        """Overrides
        :meth:`~fsl.fslview.gl.glvolume.GLVolume.genColourTexture`.

        Creates a colour texture which contains the current mask colour,
        and a transformation matrix which maps from the current
        :attr:`~fsl.fslview.displaycontext.maskopts.MaskOpts.threshold` range
        to the texture range, so that voxels within this range are coloured,
        and voxels outside the range are transparent (or vice versa, if the
        :attr:`~fsl.fslview.displaycontext.maskopts.MaskOpts.invert` flag
        is set).
        """

        display = self.display
        opts    = self.displayOpts

        imin = opts.threshold[0]
        imax = opts.threshold[1]

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

        if opts.invert:
            colourmap = np.tile([[0.0, 0.0, 0.0, 0.0]], (2, 1))
            border    = np.array(opts.colour + [display.alpha],
                                 dtype=np.float32)
        else:
            colourmap = np.tile([[opts.colour + [display.alpha]]], (2, 1))
            border    = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)            

        colourmap = np.floor(colourmap * 255)
        colourmap = np.array(colourmap, dtype=np.uint8)
        colourmap = colourmap.ravel('C')


        gl.glBindTexture(gl.GL_TEXTURE_1D, self.colourTexture)

        gl.glTexParameterfv(gl.GL_TEXTURE_1D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            border)
        
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_1D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)

        gl.glTexImage1D(gl.GL_TEXTURE_1D,
                        0,
                        gl.GL_RGBA8,
                        2,
                        0,
                        gl.GL_RGBA,
                        gl.GL_UNSIGNED_BYTE,
                        colourmap)
        gl.glBindTexture(gl.GL_TEXTURE_1D, 0)        
