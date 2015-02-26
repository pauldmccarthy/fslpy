#!/usr/bin/env python
#
# imagedisplaytoolbar.py - A toolbar which shows display control options for
#                          the currently selected image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.panel` which shows display control optionns for the currently
selected image - see :attr:`fsl.data.image.ImageList.selectedImage`.
"""

import logging
log = logging.getLogger(__name__)


import                   wx

import props

import fsl.fslview.panel as fslpanel
import fsl.data.strings  as strings
import imageselectpanel  as imageselect
import imagedisplaypanel as imagedisplay


class ImageDisplayToolBar(fslpanel.FSLViewToolBar):
    
    def __init__(self, parent, imageList, displayCtx):
        fslpanel.FSLViewToolBar.__init__(self, parent, imageList, displayCtx)

        self._imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx, False)

        self._moreButton = wx.Button(self, label=strings.labels[self, 'more'])

        self._dispSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._optsSizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer = wx.WrapSizer(wx.HORIZONTAL)
        self._sizer.Add(self._imageSelect, flag=wx.ALIGN_CENTRE)
        self._sizer.Add(self._dispSizer,   flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._optsSizer,   flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._moreButton,  flag=wx.EXPAND)

        self.SetSizer(self._sizer)

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)

        self._moreButton.Bind(wx.EVT_BUTTON, self._onMoreButton)
        
        self._selectedImageChanged()


    def destroy(self):
        """Deregisters property listeners. """
        fslpanel.FSLViewToolBar.destroy(self)

        self._imageSelect.destroy()

        self._displayCtx.removeListener('selectedImage', self._name)

        for image in self._imageList:
            image.removeListener('imageType', self._name)


    def _onMoreButton(self, ev):
        self.GetParent().toggleControlPanel(
            imagedisplay.ImageDisplayPanel, True)
    

    def _imageTypeChanged(self, value, valid, image, name):
        
        import fsl.fslview.layouts as layouts

        if image is not self._displayCtx.getSelectedImage():
            return

        self._optsSizer.Clear(True)

        display = self._displayCtx.getDisplayProperties(image)
        opts    = display.getDisplayOpts()

        optsPanel = props.buildGUI(
            self,
            opts,
            layouts.layouts[opts, 'toolbar'],
            showUnlink=False)

        self._optsSizer.Add(optsPanel, flag=wx.EXPAND, proportion=1)
        self.Layout()
            

    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.selectedImage`
        index changes. Ensures that the correct display panel is visible.
        """

        import fsl.fslview.layouts as layouts

        image = self._displayCtx.getSelectedImage()

        self._dispSizer.Clear(True)
        self._optsSizer.Clear(True)        

        if image is None:
            self.Layout()
            return

        display  = self._displayCtx.getDisplayProperties(image)
        dispPanel = props.buildGUI(
            self,
            display,
            layouts.layouts[display, 'toolbar'],
            showUnlink=False)

        image.addListener('imageType',
                          self._name,
                          self._imageTypeChanged,
                          overwrite=True)
        
        self._dispSizer.Add(dispPanel, flag=wx.EXPAND, proportion=1)
        self._imageTypeChanged(None, None, image, None)
