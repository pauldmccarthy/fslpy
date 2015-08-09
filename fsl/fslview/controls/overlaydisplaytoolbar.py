#!/usr/bin/env python
#
# overlaydisplaytoolbar.py - A toolbar which shows display control options for
#                            the currently selected overlay.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.Panel` which shows display control options for the currently
selected overlay.
"""

import logging

import wx

import props

import fsl.fslview.toolbar as fsltoolbar
import fsl.fslview.icons   as icons
import fsl.fslview.actions as actions
import fsl.utils.typedict  as td
import overlaydisplaypanel as overlaydisplay


log = logging.getLogger(__name__)



_TOOLBAR_PROPS = td.TypeDict({
    'Display' : [
        props.Widget('name'),
        props.Widget('overlayType'),
        props.Widget('alpha',      spin=False, showLimits=False),
        props.Widget('brightness', spin=False, showLimits=False),
        props.Widget('contrast',   spin=False, showLimits=False)],

    'VolumeOpts' : [
        props.Widget('cmap'),
        props.Widget('displayRange', showLimits=False),
        actions.ActionButton('VolumeOpts',
                             'resetDisplayRange',
                             icon=icons.findImageFile('resetRange'))],
    

    'MaskOpts' : [
        props.Widget('colour')],

    'VectorOpts' : [
        props.Widget('modulate'),
        props.Widget('modThreshold', showLimits=False, spin=False)],

    'LabelOpts' : [
        props.Widget('lut'),
        props.Widget('outline',
                     enabledWhen=lambda i, sw: not sw,
                     dependencies=[(lambda o: o.display, 'softwareMode')]),
        props.Widget('outlineWidth',
                     enabledWhen=lambda i, sw: not sw,
                     dependencies=[(lambda o: o.display, 'softwareMode')],
                     showLimits=False,
                     spin=False)],

    'ModelOpts' : [
        props.Widget('colour'),
        props.Widget('outline'),
        props.Widget('outlineWidth', showLimits=False, spin=False)]
})


class OverlayDisplayToolBar(fsltoolbar.FSLViewToolBar):
    
    def __init__(self, parent, overlayList, displayCtx, viewPanel):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, overlayList, displayCtx, actionz)

        self.__viewPanel      = viewPanel
        self.__currentOverlay = None

        self._displayCtx.addListener(
            'selectedOverlay',
            self._name,
            self.__selectedOverlayChanged)
        self._overlayList.addListener(
            'overlays',
            self._name,
            self.__selectedOverlayChanged) 

        self.__selectedOverlayChanged()


    def destroy(self):
        """Deregisters property listeners. """

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:

            display = self._displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self._name)
            display.removeListener('enabled',     self._name)

        self.__currentOverlay = None
        self.__viewPanel      = None
            
        fsltoolbar.FSLViewToolBar.destroy(self)


    def showMoreSettings(self, *a):
        self.__viewPanel.togglePanel(overlaydisplay.OverlayDisplayPanel,
                                     floatPane=True)

        
    def __overlayEnableChanged(self, *a):
        display = self._displayCtx.getDisplay(self.__currentOverlay)
        self.Enable(display.enabled)


    def __selectedOverlayChanged(self, *a):
        """Called when the :attr:`.DisplayContext.selectedOverlay`
        index changes. Ensures that the correct display panel is visible.
        """

        if self.__currentOverlay is not None and \
           self.__currentOverlay in self._overlayList:
            display = self._displayCtx.getDisplay(self.__currentOverlay)
            display.removeListener('overlayType', self._name)
            display.removeListener('enabled',     self._name)

        overlay = self._displayCtx.getSelectedOverlay()

        self.__currentOverlay = overlay

        if overlay is None:
            self.ClearTools(destroy=True)
            return

        display = self._displayCtx.getDisplay(overlay)

        display.addListener('enabled',
                            self._name,
                            self.__overlayEnableChanged)
        display.addListener('overlayType',
                            self._name,
                            self.__selectedOverlayChanged)

        self.__showTools(overlay)
        self.Enable(display.enabled)


    def __showTools(self, overlay):

        oldTools = self.GetTools()

        # See long comment at bottom
        def destroyOldTools():
            for t in oldTools:
                t.Destroy()

        for t in oldTools:
            t.Show(False)

        self.ClearTools(destroy=False, postevent=False)

        log.debug('Showing tools for {}'.format(overlay))

        display   = self._displayCtx.getDisplay(overlay)
        opts      = display.getDisplayOpts()
        
        dispSpecs = _TOOLBAR_PROPS[display]
        optsSpecs = _TOOLBAR_PROPS[opts]

        dispTools, dispLabels = zip(*self.GenerateTools(
            dispSpecs, display, add=False))
        optsTools, optsLabels = zip(*self.GenerateTools(
            optsSpecs, opts,    add=False))

        tools  = list(dispTools)  + list(optsTools)
        labels = list(dispLabels) + list(optsLabels)

        # Button which opens the OverlayDisplayPanel
        more = props.buildGUI(
            self,
            self,
            view=actions.ActionButton(self,
                                      'more',
                                      icon=icons.findImageFile('gear32')))

        tools .append(more)
        labels.append(None)

        self.SetTools(tools, labels)
        
        # This method may have been called via an
        # event handler an existing tool in the
        # toolbar - in this situation, destroying
        # that tool will result in nasty crashes,
        # as the wx widget that generated the event
        # will be destroyed while said event is
        # being processed. So we destroy the old
        # tools asynchronously, well after the event
        # which triggered this method call will have
        # returned.
        wx.CallLater(1000, destroyOldTools)
