#!/usr/bin/env python
#
# colourbar.py - Provides the ColourBarPanel, a panel for displaying a colour
#                bar.
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

from fsl.fslview.widgets import TextPanel, ImagePanel


class ColourBarPanel(viewpanel.ViewPanel):
    """A panel which shows a colour bar, depicting the data range of the
    currently selected image.
    """

    orientation = props.Choice({
        'horizontal' : 'Horizontal',
        'vertical'   : 'Vertical'})
    """Draw the colour bar horizontally or vertically. """

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None,
                 orientation='horizontal'):

        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

        self._labelPanel = wx.Panel(  self)
        self._cbPanel    = ImagePanel(self)
        self._minLabel   = TextPanel( self._labelPanel)
        self._maxLabel   = TextPanel( self._labelPanel)
        self._nameLabel  = TextPanel( self._labelPanel)

        self            .SetBackgroundColour('black')
        self._labelPanel.SetBackgroundColour('black')
        self._minLabel  .SetBackgroundColour('black')
        self._maxLabel  .SetBackgroundColour('black')
        self._nameLabel .SetBackgroundColour('black')
        self._nameLabel .SetForegroundColour('white')
        self._minLabel  .SetForegroundColour('white')
        self._maxLabel  .SetForegroundColour('white')

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
        """Removes all registered listeners from the image list, display
        context, and individual images.
        """
        
        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)

        for i in range(len(self._imageList)):
            image   = self._imageList[i]
            display = image.getAttribute('display')

            image.removeListener(  'name',         self._name)
            display.removeListener('cmap',         self._name)
            display.removeListener('displayRange', self._name)

            
    def _layout(self, *a):
        """
        """

        if self.orientation == 'horizontal':
            self._mainSizer  = wx.BoxSizer(wx.VERTICAL)
            self._labelSizer = wx.BoxSizer(wx.HORIZONTAL)
            rangeLabels = (self._minLabel, self._maxLabel)
        else:
            self._mainSizer  = wx.BoxSizer(wx.HORIZONTAL) 
            self._labelSizer = wx.BoxSizer(wx.VERTICAL)
            rangeLabels = (self._maxLabel, self._minLabel)

        self._mainSizer.Add(self._cbPanel,    flag=wx.EXPAND, proportion=1)
        self._mainSizer.Add(self._labelPanel, flag=wx.EXPAND) 

        self._labelSizer.Add(rangeLabels[0],  flag=wx.EXPAND)
        self._labelSizer.Add(self._nameLabel, flag=wx.EXPAND, proportion=1)
        self._labelSizer.Add(rangeLabels[1],  flag=wx.EXPAND) 

        self._nameLabel.SetOrient(self.orientation)
        self._minLabel .SetOrient(self.orientation)
        self._maxLabel .SetOrient(self.orientation)

        self            .SetSizer(self._mainSizer)
        self._labelPanel.SetSizer(self._labelSizer)

        # Fix the minor axis of the colour bar to 25 pixels
        if self.orientation == 'horizontal':
            self._cbPanel.SetSizeHints(-1, 25, -1, 25, -1, -1)
        else:
            self._cbPanel.SetSizeHints(25, -1, 25, -1, -1, -1)

        self._labelPanel.Layout()
        self.Layout()
        self._refreshColourBar()
                          

    def _selectedImageChanged(self, *a):
        """
        """

        for i in range(len(self._imageList)):
            
            image   = self._imageList[i]
            display = image.getAttribute('display')

            if i != self._displayCtx.selectedImage:
                
                display.removeListener('displayRange', self._name)
                display.removeListener('cmap',         self._name)
                image  .removeListener('name',         self._name)
                
            else:
                display.addListener('displayRange',
                                    self._name,
                                    self._displayRangeChanged)
                display.addListener('cmap',
                                    self._name,
                                    self._refreshColourBar)
                image  .addListener('name',
                                    self._name,
                                    self._imageNameChanged) 

        self._imageNameChanged()
        self._displayRangeChanged()
        self._refreshColourBar()


    def _imageNameChanged(self, *a):
        """
        """
        image = self._imageList[self._displayCtx.selectedImage]
        self._nameLabel.SetText(image.name)
        self._labelPanel.Layout()

        
    def _displayRangeChanged(self, *a):
        """
        """
        image   = self._imageList[self._displayCtx.selectedImage]
        display = image.getAttribute('display')

        dmin, dmax = display.displayRange.getRange(0)

        self._minLabel.SetText('{:0.2f}'.format(dmin))
        self._maxLabel.SetText('{:0.2f}'.format(dmax))
        self._labelPanel.Layout()
        

    def _refreshColourBar(self, *a):
        """
        """

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
