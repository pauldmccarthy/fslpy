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


import fsl.fslview.toolbar as fsltoolbar
import imageselectpanel    as imageselect
import imagedisplaypanel   as imagedisplay


class ImageDisplayToolBar(fsltoolbar.FSLViewToolBar):
    
    def __init__(self, parent, imageList, displayCtx, viewPanel):

        actionz = {'more' : self.showMoreSettings}
        
        fsltoolbar.FSLViewToolBar.__init__(
            self, parent, imageList, displayCtx, actionz)

        self._imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx, False)

        self._viewPanel      = viewPanel

        self._displayWidgets = {}
        self._optsWidgets    = {}

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        self._displayCtx.addListener(
            'imageOrder',
            self._name,
            self._selectedImageChanged) 
        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged) 

        self._selectedImageChanged()


    def destroy(self):
        """Deregisters property listeners. """
        fsltoolbar.FSLViewToolBar.destroy(self)

        self._imageSelect.destroy()

        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._displayCtx.removeListener('imageOrder',    self._name)

        for image in self._imageList:
            image.removeListener('imageType', self._name)


    def showMoreSettings(self, *a):
        self._viewPanel.togglePanel(imagedisplay.ImageDisplayPanel, True)


    def _imageListChanged(self, *a):

        for image in self._displayWidgets.keys():
            if image not in self._imageList:

                log.debug('Destroying display tools for {}'.format(image))
                
                widgets = self._displayWidgets.pop(image)
                for w, _ in widgets:
                    w.Destroy()
                    
        for image in self._optsWidgets.keys():
            if image not in self._imageList:
                
                log.debug('Destroying options tools for {}'.format(image))

                widgets = self._optsWidgets.pop(image)
                for w, _ in widgets:
                    w.Destroy()                
    

    def _imageTypeChanged(self, value, valid, image, name, refresh=True):

        oldOptsWidgets = self._optsWidgets.get(image, None)
        newOptsWidgets = self._makeOptsWidgets(image, self)

        self._optsWidgets[image] = newOptsWidgets
        
        if refresh and (image is self._displayCtx.getSelectedImage()):
            self._refreshTools(image)

        if oldOptsWidgets is not None:
            for widget, _ in oldOptsWidgets:
                widget.Destroy()
            

    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.selectedImage`
        index changes. Ensures that the correct display panel is visible.
        """

        image = self._displayCtx.getSelectedImage()

        if image is None:
            self.ClearTools()
            return

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
            if widget is not self._imageSelect:
                widget.Show(False)
        self.ClearTools(postevent=False)

        if image is None:
            self.Layout()

        dispWidgets, dispLabels = zip(*self._displayWidgets[image])
        optsWidgets, optsLabels = zip(*self._optsWidgets[   image])

        tools  = list(dispWidgets) + list(optsWidgets)
        labels = list(dispLabels)  + list(optsLabels)

        tools  = [self._imageSelect] + tools
        labels = [None]              + labels

        for tool in tools:
            tool.Show(True) 

        self.SetTools(tools, labels)

        
        
    def _makeDisplayWidgets(self, image, parent):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        :class:`~fsl.data.image.Image` instance. 
        """

        import fsl.fslview.layouts as layouts

        display   = self._displayCtx.getDisplayProperties(image)
        toolSpecs = layouts.layouts[self, display]

        log.debug('Creating display tools for {}'.format(image))
        
        return self.GenerateTools(toolSpecs, display, add=False)

    
    def _makeOptsWidgets(self, image, parent):

        import fsl.fslview.layouts as layouts

        display   = self._displayCtx.getDisplayProperties(image)
        opts      = display.getDisplayOpts()
        toolSpecs = layouts.layouts[self, opts]
        targets   = { s : self if s.key == 'more' else opts for s in toolSpecs}
        
        log.debug('Creating options tools for {}'.format(image))

        return self.GenerateTools(toolSpecs, targets, add=False) 
