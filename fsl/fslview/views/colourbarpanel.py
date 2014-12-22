#!/usr/bin/env python
#
# colourbar.py - Provides the ColourBarPanel, a panel for displaying a colour
#                bar.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`~fsl.fslview.panel.ViewPanel` which renders a colour bar
depicting the colour range of the currently selected image.

This panel is not directly accessible by users (see the
:mod:`~fsl.fslview.views` package ``__init__.py`` file), but is embedded
within other view panels.
"""

import logging
log = logging.getLogger(__name__)

import wx

import fsl.fslview.panel                  as fslpanel
import fsl.fslview.gl.wxglcolourbarcanvas as cbarcanvas


class ColourBarPanel(fslpanel.FSLViewPanel):
    """A panel which shows a colour bar, depicting the data range of the
    currently selected image.
    """

    orientation = cbarcanvas.ColourBarCanvas.orientation
    """Draw the colour bar horizontally or vertically. """

    labelSide   = cbarcanvas.ColourBarCanvas.labelSide
    """Draw colour bar labels on the top/left/right/bottom."""
                  

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 orientation='horizontal'):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self._cbPanel = cbarcanvas.ColourBarCanvas(self)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)
        self._sizer.Add(self._cbPanel, flag=wx.EXPAND, proportion=1)

        self.bindProps('orientation', self._cbPanel)
        self.bindProps('labelSide'  , self._cbPanel)

        self.SetBackgroundColour('black')

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
            display = self._displayCtx.getDisplayProperties(image)

            image.removeListener(  'name',         self._name)
            display.removeListener('cmap',         self._name)
            display.removeListener('displayRange', self._name)

            
    def _layout(self, *a):
        """
        """

        # Fix the minor axis of the colour bar to 75 pixels
        if self.orientation == 'horizontal':
            self._cbPanel.SetSizeHints(-1, 75, -1, 75, -1, -1)
        else:
            self._cbPanel.SetSizeHints(75, -1, 75, -1, -1, -1)

        self.Layout()
        self._refreshColourBar()
                          

    def _selectedImageChanged(self, *a):
        """
        """

        for i in range(len(self._imageList)):
            
            image   = self._imageList[i]
            display = self._displayCtx.getDisplayProperties(image)

            display.removeListener('displayRange', self._name)
            display.removeListener('cmap',         self._name)
            image  .removeListener('name',         self._name)
                
            if i == self._displayCtx.selectedImage:
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
        if len(self._imageList) > 0:
            label = self._displayCtx.getSelectedImage().name
        else:
            label = ''
        self._cbPanel.label = label

        
    def _displayRangeChanged(self, *a):
        """
        """

        if len(self._imageList) > 0:
            image      = self._displayCtx.getSelectedImage()
            display    = self._displayCtx.getDisplayProperties(image)
            dmin, dmax = display.displayRange.getRange(0)
        else:
            dmin, dmax = 0.0, 0.0

        self._cbPanel.vrange.x = (dmin, dmax)


    def _refreshColourBar(self, *a):
        """
        """

        if len(self._imageList) > 0:

            image   = self._displayCtx.getSelectedImage()
            display = self._displayCtx.getDisplayProperties(image)
            cmap    = display.cmap
        else:
            cmap = None

        self._cbPanel.cmap = cmap
