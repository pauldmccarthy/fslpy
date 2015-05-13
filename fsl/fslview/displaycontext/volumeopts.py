#!/usr/bin/env python
#
# volumeopts.py - Defines the VolumeOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VolumeOpts` class, which contains
display options for rendering :class:`.GLVolume` instances.
"""

import logging

import numpy as np

import props

import fsl.data.image         as fslimage
import fsl.data.strings       as strings
import fsl.fslview.colourmaps as fslcm

import display as fsldisplay


log = logging.getLogger(__name__)


# TODO Define a super/mixin class which
# has a displayRange and colour map. This
# will allow other bits of code which
# need display range/cmap options to
# test for their presence without having
# to explicitly test against the VolumeOpts
# class (and other future *Opts classes
# which have a display range/cmap).


class VolumeOpts(fsldisplay.DisplayOpts):
    """A class which describes how an :class:`.Image` should be displayed.

    This class doesn't have much functionality - it is up to things which
    actually display an :class:`.Image` to adhere to the properties stored in
    the associated :class:`.Display` and :class:`VolumeOpts` object.
    """

    
    displayRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']])
    """Image values which map to the minimum and maximum colour map colours."""

    
    clippingRange = props.Bounds(
        ndims=1,
        labels=[strings.choices['VolumeOpts.displayRange.min'],
                strings.choices['VolumeOpts.displayRange.max']]) 

    
    cmap = props.ColourMap(default=fslcm.getDefault(),
                           cmapNames=fslcm.getColourMaps())
    """The colour map, a :class:`matplotlib.colors.Colourmap` instance."""


    invert = props.Boolean(default=False)
    """Invert the colour map."""

    
    _tooltips = {
        'name'          : 'The name of this image',
        'enabled'       : 'Enable/disable this image',
        'alpha'         : 'Opacity, between 0.0 (transparent) '
                          'and 100.0 (opaque)',
        'displayRange'  : 'Minimum/maximum display values',
        'clipLow'       : 'Do not show image values which are '
                          'lower than the display range',
        'clipHigh'      : 'Do not show image values which are '
                          'higher than the display range', 
        'interpolation' : 'Interpolate between voxel values at '
                          'each displayed real world location',
        'resolution'    : 'Data resolution in voxels',
        'volume'        : 'Volume number (for 4D images)',
        'transform'     : 'The transformation matrix which specifies the '
                          'conversion from voxel coordinates to a real '
                          'world location',
        'imageType'     : 'the type of data contained in the image',
        'cmap'          : 'Colour map'}

    
    _propHelp = _tooltips



    def __init__(self, overlay, display, overlayList, displayCtx, parent=None):
        """Create a :class:`VolumeOpts` instance for the specified image."""

        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('{} can only be used with an {} overlay'.format(
                type(self).__name__, fslimage.Image.__name__)) 

        # Attributes controlling image display. Only
        # determine the real min/max for small images -
        # if it's memory mapped, we have no idea how big
        # it may be! So we calculate the min/max of a
        # sample (either a slice or an image, depending
        # on whether the image is 3D or 4D)
        if np.prod(overlay.shape) > 2 ** 30:
            sample = overlay.data[..., overlay.shape[-1] / 2]
            self.dataMin = float(sample.min())
            self.dataMax = float(sample.max())
        else:
            self.dataMin = float(overlay.data.min())
            self.dataMax = float(overlay.data.max())

        dRangeLen    = abs(self.dataMax - self.dataMin)
        dMinDistance = dRangeLen / 10000.0

        self.clippingRange.xmin = self.dataMin - dMinDistance
        self.clippingRange.xmax = self.dataMax + dMinDistance
        
        # By default, the lowest values
        # in the image are clipped
        self.clippingRange.xlo  = self.dataMin + dMinDistance
        self.clippingRange.xhi  = self.dataMax + dMinDistance

        self.displayRange.xlo  = self.dataMin
        self.displayRange.xhi  = self.dataMax

        # The Display.contrast property expands/contracts
        # the display range, by a scaling factor up to
        # approximately 10.
        self.displayRange.xmin = self.dataMin - 10 * dRangeLen
        self.displayRange.xmax = self.dataMax + 10 * dRangeLen
        
        self.setConstraint('displayRange', 'minDistance', dMinDistance)

        fsldisplay.DisplayOpts.__init__(self,
                                        overlay,
                                        display,
                                        overlayList,
                                        displayCtx,
                                        parent)

        # The displayRange property of every child VolumeOpts
        # instance is linked to the corresponding 
        # Display.brightness/contrast properties, so changes
        # in one are reflected in the other.
        if parent is not None:
            display.addListener('brightness', self.name, self.__briconChanged)
            display.addListener('contrast',   self.name, self.__briconChanged)
            self   .addListener('displayRange',
                                self.name,
                                self.__displayRangeChanged)

            # Because displayRange and bri/con are intrinsically
            # linked, it makes no sense to let the user sync/unsync
            # them independently. So here we are binding the boolean
            # sync properties which control whether the dRange/bricon
            # properties are synced with their parent. So when one
            # property is synced/unsynced, the other ones are too.
            self.bindProps(self   .getSyncPropertyName('displayRange'),
                           display,
                           display.getSyncPropertyName('brightness'))
            self.bindProps(self   .getSyncPropertyName('displayRange'), 
                           display,
                           display.getSyncPropertyName('contrast')) 

    def destroy(self):

        if self.getParent() is not None:
            display = self.display
            display.removeListener('brightness',   self.name)
            display.removeListener('contrast',     self.name)
            self   .removeListener('displayRange', self.name)
            self.unbindProps(self   .getSyncPropertyName('displayRange'),
                             display,
                             display.getSyncPropertyName('brightness'))
            self.unbindProps(self   .getSyncPropertyName('displayRange'), 
                             display,
                             display.getSyncPropertyName('contrast')) 


    def __toggleListeners(self, enable=True):
        """This method enables/disables the property listeners which
        are registered on the :attr:`displayRange` and
        :attr:`.Display.brightness`/:attr:`.Display.contrast`/ properties.
        
        Because these properties are linked via the
        :meth:`__displayRangeChanged` and :meth:`__briconChanged` methods,
        we need to be careful about avoiding recursive callbacks.

        Furthermore, because the properties of both :class:`VolumeOpts` and
        :class:`.Display` instances are possibly synchronised to a parent
        instance (which in turn is synchronised to other children), we need to
        make sure that the property listeners on these other sibling instances
        are not called when our own property values change. So this method
        disables/enables the property listeners on all sibling ``VolumeOpts``
        and ``Display`` instances.
        """

        parent = self.getParent()

        # this is the parent instance
        if parent is None:
            return

        # The parent.getChildren() method will
        # contain this VolumeOpts instance,
        # so the below loop toggles listeners
        # for this instance, the parent instance,
        # and all of the other children of the
        # parent
        peers  = [parent] + parent.getChildren()

        for peer in peers:

            if enable:
                peer.display.enableListener('brightness',   peer.name)
                peer.display.enableListener('contrast',     peer.name)
                peer        .enableListener('displayRange', peer.name)
            else:
                peer.display.disableListener('brightness',   peer.name)
                peer.display.disableListener('contrast',     peer.name)
                peer        .disableListener('displayRange', peer.name) 
                

    def __briconChanged(self, *a):
        """Called when the ``brightness``/``contrast`` properties of the
        :class:`.Display` instance change.
        
        Updates the :attr:`displayRange` property accordingly.

        See :func:`.colourmaps.briconToDisplayRange`.
        """

        dlo, dhi = fslcm.briconToDisplayRange(
            (self.dataMin, self.dataMax),
            self.display.brightness / 100.0,
            self.display.contrast   / 100.0)

        self.__toggleListeners(False)
        self.displayRange.x = [dlo, dhi]
        self.__toggleListeners(True)

        
    def __displayRangeChanged(self, *a):
        """Called when the `attr`:displayRange: property changes.

        Updates the :attr:`.Display.brightness` and :attr:`.Display.contrast`
        properties accordingly.

        See :func:`.colourmaps.displayRangeToBricon`.
        """

        brightness, contrast = fslcm.displayRangeToBricon(
            (self.dataMin, self.dataMax),
            self.displayRange.x)
        
        self.__toggleListeners(False)

        # update bricon
        self.display.brightness = 100 - brightness * 100
        self.display.contrast   = 100 - contrast   * 100

        self.__toggleListeners(True)
