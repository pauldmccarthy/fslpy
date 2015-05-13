#!/usr/bin/env python
#
# glmask.py - OpenGL rendering of a binary mask image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`GLMask` class, which provides functionality
for OpenGL rendering of a 3D volume as a binary mask.

When created, a :class:`GLMask` instance assumes that the provided
:class:`.Image` instance has an ``overlayType`` of ``mask``, and that its
associated :class:`.Display` instance contains a :class:`.MaskOpts` instance,
containing mask-specific display properties.

The :class:`GLMask` class uses the functionality of the :class:`.GLVolume`
class through inheritance.
"""

import logging

import numpy                   as np

import fsl.fslview.gl.glvolume as glvolume


log = logging.getLogger(__name__)


class GLMask(glvolume.GLVolume):
    """The :class:`GLMask` class encapsulates logic to render 2D slices of a
    :class:`.Image` instance as a binary mask in OpenGL.

    ``GLMask`` is a subclass of the :class:`.GLVolume class. It overrides a
    few key methods of ``GLVolume``, but most of the logic is provided by
    ``GLVolume``.
    """


    def addDisplayListeners(self):
        """Overrides :meth:`.GLVolume.addDisplayListeners`.

        Adds a bunch of listeners to the :class:`.Display` object, and the
        associated :class:`.MaskOpts` instance, which define how the mask
        image should be displayed.
        """
        def vertexUpdate(*a):
            self.setAxes(self.xax, self.yax)
            self.onUpdate()

        def colourUpdate(*a):
            self.refreshColourTexture()
            self.onUpdate()

        lnrName = '{}_{}'.format(type(self).__name__, id(self))

        self.display    .addListener('transform',     lnrName, vertexUpdate)
        self.display    .addListener('alpha',         lnrName, colourUpdate)
        self.displayOpts.addListener('colour',        lnrName, colourUpdate)
        self.displayOpts.addListener('threshold',     lnrName, colourUpdate)
        self.displayOpts.addListener('invert',        lnrName, colourUpdate)


    def removeDisplayListeners(self):
        """Overrides :meth:`.GLVolume.removeDisplayListeners`.

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

        
    def refreshColourTexture(self, *a):
        """Overrides :meth:`.GLVolume.refreshColourTexture`.

        Creates a colour texture which contains the current mask colour, and a
        transformation matrix which maps from the current
        :attr:`.MaskOpts.threshold` range to the texture range, so that voxels
        within this range are coloured, and voxels outside the range are
        transparent (or vice versa, if the :attr:`.MaskOpts.invert` flag is
        set).
        """

        display = self.display
        opts    = self.displayOpts
        alpha   = display.alpha / 100.0
        colour  = opts.colour
        dmin    = opts.threshold[0]
        dmax    = opts.threshold[1]
        
        colour[3] = 1.0

        if opts.invert:
            cmap   = np.tile([0.0, 0.0, 0.0, 0.0], (4, 1))
            border = np.array(opts.colour, dtype=np.float32)
        else:
            cmap   = np.tile([opts.colour],        (4, 1))
            border = np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32)

        self.colourTexture.set(cmap=cmap,
                               border=border,
                               displayRange=(dmin, dmax),
                               alpha=alpha)
