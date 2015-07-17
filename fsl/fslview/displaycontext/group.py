#!/usr/bin/env python
#
# group.py - Overlay groups
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
import copy

import props

import display as fsldisplay
import            volumeopts


log = logging.getLogger(__name__)



class OverlayGroup(props.HasProperties):

    
    name     = props.String()

    
    overlays = props.List()

    
    # Properties which are linked across all overlays
    enabled    = copy.copy(fsldisplay.Display.enabled)
    alpha      = copy.copy(fsldisplay.Display.alpha)
    brightness = copy.copy(fsldisplay.Display.brightness)
    contrast   = copy.copy(fsldisplay.Display.contrast)


    # Properties which are linked across Image overlays
    volume = copy.copy(volumeopts.ImageOpts.transform)

    
    # Properties which are linked across Volume overlays
    displayRange   = copy.copy(volumeopts.VolumeOpts.displayRange)
    clippingRange  = copy.copy(volumeopts.VolumeOpts.clippingRange)
    invertClipping = copy.copy(volumeopts.VolumeOpts.invertClipping)
    interpolation  = copy.copy(volumeopts.VolumeOpts.interpolation)

    
    # TODO Vector
    # TODO Model
    # TODO Label

    
    def __init__(self, displayCtx, overlayList, number, name=None):

        self.__displayCtx  = displayCtx
        self.__overlayList = overlayList
        self.__number      = number

        if name is not None:
            self.name = name


    def __copy__(self):
        return OverlayGroup(
            self,
            self.__displayCtx,
            self.__overlayList,
            self.__number,
            self.name)

            
    def addOverlay(self, overlay):

        self.overlays.append(overlay)

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        # This is the first overlay to be added - the group
        # should inherit its property values
        if len(self.overlays) == 1: master, slave = display, self

        # Other overlays are already in the group - the
        # new overlay should inherit the group properties
        else:                       master, slave = self, display

        slave.bindProps('enabled',    master)
        slave.bindProps('alpha',      master)
        slave.bindProps('brightness', master)
        slave.bindProps('contrast',   master)


    def removeOverlay(self, overlay):

        self.overlays.remove(overlay)

        display = self.__displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        self.unbindProps('enabled',    display)
        self.unbindProps('alpha',      display)
        self.unbindProps('brightness', display)
        self.unbindProps('contrast',   display)


    def __overlayTypeChanged(self, *a):
        pass
