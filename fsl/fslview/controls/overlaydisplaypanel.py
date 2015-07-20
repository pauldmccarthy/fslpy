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

import pwidgets.widgetlist        as widgetlist

import fsl.utils.typedict         as td
import fsl.data.strings           as strings
import fsl.fslview.panel          as fslpanel
import fsl.fslview.displaycontext as displayctx



log = logging.getLogger(__name__)


_DISPLAY_PROPS = td.TypeDict({
    'Display' : [
        props.Widget('name'),
        props.Widget('overlayType'),
        props.Widget('enabled'),
        props.Widget('alpha',      showLimits=False),
        props.Widget('brightness', showLimits=False),
        props.Widget('contrast',   showLimits=False)],

    'VolumeOpts' : [
        props.Widget('resolution',    showLimits=False),
        props.Widget('transform'),
        props.Widget('volume',        showLimits=False),
        props.Widget('interpolation'),
        props.Widget('cmap'),
        props.Widget('invert'),
        props.Widget('invertClipping'),
        props.Widget('displayRange',  showLimits=False, slider=True),
        props.Widget('clippingRange', showLimits=False, slider=True)],

    'MaskOpts' : [
        props.Widget('resolution', showLimits=False),
        props.Widget('transform'),
        props.Widget('volume',     showLimits=False),
        props.Widget('colour'),
        props.Widget('invert'),
        props.Widget('threshold',  showLimits=False)],

    'RGBVectorOpts' : [
        props.Widget('resolution',    showLimits=False),
        props.Widget('transform'),
        props.Widget('interpolation'),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('modulate'),
        props.Widget('modThreshold', showLimits=False, spin=False)],

    'LineVectorOpts' : [
        props.Widget('resolution',    showLimits=False),
        props.Widget('transform'),
        props.Widget('xColour'),
        props.Widget('yColour'),
        props.Widget('zColour'),
        props.Widget('suppressX'),
        props.Widget('suppressY'),
        props.Widget('suppressZ'),
        props.Widget('directed'),
        props.Widget('lineWidth', showLimits=False),
        props.Widget('modulate'),
        props.Widget('modThreshold', showLimits=False, spin=False)],

    'ModelOpts' : [
        props.Widget('colour'),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False),
        props.Widget('refImage'),
        # props.Widget('showName'),
        props.Widget('coordSpace',
                     enabledWhen=lambda o: o.refImage != 'none')],

    'LabelOpts' : [
        props.Widget('lut'),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False),
        # props.Widget('showNames'),
        props.Widget('resolution',   showLimits=False),
        props.Widget('transform'),
        props.Widget('volume',       showLimits=False)]
})

    
class OverlayDisplayPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx):
        """
        """

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__overlayName = wx.StaticText(self, style=wx.ALIGN_CENTRE)
        self.__widgets     = widgetlist.WidgetList(self)
        self.__sizer       = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__overlayName, flag=wx.EXPAND)
        self.__sizer.Add(self.__widgets,     flag=wx.EXPAND, proportion=1)

        displayCtx .addListener('selectedOverlay',
                                 self._name,
                                 self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                 self._name,
                                 self.__selectedOverlayChanged)

        self.__currentOverlay = None
        self.__selectedOverlayChanged()

        self.Layout()
        self.SetMinSize((100, 50))

        
    def destroy(self):

        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:
            
            display = self._displayCtx.getDisplay(self.__currentOverlay)
            opts    = display.getDisplayOpts()
            
            display.removeListener('overlayType', self._name)
            display.removeListener('name',        self._name)

            if isinstance(opts, displayctx.VolumeOpts):
                opts.removeListener('transform', self._name)

        self.__currentOverlay = None
        fslpanel.FSLViewPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):

        overlay     = self._displayCtx.getSelectedOverlay()
        lastOverlay = self.__currentOverlay

        if overlay is None:
            self.__currentOverlay = None
            self.__overlayName.SetLabel('')
            self.__widgets.Clear()
            self.Layout()
            return

        if overlay is lastOverlay:
            return

        self.__currentOverlay = overlay

        if lastOverlay is not None and \
           lastOverlay in self._overlayList:
            
            lastDisplay = self._displayCtx.getDisplay(lastOverlay)
            lastOpts    = lastDisplay.getDisplayOpts()
            
            lastDisplay.removeListener('overlayType', self._name)
            lastDisplay.removeListener('name',        self._name)

            if isinstance(lastOpts, displayctx.VolumeOpts):
                lastOpts.removeListener('transform', self._name)

        if lastOverlay is not None:
            displayExpanded = self.__widgets.IsExpanded('display')
            optsExpanded    = self.__widgets.IsExpanded('opts')
        else:
            displayExpanded = True
            optsExpanded    = True

        display = self._displayCtx.getDisplay(overlay)
        opts    = display.getDisplayOpts()
            
        display.addListener('overlayType', self._name, self.__ovlTypeChanged)
        display.addListener('name',        self._name, self.__ovlNameChanged) 

        if isinstance(opts, displayctx.VolumeOpts):
            opts.addListener('transform', self._name, self.__transformChanged)
        
        self.__widgets.Clear()
        self.__widgets.AddGroup('display', strings.labels[self, display])
        self.__widgets.AddGroup('opts',    strings.labels[self, opts]) 

        self.__overlayName.SetLabel(display.name)
        self.__updateWidgets(display, 'display')
        self.__updateWidgets(opts,    'opts')


        self.__widgets.Expand('display', displayExpanded)
        self.__widgets.Expand('opts',    optsExpanded)
        
        self.Layout()

        
    def __ovlNameChanged(self, *a):
        
        display = self._displayCtx.getDisplay(self.__currentOverlay)
        self.__overlayName.SetLabel(display.name)
        self.Layout()
        

    def __ovlTypeChanged(self, *a):

        opts = self._displayCtx.getOpts(self.__currentOverlay)
        self.__updateWidgets(opts, 'opts')
        self.Layout()
        

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

        if not isinstance(opts, displayctx.VolumeOpts):
            return

        choices = opts.getProp('interpolation').getChoices(display)

        if  opts.transform in ('none', 'pixdim'):
            opts.interpolation = 'none'
            
        elif opts.transform == 'affine':
            if 'spline' in choices: opts.interpolation = 'spline'
            else:                   opts.interpolation = 'linear'

        
    def __updateWidgets(self, target, groupName):

        self.__widgets.ClearGroup(groupName)

        widgets = _DISPLAY_PROPS[target]
        if isinstance(target, displayctx.RGBVectorOpts):
            print 'bah'
        labels  = [strings.properties[target, w.key] for w in widgets]
        widgets = [props.buildGUI(self.__widgets,
                                  target,
                                  w,
                                  showUnlink=False)
                   for w in widgets]

        for label, widget in zip(labels, widgets):
            self.__widgets.AddWidget(
                widget,
                label,
                groupName=groupName)

        self.Layout()
