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

        self._displayWidgets = {}
        self._optsWidgets    = {}

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
        self.GetParent().togglePanel(imagedisplay.ImageDisplayPanel, True)


    def _imageListChanged(self, *a):

        for image in self._dispWidgets.keys():
            if image not in self._imageList:
                widgets = self._dispWidgets.pop(image)
                for w, _ in widgets:
                    w.Destroy()
                    
        for image in self._optsWidgets.keys():
            if image not in self._imageList:
                widgets = self._optsWidgets.pop(image)
                for w, _ in widgets:
                    w.Destroy()                
    

    def _imageTypeChanged(self, value, valid, image, name, refresh=True):

        oldOptsWidgets = self._optsWidgets.get(image, None)
        newOptsWidgets = self._makeOptsWidgets(image, self)

        self._optsWidgets[image] = newOptsWidgets
        
        if refresh and (image is self._displayCtx.getSelectedImage()):
            self.ClearTools()
            self._refreshTools(image)

        if oldOptsWidgets is not None:
            for widget, _ in oldOptsWidgets:
                widget.Destroy()
            

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

        self._refreshTools(image)


    def _refreshTools(self, image):

        tools = self.GetTools()
        for widget in tools:
            if widget not in (self._imageSelect, self._moreButton):
                widget.Show(False)
        self.ClearTools()

        if image is None:
            self.Layout()

        dispWidgets, dispLabels = zip(*self._displayWidgets[image])
        optsWidgets, optsLabels = zip(*self._optsWidgets[   image])

        tools  = list(dispWidgets) + list(optsWidgets)
        labels = list(dispLabels)  + list(optsLabels)

        tools  = [self._imageSelect] + tools  + [self._moreButton]
        labels = [None]              + labels + [None]

        self.SetTools(tools, labels)

        for tool in tools:
            tool.Show(True)
        
        
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

        widgets = [enabled, name, imageType, alpha, brightness, contrast]
        labels  = [strings.properties[display, 'enabled'],
                   strings.properties[display, 'name'],
                   strings.properties[display, 'imageType'],
                   strings.properties[display, 'alpha'],
                   strings.properties[display, 'brightness'],
                   strings.properties[display, 'contrast']]

        return zip(widgets, labels)

    
    def _makeOptsWidgets(self, image, parent):

        display = self._displayCtx.getDisplayProperties(image)
        opts    = display.getDisplayOpts()
        labels  = []
        widgets = []

        if display.imageType == 'volume':
            widgets.append(props.makeWidget(parent, opts, 'cmap'))
            labels .append(strings.properties[opts, 'cmap'])
            
        elif display.imageType == 'mask':
            widgets.append(props.makeWidget(parent, opts, 'colour'))
            labels .append(strings.properties[opts, 'colour'])
            
        elif display.imageType == 'vector':
            widgets.append(props.makeWidget(parent, opts, 'displayMode'))
            labels .append(strings.properties[opts, 'displayMode'])

        return zip(widgets, labels)
