#!/usr/bin/env python
#
# imagedisplaypanel.py - A panel which shows display control options for the
#                        currently selected image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>

"""A :class:`wx.panel` which shows display control optionns for the currently
selected image - see :attr:`fsl.data.image.ImageList.selectedImage`.
"""

import logging
log = logging.getLogger(__name__)


import wx
import props

import fsl.fslview.panel as fslpanel
import imageselectpanel  as imageselect

    
class ImageDisplayPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, imageList, displayCtx):
        """
        """

        # TODO Ability to link properties across images

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        self.imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx)

        self.propPanel = wx.ScrolledWindow(self)
        self.propPanel.SetScrollRate(0, 5)
        self.dispPanel = wx.Panel(self.propPanel)
        self.optsPanel = wx.Panel(self.propPanel)

        self.divider = wx.StaticLine(
            self.propPanel, size=(-1, -1), style=wx.LI_HORIZONTAL)

        self.sizer     = wx.BoxSizer(wx.VERTICAL)
        self.propSizer = wx.BoxSizer(wx.VERTICAL)
        self.dispSizer = wx.BoxSizer(wx.VERTICAL)
        self.optsSizer = wx.BoxSizer(wx.VERTICAL)
        
        self          .SetSizer(self.sizer)
        self.propPanel.SetSizer(self.propSizer)
        self.dispPanel.SetSizer(self.dispSizer)
        self.optsPanel.SetSizer(self.optsSizer)

        self.sizer.Add(self.imageSelect, flag=wx.EXPAND)
        self.sizer.Add(self.propPanel,   flag=wx.EXPAND, proportion=1)
        
        self.propSizer.Add(self.dispPanel,
                           border=20,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL)

        self.propSizer.Add(self.divider,
                           border=20,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL)

        self.propSizer.Add(self.optsPanel,
                           border=20,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL)        
        
        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList .addListener('images',
                               self._name,
                               self._selectedImageChanged)

        self._lastImage = None
        self._selectedImageChanged()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)

        self._displayCtx.removeListener('selectedImage', self._name)
        self._imageList .removeListener('images',        self._name)
        self.imageSelect.destroy()

        for image in self._imageList:
            image.removeListener('imageType', self._name)


    def _selectedImageChanged(self, *a):

        image     = self._displayCtx.getSelectedImage()
        lastImage = self._lastImage

        if image is None:
            self._lastImage = None
            self.dispPanel.DestroyChildren()
            self.optsPanel.DestroyChildren()
            self.Layout()
            return

        if image is lastImage:
            return

        if lastImage is not None:
            lastImage.removeListener('imageType', self._name)
            
        image.addListener('imageType',
                          self._name,
                          lambda *a: self._updateProps(self.optsPanel, True))
        self._lastImage = image
        self._updateProps(self.dispPanel, False)
        self._updateProps(self.optsPanel, True)

        
    def _updateProps(self, parent, opts):

        import fsl.fslview.layouts as layouts

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        if opts: optObj = display.getDisplayOpts()
        else:    optObj = display

        parent.DestroyChildren()
        
        panel = props.buildGUI(parent, optObj, view=layouts.layouts[optObj])

        parent.GetSizer().Add(panel, flag=wx.EXPAND, proportion=1)
        panel .Layout()
        parent.Layout()
