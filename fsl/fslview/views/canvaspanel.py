#!/usr/bin/env python
#
# canvaspanel.py - Base class for all panels that display image data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasPanel` class, which is the base
class for all panels which display image data (e.g. the
:class:`~fsl.fslview.views.orthopanel.OrthoPanel` and the
:class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`).

Another class, the :class:`ControlStrip` is also defined in this module; it
contains a few buttons allowing the user to configure a :class:`CanvasPanel`
instance.
"""

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.fslview.controlpanel                as controlpanel 
import fsl.fslview.displaycontext              as displayctx
import fsl.fslview.viewpanel                   as viewpanel
import fsl.fslview.controls.imagelistpanel     as imagelistpanel
import fsl.fslview.controls.imagedisplaypanel  as imagedisplaypanel
import fsl.fslview.controls.locationpanel      as locationpanel
import                                            colourbarpanel


class ControlStrip(controlpanel.ControlPanel):
    """
    """

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
            canvasPanel.showImageDisplayPanel = \
                not canvasPanel.showImageDisplayPanel
        def toggleLocation(ev):
            canvasPanel.showLocationPanel = not canvasPanel.showLocationPanel
        def toggleSettings(ev):
            canvasPanel.showSettingsPanel = not canvasPanel.showSettingsPanel 

        self._imageListButton   .Bind(wx.EVT_BUTTON, toggleImageList)
        self._displayPropsButton.Bind(wx.EVT_BUTTON, toggleDisplayProps)
        self._locationButton    .Bind(wx.EVT_BUTTON, toggleLocation)
        self._settingsButton    .Bind(wx.EVT_BUTTON, toggleSettings)
            

class CanvasPanel(viewpanel.ViewPanel):
    """
    """

    
    showCursor = props.Boolean(default=True)

    showColourBar         = props.Boolean(default=False)
    showImageList         = props.Boolean(default=False)
    showLocationPanel     = props.Boolean(default=False)
    showImageDisplayPanel = props.Boolean(default=False)
    showSettingsPanel     = props.Boolean(default=False)

    syncLocation   = displayctx.DisplayContext.getSyncProperty('location')
    syncImageOrder = displayctx.DisplayContext.getSyncProperty('imageOrder')
    syncVolume     = displayctx.DisplayContext.getSyncProperty('volume')
    
    colourBarLocation = props.Choice({
        'top'    : 'Top',
        'bottom' : 'Bottom',
        'left'   : 'Left',
        'right'  : 'Right'})

    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide

    
    _labels = {
        'showCursor'             : 'Show cursor',
        'showColourBar'          : 'Show/hide colour bar',
        'showImageList'          : 'Show/hide image list',
        'showLocationPanel'      : 'Show/hide location panel',
        'showImageDisplayPanel'  : 'Show/hide image display panel',
        'showSettingsPanel'      : 'Show/hide canvas settings',
        'syncLocation'           : 'Synchronise location',
        'syncImageOrder'         : 'Synchronise image order',
        'syncVolume'             : 'Synchronise volume number',
        'colourBarLocation'      : 'Colour bar location',
        'colourBarLabelSide'     : 'Colour bar label side'
    }


    def _createSettingsPanel(self, parent, imageList, displayCtx):
        """
        """

        return props.buildGUI(self._dispSetContainer, self)
        # raise NotImplementedError(
        #     'Subclasses of {} must implement the {} method'.format(
        #         self.__class__.__name__,
        #         '_createSettingsPanel'))


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self.bindProps('syncLocation',
                       displayCtx,
                       displayCtx.getSyncPropertyName('location'))
        self.bindProps('syncImageOrder',
                       displayCtx,
                       displayCtx.getSyncPropertyName('imageOrder'))
        self.bindProps('syncVolume',
                       displayCtx,
                       displayCtx.getSyncPropertyName('volume')) 

        self._canvasContainer  = wx.Panel(self)
        self._listLocContainer = wx.Panel(self)
        self._dispSetContainer = wx.Panel(self)

        self._canvasPanel = wx.Panel(self._canvasContainer)
        
        self._controlPanel = ControlStrip(
            self, imageList, displayCtx, self)
        
        self._imageListPanel = imagelistpanel.ImageListPanel(
            self._listLocContainer, imageList, displayCtx)

        self._locationPanel = locationpanel.LocationPanel(
            self._listLocContainer, imageList, displayCtx) 
        
        self._imageDisplayPanel = imagedisplaypanel.ImageDisplayPanel(
            self._dispSetContainer, imageList, displayCtx)
        
        self._settingsPanel = self._createSettingsPanel(
            self._dispSetContainer, imageList, displayCtx)

        self._listLocSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._listLocContainer.SetSizer(self._listLocSizer)

        self._listLocSizer.Add(self._imageListPanel,
                               flag=wx.EXPAND,
                               proportion=0.5)
        self._listLocSizer.Add(self._locationPanel,
                               flag=wx.EXPAND,
                               proportion=1)

        self._dispSetSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._dispSetContainer.SetSizer(self._dispSetSizer)

        self._dispSetSizer.Add(self._imageDisplayPanel,
                               flag=wx.EXPAND,
                               proportion=1)
        self._dispSetSizer.Add(self._settingsPanel,
                               flag=wx.EXPAND,
                               proportion=0.75)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self._canvasSizer = None
        self._colourBar   = None

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._controlPanel,      flag=wx.EXPAND)
        self._sizer.Add(self._listLocContainer,  flag=wx.EXPAND)
        self._sizer.Add(self._canvasContainer,   flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._dispSetContainer,  flag=wx.EXPAND)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('showColourBar',         lName, self._layout)
        self.addListener('colourBarLocation',     lName, self._layout)
        self.addListener('showImageList',         lName, self._layout)
        self.addListener('showLocationPanel',     lName, self._layout)
        self.addListener('showImageDisplayPanel', lName, self._layout)
        self.addListener('showSettingsPanel',     lName, self._layout)

        self._layout()

        
    def getCanvasPanel(self):
        return self._canvasPanel

    
    def _layout(self, *a):

        self._toggleColourBar()

        if self.showImageList:         self._imageListPanel   .Show(True)
        else:                          self._imageListPanel   .Show(False)
        if self.showLocationPanel:     self._locationPanel    .Show(True)
        else:                          self._locationPanel    .Show(False)
        if self.showImageDisplayPanel: self._imageDisplayPanel.Show(True)
        else:                          self._imageDisplayPanel.Show(False)
        if self.showSettingsPanel:     self._settingsPanel    .Show(True)
        else:                          self._settingsPanel    .Show(False) 

        self._listLocContainer.Layout()
        self._dispSetContainer.Layout()
        self._canvasContainer .Layout()
        self                  .Layout()


    def _toggleColourBar(self):

        if not self.showColourBar:

            if self._colourBar is not None:
                self.unbindProps('colourBarLabelSide',
                                 self._colourBar,
                                 'labelSide')
                self._colourBar.Destroy()
                self._colourBar = None
                
            self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
            self._canvasSizer.Add(self._canvasPanel,
                                  flag=wx.EXPAND,
                                  proportion=1)

            self._canvasContainer.SetSizer(self._canvasSizer)
            return


        if self._colourBar is None:
            self._colourBar = colourbarpanel.ColourBarPanel(
                self._canvasContainer, self._imageList, self._displayCtx)

        self.bindProps('colourBarLabelSide', self._colourBar, 'labelSide') 
            
        if   self.colourBarLocation in ('top', 'bottom'):
            self._colourBar.orientation = 'horizontal'
        elif self.colourBarLocation in ('left', 'right'):
            self._colourBar.orientation = 'vertical'
        
        if self.colourBarLocation in ('top', 'bottom'):
            self._canvasSizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self._canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self._canvasContainer.SetSizer(self._canvasSizer)

        if self.colourBarLocation in ('top', 'left'):
            self._canvasSizer.Add(self._colourBar,   flag=wx.EXPAND)
            self._canvasSizer.Add(self._canvasPanel, flag=wx.EXPAND,
                                  proportion=1)
        else:
            self._canvasSizer.Add(self._canvasPanel, flag=wx.EXPAND,
                                  proportion=1)
            self._canvasSizer.Add(self._colourBar,   flag=wx.EXPAND)
