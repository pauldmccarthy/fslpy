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

        self._sepLine = wx.StaticLine(
            self, size=(-1, 25), style=wx.LI_VERTICAL)

        self._displayPanels = {}
        self._optsPanels    = {}

        self._currentDisplayPanel = None
        self._currentOptsPanel    = None

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self._sizer.Add(self._imageSelect)
        self._sizer.Add((0, 0))
        self._sizer.Add(self._sepLine)
        self._sizer.Add((0, 0))
        self._sizer.Add(self._moreButton)

        self.SetSizer(self._sizer)

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        
        self._selectedImageChanged()


    def destroy(self):
        """Deregisters property listeners. """
        fslpanel.FSLViewToolBar.destroy(self)

        self._imageSelect.destroy()

        self._displayCtx.removeListener('selectedImage', self._name)

        for image in self._imageList:
            image.removeListener('imageType', self._name)


    def _imageTypeChanged(self, value, valid, image, name):

        oldOptsPanel = self._optsPanels.get(image, None)
        newOptsPanel = self._makeOptsPanel(image)
        
        self._optsPanels[image] = newOptsPanel
        
        if oldOptsPanel is not None:
            current = self._sizer.GetItem(3).GetWindow()
            if current is oldOptsPanel:
                self._sizer.Detach(3)
                self._sizer.Insert(3, newOptsPanel, flag=wx.EXPAND)
            oldOptsPanel.Destroy()
            

    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.selectedImage`
        index changes. Ensures that the correct display panel is visible.
        """

        currDispPanel = self._sizer.GetItem(1).GetWindow()
        currOptsPanel = self._sizer.GetItem(3).GetWindow()

        self._sizer.Detach(3)
        self._sizer.Detach(1)

        if currDispPanel is not None: currDispPanel.Show(False)
        if currOptsPanel is not None: currOptsPanel.Show(False) 

        image = self._displayCtx.getSelectedImage()

        if image is None:
            self._sizer.Insert(1, (0, 0))
            self._sizer.Insert(3, (0, 0))
        else:

            displayPanel = self._displayPanels.get(image, None)
            optsPanel    = self._optsPanels   .get(image, None)

            if displayPanel is None:
                displayPanel = self._makeDisplayPanel(image)
                self._displayPanels[image] = displayPanel

            if optsPanel is None:
                optsPanel = self._makeOptsPanel(image)
                self._optsPanels[image] = optsPanel
                
                image.addListener(
                    'imageType',
                    self._name,
                    self._imageTypeChanged,
                    overwrite=True)
                
            self._sizer.Insert(1, displayPanel, flag=wx.EXPAND)
            self._sizer.Insert(3, optsPanel,    flag=wx.EXPAND)

            displayPanel.Show(True)
            optsPanel   .Show(True)

        self.Layout()
            
        
    def _makeDisplayPanel(self, image):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        :class:`~fsl.data.image.Image` instance. 
        """

        display = self._displayCtx.getDisplayProperties(image)
        panel   = wx.Panel(self)
        
        enabled    = props.makeWidget(panel, display, 'enabled')
        name       = props.makeWidget(panel, display, 'name')
        imageType  = props.makeWidget(panel, display, 'imageType')
        
        alpha      = wx.Slider(panel, value=100, minValue=0, maxValue=100)
        brightness = wx.Slider(panel, value=50,  minValue=0, maxValue=100)
        contrast   = wx.Slider(panel, value=50,  minValue=0, maxValue=100)
        
        props.bindWidget(alpha,      display, 'alpha',      wx.EVT_SLIDER)
        props.bindWidget(brightness, display, 'brightness', wx.EVT_SLIDER)
        props.bindWidget(contrast,   display, 'contrast',   wx.EVT_SLIDER)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)

        sizer.Add(enabled,    flag=wx.EXPAND)
        sizer.Add(name,       flag=wx.EXPAND)
        sizer.Add(imageType,  flag=wx.EXPAND)
        sizer.Add(alpha,      flag=wx.EXPAND)
        sizer.Add(brightness, flag=wx.EXPAND)
        sizer.Add(contrast,   flag=wx.EXPAND)

        panel.Layout()

        return panel

    
    def _makeOptsPanel(self, image):

        display = self._displayCtx.getDisplayProperties(image)
        opts    = display.getDisplayOpts()
        panel   = wx.Panel(self)
        widgets = []

        if display.imageType == 'volume':
            widgets.append(props.makeWidget(panel, opts, 'cmap'))
            
        elif display.imageType == 'mask':
            widgets.append(props.makeWidget(panel, opts, 'colour'))
            
        elif display.imageType == 'vector':
            widgets.append(props.makeWidget(panel, opts, 'displayMode'))

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        panel.SetSizer(sizer)

        for w in widgets:
            sizer.Add(w)

        panel.Layout()
        return panel
