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

        self._moreButton = wx.Button(
            self, label=strings.labels['ImageDisplayToolBar.more'])

        self._displaySizer = wx.GridBagSizer()

        self._sepLine1 = wx.StaticLine(
            self,
            size=(-1, 30),
            style=wx.LI_VERTICAL)
        self._sepLine2 = wx.StaticLine(
            self,
            size=(-1, 30),
            style=wx.LI_VERTICAL) 

        self._displayWidgets = {}
        self._optsWidgets    = {}

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._imageSelect,  flag=wx.ALIGN_CENTRE)
        self._sizer.Add(self._displaySizer, flag=wx.EXPAND, proportion=1)
        self._sizer.Add(self._sepLine2,     flag=wx.ALIGN_CENTRE)
        self._sizer.Add(self._moreButton,   flag=wx.EXPAND)

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
    

    def _imageTypeChanged(self, value, valid, image, name, refresh=True):

        oldOptsWidgets = self._optsWidgets.get(image, None)
        newOptsWidgets = self._makeOptsWidgets(image, self)

        self._optsWidgets[image] = newOptsWidgets

        if oldOptsWidgets is not None:
            for widget, label, _ in oldOptsWidgets:
                widget.Destroy()
                label .Destroy()

        if refresh and (image is self._displayCtx.getSelectedImage()):
            self._showImageWidgets(image)
            

    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.selectedImage`
        index changes. Ensures that the correct display panel is visible.
        """

        image = self._displayCtx.getSelectedImage()

        if image is not None:

            displayWidgets = self._displayWidgets.get(image, None)
            optsWidgets    = self._optsWidgets   .get(image, None)

            if displayWidgets is None:
                displayWidgets = self._makeDisplayWidgets(image, self)
                self._displayWidgets[image] = displayWidgets

            if optsWidgets is None:
                self._imageTypeChanged(None, None, image, None, False)
                image.addListener(
                    'imageType',
                    self._name,
                    self._imageTypeChanged,
                    overwrite=True)

        self._showImageWidgets(image)


    def _showImageWidgets(self, image):

        for i in range(self._displaySizer.GetItemCount()):
            self._displaySizer.Hide(i)

        self._displaySizer.Clear(False)

        if image is None:
            self._displaySizer.Layout()
            self              .Layout()
            return

        displayWidgets = self._displayWidgets[image]
        optsWidgets    = self._optsWidgets[   image]

        for col, (widget, label, flag) in enumerate(displayWidgets):
            self._displaySizer.Add(widget, (0, col), flag=flag)
            self._displaySizer.Add(label,  (1, col), flag=wx.EXPAND)

            widget.Show()
            label .Show()

        self._displaySizer.Add(self._sepLine1,
                               (0, len(displayWidgets)),
                               (2, 1),
                               flag=wx.ALIGN_CENTRE)

        startCol = len(displayWidgets) + 1

        for col, (widget, label, flag) in enumerate(optsWidgets, startCol):
            self._displaySizer.Add(widget, (0, col), flag=flag)
            self._displaySizer.Add(label,  (1, col), flag=wx.EXPAND)
            widget.Show()
            label .Show() 

        self._displaySizer.Layout()            
        self              .Layout()            
            

    def _makeLabel(self, parent, hasProps, propName):
        
        label = wx.StaticText(
            parent, label=strings.properties[hasProps, propName],
            style=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_BOTTOM)
        label.SetFont(label.GetFont().Smaller().Smaller())
        return label

        
    def _makeDisplayWidgets(self, image, parent):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        :class:`~fsl.data.image.Image` instance. 
        """

        display    = self._displayCtx.getDisplayProperties(image)

        enabled    = props.makeWidget(parent, display, 'enabled')
        name       = props.makeWidget(parent, display, 'name')
        imageType  = props.makeWidget(parent, display, 'imageType')
        
        alpha      = props.makeWidget(
            parent, display, 'alpha',      spin=False, showLimits=False)
        brightness = props.makeWidget(
            parent, display, 'brightness', spin=False, showLimits=False)
        contrast   = props.makeWidget(
            parent, display, 'contrast',   spin=False, showLimits=False)

        name.SetMinSize((150, -1))

        def label(prop):
            return self._makeLabel(parent, display, prop)

        widgets = [enabled, name, imageType, alpha, brightness, contrast]
        labels = [label('enabled'),
                  label('name'),
                  label('imageType'),
                  label('alpha'),
                  label('brightness'),
                  label('contrast')]
        flags = [wx.ALIGN_CENTRE,
                 wx.EXPAND,
                 wx.EXPAND,
                 wx.EXPAND,
                 wx.EXPAND,
                 wx.EXPAND]

        return zip(widgets, labels, flags)

    
    def _makeOptsWidgets(self, image, parent):

        display = self._displayCtx.getDisplayProperties(image)
        opts    = display.getDisplayOpts()
        labels  = []
        widgets = []
        flags   = []

        if display.imageType == 'volume':
            widgets.append(props.makeWidget(parent, opts, 'cmap'))
            labels .append(self._makeLabel( parent, opts, 'cmap'))
            flags  .append(wx.EXPAND)
            
        elif display.imageType == 'mask':
            widgets.append(props.makeWidget(parent, opts, 'colour'))
            labels .append(self._makeLabel( parent, opts, 'colour'))
            flags  .append(wx.ALIGN_CENTRE)
            
        elif display.imageType == 'vector':
            widgets.append(props.makeWidget(parent, opts, 'displayMode'))
            labels .append(self._makeLabel( parent, opts, 'displayMode'))
            flags  .append(wx.EXPAND)

        return zip(widgets, labels, flags)
