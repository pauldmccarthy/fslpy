#!/usr/bin/env python
#
# colourbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`~fsl.fslview.viewpanel.ViewPanel` which renders a colour bar
depicting the colour range of the currently selected image.

This panel is not directly accessible by users (see the
:mod:`~fsl.fslview.views` package ``__init__.py`` file), but is embedded
within other control panels.
"""

import logging
log = logging.getLogger(__name__)

import numpy as np
import          wx
import          props 

import fsl.fslview.viewpanel as viewpanel

class ColourBarPanel(viewpanel.ViewPanel):
    """A panel which shows a colour bar, depicting the data range of the currently
    selected image.
    """

    orientation = props.Choice({
        'horizontal' : 'Horizontal',
        'vertical'   : 'Vertical'})

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None,
                 orientation='horizontal'):

        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self._cbContainerPanel = wx.Panel(self)
        self._cbPanel          = ImagePanel(self._cbContainerPanel)
        
        self._minLabel = wx.StaticText(
            self._cbContainerPanel, style=wx.ALIGN_CENTRE_HORIZONTAL)
        
        self._maxLabel = wx.StaticText(
            self._cbContainerPanel, style=wx.ALIGN_CENTRE_HORIZONTAL)
        
        self._imageNameLabel = wx.StaticText(
            self, style=wx.ALIGN_CENTRE_HORIZONTAL)

        self                  .SetBackgroundColour('black')
        self._cbContainerPanel.SetBackgroundColour('black')
        self._minLabel        .SetBackgroundColour('black')
        self._maxLabel        .SetBackgroundColour('black')
        self._imageNameLabel  .SetBackgroundColour('black')
        self._imageNameLabel  .SetForegroundColour('white')
        self._minLabel        .SetForegroundColour('white')
        self._maxLabel        .SetForegroundColour('white')

        self.addListener('orientation', self._name, self._layout)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)
        
        self._imageList .addListener('images',
                                     self._name,
                                     self._selectedImageChanged)
        
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        
        self._layout()
        self._selectedImageChanged()


    def _onDestroy(self, ev):
        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)

        for i in range(len(self._imageList)):
            image   = self._imageList[i]
            display = image.getAttribute('display')

            display.removeListener('cmap',         self._name)
            display.removeListener('displayRange', self._name)

            
    def _layout(self, *a):

        if self.orientation == 'horizontal':
            self._mainSizer = wx.BoxSizer(wx.VERTICAL)
            self._cbSizer   = wx.BoxSizer(wx.HORIZONTAL)
            rangeFlag   = wx.ALIGN_CENTRE_VERTICAL
            rangeLabels = (self._minLabel, self._maxLabel)
            nameFlag    = wx.EXPAND
        else:
            self._mainSizer = wx.BoxSizer(wx.HORIZONTAL) 
            self._cbSizer   = wx.BoxSizer(wx.VERTICAL)
            rangeFlag   = wx.EXPAND
            rangeLabels = (self._maxLabel, self._minLabel)
            nameFlag    = wx.ALIGN_CENTRE_VERTICAL

        self._mainSizer.Add(self._cbContainerPanel,
                            flag=wx.EXPAND,
                            proportion=1)
        self._mainSizer.Add(self._imageNameLabel, flag=nameFlag) 
 

        self._cbSizer.Add(rangeLabels[0], flag=rangeFlag)
        self._cbSizer.Add(self._cbPanel,  flag=wx.EXPAND, proportion=1)
        self._cbSizer.Add(rangeLabels[1], flag=rangeFlag) 


        # TODO: orientation of labels

        self._minLabel      .SetLabel('Min')
        self._maxLabel      .SetLabel('Max')
        self._imageNameLabel.SetLabel('Image Name')

        self                  .SetSizer(self._mainSizer)
        self._cbContainerPanel.SetSizer(self._cbSizer)

        self._cbSizer  .Layout()
        self._mainSizer.Layout()

        self.Layout()
        self._refreshColourBar()
                          

    def _selectedImageChanged(self, *a):

        for i in range(len(self._imageList)):
            
            image   = self._imageList[i]
            display = image.getAttribute('display')

            if i != self._displayCtx.selectedImage:
                
                display.removeListener('displayRange', self._name)
                display.removeListener('cmap',         self._name)
                
            else:
                display.addListener('displayRange',
                                    self._name,
                                    self._refreshColourBar)
                display.addListener('cmap',
                                    self._name,
                                    self._refreshColourBar)
                
        self._refreshColourBar()
        

    def _refreshColourBar(self, *a):

        width  = 256
        height = 30

        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')
        cmap    = display.cmap

        # create image data containing colour values
        # representing the entire colour range
        colours = cmap(np.linspace(0.0, 1.0, width))
        colours = colours[:, :3]
        colours = np.tile(colours, (height, 1, 1))
        colours = colours * 255
        colours = np.array(colours, dtype=np.uint8)

        # make sure the image is oriented correctly
        if self.orientation == 'vertical':
            colours = colours.transpose((1, 0, 2))
            colours = np.flipud(colours)
            width, height = height, width

        # make a wx Bitmap from the colour data
        colours = colours.ravel(order='C')
        bitmap  = wx.BitmapFromBuffer(width, height, colours)

        self._cbPanel.image = bitmap.ConvertToImage()
        self._cbPanel.Draw()
        

class ImagePanel(wx.Panel):
    

    def __init__(self, parent, image=None):

        wx.Panel.__init__(self, parent)
        
        self.image = image

        self.Bind(wx.EVT_PAINT, self.Draw)
        self.Bind(wx.EVT_SIZE,  self._onSize)

        
    def Draw(self, ev=None):
        
        self.ClearBackground()

        if self.image is None:
            return

        if ev is None: dc = wx.ClientDC(self)
        else:          dc = wx.PaintDC( self)
        
        width, height = dc.GetSize().Get()

        if width == 0 or height == 0:
            return

        bitmap = wx.BitmapFromImage(self.image.Scale(width, height))
        
        dc.DrawBitmap(bitmap, 0, 0, False)

        
    def _onSize(self, ev):
        self.Refresh()
        ev.Skip()
