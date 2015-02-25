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
        self.GetParent().toggleControlPanel(ImageDisplayPanel, True)
    

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

        self              .Layout()            
        self._displaySizer.Layout()
            

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
        
        alpha      = wx.Slider(parent, value=100, minValue=0, maxValue=100)
        brightness = wx.Slider(parent, value=50,  minValue=0, maxValue=100)
        contrast   = wx.Slider(parent, value=50,  minValue=0, maxValue=100)

        props.bindWidget(alpha,      display, 'alpha',      wx.EVT_SLIDER)
        props.bindWidget(brightness, display, 'brightness', wx.EVT_SLIDER)
        props.bindWidget(contrast,   display, 'contrast',   wx.EVT_SLIDER)

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

        self.divider = wx.StaticLine(
            self.propPanel, size=(-1, -1), style=wx.LI_HORIZONTAL)

        self.sizer     = wx.BoxSizer(wx.VERTICAL)
        self.propSizer = wx.BoxSizer(wx.VERTICAL)
        self.dispSizer = wx.GridBagSizer()
        self.optsSizer = wx.GridBagSizer()
        
        self          .SetSizer(self.sizer)
        self.propPanel.SetSizer(self.propSizer)

        self.sizer.Add(self.imageSelect, flag=wx.EXPAND)
        self.sizer.Add(self.propPanel,   flag=wx.EXPAND, proportion=1)
        
        self.propSizer.Add(self.dispSizer,
                           border=20,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL)

        self.propSizer.Add(self.divider,
                           border=20,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL)
        
        self.propSizer.Add(self.optsSizer,
                           border=10,
                           flag=wx.EXPAND | wx.ALIGN_CENTRE | wx.ALL) 

        displayCtx.addListener('selectedImage',
                               self._name,
                               self._selectedImageChanged)
        imageList .addListener('images',
                               self._name,
                               self._selectedImageChanged)

        self._lastImage = None
        self._selectedImageChanged()


    def _selectedImageChanged(self, *a):

        image     = self._displayCtx.getSelectedImage()
        dispSizer = self.dispSizer
        optsSizer = self.optsSizer
        lastImage = self._lastImage

        if image is None:
            self._lastImage = None
            dispSizer.Clear(True)
            optsSizer.Clear(True)
            self.Layout()
            return

        if image is lastImage:
            return

        if lastImage is not None:
            lastImage.removeListener('imageType', self._name)
            
        image.addListener('imageType',
                          self._name,
                          lambda *a: self._updateProps(True))
        self._lastImage = image
        self._updateProps(False)
        self._updateProps(True)

        
    def _updateProps(self, opts=False):

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        if opts:
            sizer  = self.optsSizer
            optObj = display.getDisplayOpts()
        else:
            sizer  = self.dispSizer
            optObj = display

        propNames = optObj.getAllProperties()[0]

        sizer.Clear(True)
        
        for i, prop in enumerate(propNames):

            widget     = props.makeWidget(    self.propPanel, optObj, prop)
            syncWidget = props.makeSyncWidget(self.propPanel, optObj, prop)
            label      = wx.StaticText(
                self.propPanel, label=strings.properties[optObj, prop])

            sizer.Add(label,      (i, 0), flag=wx.EXPAND)
            sizer.Add(syncWidget, (i, 1), flag=wx.EXPAND)
            sizer.Add(widget,     (i, 2), flag=wx.EXPAND)

        if not sizer.IsColGrowable(2):
            sizer.AddGrowableCol(2)

        sizer.Layout()
        self.propPanel.Layout()
