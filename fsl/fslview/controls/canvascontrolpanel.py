#!/usr/bin/env python
#
# orthocontrolpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx


import fsl.fslview.controlpanel as controlpanel


class CanvasControlPanel(controlpanel.ControlPanel):

    def __init__(self, parent, imageList, displayCtx, canvasPanel):
        controlpanel.ControlPanel.__init__(self, parent, imageList, displayCtx)

        self._imageListButton    = wx.Button(self, label='IL')
        self._displayPropsButton = wx.Button(self, label='ID')
        self._locationButton     = wx.Button(self, label='LOC')
        self._settingsButton     = wx.Button(self, label='DS')

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._imageListButton)
        self._sizer.Add(self._displayPropsButton)
        self._sizer.Add(self._locationButton)
        self._sizer.Add(self._settingsButton)

        self.SetSizer(self._sizer)
        self.Layout()

        def toggleImageList(ev):
            canvasPanel.showImageList = not canvasPanel.showImageList
        def toggleDisplayProps(ev):
            canvasPanel.showImageDisplayPanel = not canvasPanel.showImageDisplayPanel
        def toggleLocation(ev):
            canvasPanel.showLocationPanel = not canvasPanel.showLocationPanel 

        self._imageListButton   .Bind(wx.EVT_BUTTON, toggleImageList)
        self._displayPropsButton.Bind(wx.EVT_BUTTON, toggleDisplayProps)
        self._locationButton    .Bind(wx.EVT_BUTTON, toggleLocation)
            

