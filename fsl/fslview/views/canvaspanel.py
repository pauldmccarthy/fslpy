#!/usr/bin/env python
#
# canvaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.fslview.viewpanel                   as viewpanel
import fsl.fslview.controls.canvascontrolpanel as canvascontrolpanel
import fsl.fslview.controls.imagelistpanel     as imagelistpanel
import fsl.fslview.controls.imagedisplaypanel  as imagedisplaypanel
import fsl.fslview.controls.locationpanel      as locationpanel

import colourbarpanel 


class CanvasPanel(viewpanel.ViewPanel):

    
    showCursor = props.Boolean(default=True)

    
    posSync = props.Boolean(default=True)
    """Should the position shown in each of the
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` instances 
    be synchronised to the :class:`~fsl.data.image.ImageList.location`
    :attr:`~fsl.data.image.ImageList.location` property?
    """
    
    showColourBar         = props.Boolean(default=False)
    showImageList         = props.Boolean(default=False)
    showLocationPanel     = props.Boolean(default=False)
    showImageDisplayPanel = props.Boolean(default=False)
    
    colourBarLocation = props.Choice({
        'top'    : 'Top',
        'bottom' : 'Bottom',
        'left'   : 'Left',
        'right'  : 'Right'})

    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide

    
    _labels = {
        'showCursor'         : 'Show cursor',
        'posSync'            : 'Synchronise location',
        'showColourBar'      : 'Show/hide colour bar',
        'colourBarLocation'  : 'Colour bar location',
        'colourBarLabelSide' : 'Colour bar label side'
    } 


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self._canvasContainer  = wx.Panel(self)
        self._listLocContainer = wx.Panel(self)

        self._canvasPanel = wx.Panel(self._canvasContainer)
        
        self._controlPanel = canvascontrolpanel.CanvasControlPanel(
            self, imageList, displayCtx, self)
        
        self._imageListPanel = imagelistpanel.ImageListPanel(
            self._listLocContainer, imageList, displayCtx)
        
        self._imageDisplayPanel = imagedisplaypanel.ImageDisplayPanel(
            self, imageList, displayCtx)
        
        self._locationPanel = locationpanel.LocationPanel(
            self._listLocContainer, imageList, displayCtx)

        self._listLocSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._listLocContainer.SetSizer(self._listLocSizer)

        self._listLocSizer.Add(self._imageListPanel,
                               flag=wx.EXPAND,
                               proportion=0.5)
        self._listLocSizer.Add(self._locationPanel,
                               flag=wx.EXPAND,
                               proportion=1)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self._canvasSizer = None
        self._colourBar   = None

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._controlPanel,      flag=wx.EXPAND)
        self._sizer.Add(self._listLocContainer,  flag=wx.EXPAND)
        self._sizer.Add(self._canvasContainer,   flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._imageDisplayPanel, flag=wx.EXPAND)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('showColourBar',         lName, self._layout)
        self.addListener('colourBarLocation',     lName, self._layout)
        self.addListener('showImageList',         lName, self._layout)
        self.addListener('showLocationPanel',     lName, self._layout)
        self.addListener('showImageDisplayPanel', lName, self._layout)

        self._layout()

        
    def getCanvasPanel(self):
        return self._canvasPanel

    
    def _layout(self, *a):

        self._toggleColourBar()

        if self.showImageList:         self._imageListPanel.Show(   True)
        else:                          self._imageListPanel.Show(   False)
        if self.showLocationPanel:     self._locationPanel.Show(    True)
        else:                          self._locationPanel.Show(    False)
        if self.showImageDisplayPanel: self._imageDisplayPanel.Show(True)
        else:                          self._imageDisplayPanel.Show(False)

        self._listLocContainer.Layout()
        self._canvasContainer.Layout()
        self.Layout()


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
