#!/usr/bin/env python
#
# overlaydisplaypanel.py - A panel which shows display control options for the
#                          currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.panel` which shows display control optionns for the currently
selected overlay.
"""

import logging

import wx
import props

import fsl.fslview.panel          as fslpanel
import fsl.fslview.displaycontext as fsldisplay
import overlayselectpanel         as overlayselect


log = logging.getLogger(__name__)

    
class OverlayDisplayPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx):
        """
        """

        # TODO Ability to link properties across images

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.overlaySelect = overlayselect.OverlaySelectPanel(
            self, overlayList, displayCtx)

        self.propPanel = wx.ScrolledWindow(self)
        self.propPanel.SetScrollRate(0, 5)
        self.dispPanel = wx.Panel(self.propPanel)
        self.optsPanel = wx.Panel(self.propPanel)

        self.divider = wx.StaticLine(
            self.propPanel, size=(-1, -1), style=wx.LI_HORIZONTAL)

        self.sizer     = wx.BoxSizer(wx.VERTICAL)
        self.propSizer = wx.BoxSizer(wx.VERTICAL)
        self.dispSizer = wx.BoxSizer(wx.VERTICAL)
        self.optsSizer = wx.BoxSizer(wx.VERTICAL)
        
        self          .SetSizer(self.sizer)
        self.propPanel.SetSizer(self.propSizer)
        self.dispPanel.SetSizer(self.dispSizer)
        self.optsPanel.SetSizer(self.optsSizer)

        self.sizer.Add(self.overlaySelect, flag=wx.EXPAND)
        self.sizer.Add(self.propPanel,     flag=wx.EXPAND, proportion=1)

        flags = wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL
        
        self.propSizer.Add(self.dispPanel, border=20, flag=flags)
        self.propSizer.Add(self.divider,              flag=flags)
        self.propSizer.Add(self.optsPanel, border=20, flag=flags) 
        
        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__lastOverlay = None
        self.__selectedOverlayChanged()

        self.propSizer.Layout()
        self.Layout()
        
        pSize = self.propSizer.GetMinSize().Get()
        size  = self.sizer    .GetMinSize().Get()
        self.SetMinSize((max(pSize[0], size[0]), max(pSize[1], size[1]) + 20))

        
    def destroy(self):

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)
        self.overlaySelect.destroy()

        for ovl in self._overlayList:
            display = self._displayCtx.getDisplay(ovl)
            display.removeListener('overlayType', self._name)

        fslpanel.FSLViewPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):

        overlay     = self._displayCtx.getSelectedOverlay()
        lastOverlay = self.__lastOverlay

        if overlay is None:
            self.__lastOverlay = None
            self.dispPanel.DestroyChildren()
            self.optsPanel.DestroyChildren()
            self.Layout()
            return

        if overlay is lastOverlay:
            return

        if lastOverlay is not None:
            lastDisplay = self._displayCtx.getDisplay(lastOverlay)
            lastOpts    = lastDisplay.getDisplayOpts()
            lastDisplay.removeListener('overlayType', self._name)

            if isinstance(lastOpts, fsldisplay.VolumeOpts):
                lastOpts.removeListener('transform', self._name)

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()
            
        display.addListener('overlayType',
                            self._name,
                            self.__overlayTypeChanged)

        if isinstance(opts, fsldisplay.VolumeOpts):
            opts.addListener('transform', self._name, self.__transformChanged)
        
        self.__lastOverlay = overlay
        self.__updateProps(self.dispPanel, False)
        self.__updateProps(self.optsPanel, True)

    def __overlayTypeChanged(self, *a):
        self.__updateProps(self.optsPanel, True)

        
    def __transformChanged(self, *a):
        """Called when the transform setting of the currently selected overlay
        changes.

        If the current overlay has an :attr:`.Display.overlayType` of
        ``volume``, and the :attr:`.ImageOpts.transform` property has been set
        to ``affine``, the :attr:`.VolumeOpts.interpolation` property is set to
        ``spline``.  Otherwise interpolation is disabled.
        """
        overlay = self._displayCtx.getSelectedOverlay()
        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()

        if not isinstance(opts, fsldisplay.VolumeOpts):
            return

        choices = opts.getProp('interpolation').getChoices(display)

        if  opts.transform in ('none', 'pixdim'):
            opts.interpolation = 'none'
            
        elif opts.transform == 'affine':
            if 'spline' in choices: opts.interpolation = 'spline'
            else:                   opts.interpolation = 'linear'

        
    def __updateProps(self, parent, opts):

        import fsl.fslview.layouts as layouts

        overlay = self._displayCtx.getSelectedOverlay()
        display = self._displayCtx.getDisplay(overlay)

        if opts: optObj = display.getDisplayOpts()
        else:    optObj = display

        parent.DestroyChildren()
        
        panel = props.buildGUI(
            parent, optObj, view=layouts.layouts[self, optObj])

        parent.GetSizer().Add(panel, flag=wx.EXPAND, proportion=1)
        panel .Layout()
        parent.Layout()
