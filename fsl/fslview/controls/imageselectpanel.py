#!/usr/bin/env python
#
# imageselectpanel.py - A little panel which allows the currently selected
# image to be changed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`ImageSelectPanel` which is a little panel that allows
the currently selected image to be changed.

This panel is not directly accessible by users, but is embedded within other
control panels.
"""

import logging
log = logging.getLogger(__name__)

import wx

import fsl.fslview.controlpanel as controlpanel


class ImageSelectPanel(controlpanel.ControlPanel):
    """A panel which displays the currently selected image,
    and allows it to be changed.
    """

    def __init__(self, parent, imageList, displayCtx):

        controlpanel.ControlPanel.__init__(self, parent, imageList, displayCtx)

        # A button to select the previous image
        self._prevButton = wx.Button(self, label=u'\u25C0',
                                     style=wx.BU_EXACTFIT)

        # A label showing the name of the current image
        self._imageLabel = wx.StaticText(self,
                                         style=wx.ALIGN_CENTRE |
                                         wx.ST_ELLIPSIZE_MIDDLE)

        # A button selecting the next image
        self._nextButton = wx.Button(self, label=u'\u25B6',
                                     style=wx.BU_EXACTFIT)

        self._sizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._prevButton, flag=wx.EXPAND)
        self._sizer.Add(self._imageLabel, flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._nextButton, flag=wx.EXPAND)

        # Make the image name label font a bit smaller
        font = self._imageLabel.GetFont()
        font.SetPointSize(font.GetPointSize() - 2)
        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self._imageLabel.SetFont(font)
        
        self._imageList.addListener(
            'images',
            self._name,
            self._selectedImageChanged)

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)

        self._selectedImageChanged()

        
    def _selectedImageChanged(self, *a):

        idx = self._displayCtx.selectedImage

        if len(self._imageList) == 0:
            self._imageLabel.SetLabel('')
            return

        image = self._imageList[idx]
        self._imageLabel.SetLabel('{}'.format(image.imageFile))

        self.Layout()
        self.Refresh() 
