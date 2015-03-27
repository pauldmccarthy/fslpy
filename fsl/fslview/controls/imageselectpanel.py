#!/usr/bin/env python
#
# imageselectpanel.py - A little panel which allows the currently selected
# image to be changed.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`ImageSelectPanel` which is a little panel that allows
the currently selected image to be changed.

This panel is generally embedded within other control panels.
"""

import logging
log = logging.getLogger(__name__)

import wx

import fsl.fslview.panel as fslpanel


class ImageSelectPanel(fslpanel.FSLViewPanel):
    """A panel which displays the currently selected image,
    and allows it to be changed.
    """

    def __init__(self, parent, imageList, displayCtx, showName=True):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.showName = showName

        # A button to select the previous image
        self._prevButton = wx.Button(self, label=u'\u25C0',
                                     style=wx.BU_EXACTFIT)
        
        # A button selecting the next image
        self._nextButton = wx.Button(self, label=u'\u25B6',
                                     style=wx.BU_EXACTFIT)

        self._sizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._prevButton, flag=wx.EXPAND)
        self._sizer.Add(self._nextButton, flag=wx.EXPAND)

        # bind callbacks for next/prev buttons
        self._nextButton.Bind(wx.EVT_BUTTON, self._onNextButton)
        self._prevButton.Bind(wx.EVT_BUTTON, self._onPrevButton)

        # A label showing the name of the current image
        if not showName:
            self._imageLabel = None
        else:
            self._imageLabel = wx.StaticText(self,
                                             style=wx.ALIGN_CENTRE |
                                             wx.ST_ELLIPSIZE_MIDDLE)

            self._sizer.Insert(1,
                               self._imageLabel,
                               flag=wx.EXPAND,
                               proportion=1)

            # Make the image name label font a bit smaller
            font = self._imageLabel.GetFont()
            font.SetPointSize(font.GetPointSize() - 2)
            font.SetWeight(wx.FONTWEIGHT_LIGHT)
            self._imageLabel.SetFont(font)
        
        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged)

        self._displayCtx.addListener(
            'imageOrder',
            self._name,
            self._imageListChanged) 

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)

        self._imageListChanged()

        self.Layout()
        self.SetMinSize(self._sizer.GetMinSize())


    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)

        self._imageList. removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._displayCtx.removeListener('imageOrder',    self._name)

        # the _imageListChanged method registers
        # a listener on the name of each image
        for image in self._imageList:
            image.removeListener('name', self._name)
 
        
    def _onPrevButton(self, ev):
        """Called when the previous button is pushed. Selects the previous
        image.
        """
        allImages = self._displayCtx.getOrderedImages()
        currImage = self._displayCtx.getSelectedImage()
        currIdx   = allImages.index(currImage)

        if currIdx == 0:
            return

        self._displayCtx.selectImage(allImages[currIdx - 1])

        
    def _onNextButton(self, ev):
        """Called when the previous button is pushed. Selects the next
        image.
        """
        allImages = self._displayCtx.getOrderedImages()
        currImage = self._displayCtx.getSelectedImage()
        currIdx   = allImages.index(currImage)

        if currIdx == len(allImages) - 1:
            return

        self._displayCtx.selectImage(allImages[currIdx + 1]) 


    def _imageListChanged(self, *a):
        """Called when the :class:`~fsl.data.image.ImageList.images`
        list changes.

        Ensures that the currently selected image is displayed on the panel,
        and that listeners are registered on the name property of each image.
        """

        def nameChanged(value, valid, image, name):

            idx = self._imageList.index(image)
            
            # if the name of the currently selected image has changed,
            # make sure that this panel updates to reflect the change
            if idx == self._displayCtx.selectedImage:
                self._selectedImageChanged()

        if self._imageLabel is not None:
            for image in self._imageList:
                image.addListener('name',
                                  self._name,
                                  nameChanged,
                                  overwrite=True)

        self._selectedImageChanged()

        
    def _selectedImageChanged(self, *a):
        """Called when the selected image is changed. Updates the image name
        label.
        """

        allImages = self._displayCtx.getOrderedImages()
        image     = self._displayCtx.getSelectedImage()
        nimgs     = len(allImages)
        
        if nimgs > 0: idx = allImages.index(image)
        else:         idx = -1

        self._prevButton.Enable(nimgs > 0 and idx > 0)
        self._nextButton.Enable(nimgs > 0 and idx < nimgs - 1)

        if self._imageLabel is None:
            return

        if nimgs == 0:
            self._imageLabel.SetLabel('')
            return

        name = image.name
        
        if name is None: name = ''
        self._imageLabel.SetLabel('{}'.format(name))

        self.Layout()
        self.Refresh() 
