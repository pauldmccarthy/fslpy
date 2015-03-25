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

        flags = wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL
        
        self.propSizer.Add(self.dispPanel, border=20, flag=flags)
        self.propSizer.Add(self.divider,              flag=flags)
        self.propSizer.Add(self.optsPanel, border=20, flag=flags) 
        
        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList .addListener('images',
                               self._name,
                               self._selectedImageChanged)

        self._lastImage = None
        self._selectedImageChanged()

        self.Layout()

        pSize = self.propSizer.GetMinSize().Get()
        size  = self.sizer    .GetMinSize().Get()

        self.SetMinSize((max(pSize[0], size[0]),
                         max(pSize[1], size[1]) / 4.0))

        
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
            lastDisplay = self._displayCtx.getDisplayProperties(lastImage)
            lastImage  .removeListener('imageType', self._name)
            lastDisplay.removeListener('transform', self._name)

        display = self._displayCtx.getDisplayProperties(image)
            
        image  .addListener('imageType',
                            self._name,
                            lambda *a: self._updateProps(self.optsPanel, True))
        display.addListener('transform', self._name, self._transformChanged)
        
        self._lastImage = image
        self._updateProps(self.dispPanel, False)
        self._updateProps(self.optsPanel, True)

        
    def _transformChanged(self, *a):
        """Called when the transform setting of the currently selected image
        changes. If affine transformation is selected, interpolation is
        enabled, otherwise interpolation is disabled.
        """
        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        choices = display.getProp('interpolation').getChoices(display)

        if  display.transform in ('none', 'pixdim'):
            display.interpolation = 'none'
            
        elif display.transform == 'affine':
            if 'spline' in choices: display.interpolation = 'spline'
            else:                   display.interpolation = 'linear'

        
    def _updateProps(self, parent, opts):

        import fsl.fslview.layouts as layouts

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        if opts: optObj = display.getDisplayOpts()
        else:    optObj = display

        parent.DestroyChildren()
        
        panel = props.buildGUI(
            parent, optObj, view=layouts.layouts[self, optObj])

        parent.GetSizer().Add(panel, flag=wx.EXPAND, proportion=1)
        panel .Layout()
        parent.Layout()
