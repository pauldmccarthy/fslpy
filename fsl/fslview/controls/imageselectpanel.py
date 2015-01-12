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

    def __init__(self, parent, imageList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

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

        # bind callbacks for next/prev buttons
        self._nextButton.Bind(wx.EVT_BUTTON, self._onNextButton)
        self._prevButton.Bind(wx.EVT_BUTTON, self._onPrevButton)

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

        def onDestroy(ev):
            ev.Skip()

            if ev.GetEventObject() is not self:
                return
            
            self._imageList. removeListener('images',        self._name)
            self._displayCtx.removeListener('selectedImage', self._name)
            self._displayCtx.removeListener('imageOrder',    self._name)

            # the _imageListChanged method registers
            # a listener on the name of each image
            for image in imageList:
                image.removeListener('name', self._name)

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self._imageListChanged()

        
    def _onPrevButton(self, ev):
        """Called when the previous button is pushed. Selects the previous
        image.
        """

        selectedImage = self._displayCtx.selectedImage

        if selectedImage == 0:
            return

        self._displayCtx.selectedImage = selectedImage - 1

        
    def _onNextButton(self, ev):
        """Called when the previous button is pushed. Selects the next
        image.
        """
        
        selectedImage = self._displayCtx.selectedImage

        if selectedImage == len(self._imageList) - 1:
            return

        self._displayCtx.selectedImage = selectedImage + 1


    def _imageListChanged(self, *a):
        """Called when the :class:`~fsl.data.image.ImageList.images`
        list changes.

        Ensures that the currently selected image is displayed on the panel,
        and that listeners are registered on the name property of each image.
        """

        def nameChanged(img):

            idx = self._imageList.index(img)
            
            # if the name of the currently selected image has changed,
            # make sure that this panel updates to reflect the change
            if idx == self._displayCtx.selectedImage:
                self._selectedImageChanged()

        for image in self._imageList:
            image.addListener('name',
                              self._name,
                              lambda c, va, vi, i=image: nameChanged(i),
                              overwrite=True)

        self._selectedImageChanged()

        
    def _selectedImageChanged(self, *a):
        """Called when the selected image is changed. Updates the image name
        label.
        """

        idx   = self._displayCtx.selectedImage
        image = self._displayCtx.getSelectedImage()
        nimgs = len(self._imageList)

        self._prevButton.Enable(nimgs > 0 and idx != 0)
        self._nextButton.Enable(nimgs > 0 and idx != len(self._imageList) - 1)

        if len(self._imageList) == 0:
            self._imageLabel.SetLabel('')
            return

        name = image.name
        
        if name is None: name = ''
        self._imageLabel.SetLabel('{}'.format(name))

        self.Layout()
        self.Refresh() 
