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


class DisplayStrip(fslpanel.FSLViewPanel):
    
    def __init__(self, parent, imageList, displayCtx, image, display):
        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)
        
        self.image   = image
        self.display = display

        self.topPanel  = wx.Panel(self)
        self.morePanel = wx.Panel(self)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.topPanel,  flag=wx.EXPAND)
        self.sizer.Add(self.morePanel, flag=wx.EXPAND, proportion=1)
        self.SetSizer(self.sizer)

        self.topMainOptsPanel  = wx.Panel( self.topPanel)
        self.topExtraOptsPanel = wx.Panel( self.topPanel)
        self.moreButton        = wx.Button(self.topPanel,
                                           label='more')

        self.topSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.topSizer.Add(self.topMainOptsPanel,  flag=wx.EXPAND, proportion=1)
        self.topSizer.Add(self.topExtraOptsPanel, flag=wx.EXPAND, proportion=1)
        self.topSizer.Add(self.moreButton,        flag=wx.EXPAND)
        self.topPanel.SetSizer(self.topSizer)

        self.enabled    = wx.CheckBox(self.topMainOptsPanel)
        self.name       = wx.TextCtrl(self.topMainOptsPanel)
        self.alpha      = wx.Slider(  self.topMainOptsPanel,
                                      value=100,
                                      minValue=0,
                                      maxValue=100)
        self.brightness = wx.Slider(  self.topMainOptsPanel,
                                      value=50,
                                      minValue=0,
                                      maxValue=100)
        self.contrast   = wx.Slider(  self.topMainOptsPanel,
                                      value=50,
                                      minValue=0,
                                      maxValue=100)
        

        self.topMainSizer = wx.FlexGridSizer(2, 5)
        self.topMainSizer.AddGrowableCol(1)
        self.topMainSizer.AddGrowableCol(2)
        self.topMainSizer.AddGrowableCol(3)
        self.topMainSizer.AddGrowableCol(4)
        
        self.topMainOptsPanel.SetSizer(self.topMainSizer)
        self.topMainSizer.Add(self.enabled,    flag=wx.EXPAND)
        self.topMainSizer.Add(self.name,       flag=wx.EXPAND)
        self.topMainSizer.Add(self.alpha,      flag=wx.EXPAND)
        self.topMainSizer.Add(self.brightness, flag=wx.EXPAND)
        self.topMainSizer.Add(self.contrast,   flag=wx.EXPAND)

        def label(label):
            return wx.StaticText(self.topMainOptsPanel,
                                 label=label,
                                 style=wx.ALIGN_CENTER_HORIZONTAL)
        
        self.topMainSizer.Add(label(''))
        self.topMainSizer.Add(label('name'),       flag=wx.EXPAND)
        self.topMainSizer.Add(label('alpha'),      flag=wx.EXPAND)
        self.topMainSizer.Add(label('brightness'), flag=wx.EXPAND)
        self.topMainSizer.Add(label('contrast'),   flag=wx.EXPAND)

        props.bindWidget(self.enabled,    display, 'enabled', wx.EVT_CHECKBOX)
        props.bindWidget(self.name,       display, 'name',       wx.EVT_TEXT)
        props.bindWidget(self.alpha,      display, 'alpha',      wx.EVT_SLIDER)
        props.bindWidget(self.brightness, display, 'brightness', wx.EVT_SLIDER)
        props.bindWidget(self.contrast,   display, 'contrast',   wx.EVT_SLIDER)

        image.addListener('imageType', self._name, self._imageTypeChanged)

        self._imageTypeChanged()

        self.Layout()

    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
        self.image.removeListener('imageType', self._name)

        
    def _imageTypeChanged(self, *a):

        pass
        
        # import fsl.fslview.layouts as fsllayouts

        # display      = self._displayCtx.getDisplayProperties(self.image)
        # opts         = display.getDisplayOpts()
        # displayPanel = self._getDisplayPanel(self.image)
        # panelSizer   = displayPanel.GetSizer()

        # item = panelSizer.GetItem(1).GetWindow()
        # panelSizer.Remove(1)
        # item.Destroy()

        # optPropPanel = props.buildGUI(
        #     displayPanel,
        #     opts,
        #     view=fsllayouts.layouts[opts])

        # panelSizer.Add(optPropPanel, flag=wx.EXPAND)

        # displayPanel.Layout()
        # self.Layout()
        # self.GetParent().Layout()


class ImageDisplayPanel(fslpanel.FSLViewPanel):
    """A panel which shows display control options for the currently selected
    image.
    """

    def __init__(self, parent, imageList, displayCtx):
        """Create and lay out an :class:`ImageDisplayPanel`.

        :param parent:     The :mod:`wx` parent object.
        :param imageList:  A :class:`~fsl.data.image.ImageList` instance.
        :param displayCtx: A
                           :class:`~fsl.fslview.displaycontext.DisplayContext`
                           instance. 
        """

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        # a dictionary containing {image : panel} mappings
        self._displayPanels = {}

        self._imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx, False)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.SetSizer(self._sizer)

        self._sizer.Add(self._imageSelect, flag=wx.EXPAND)

        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged)
        
        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        
        # trigger initial display panel creation
        self._imageListChanged()


    def destroy(self):
        """Deregisters property listeners. """
        fslpanel.FSLViewPanel.destroy(self)

        self._imageSelect.destroy()

        for panel in self._displayPanels.values():
            panel.destroy()
        
        self._imageList .removeListener('images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)

        for image in self._imageList:
            image.removeListener('imageType', self._name)
 
        
    def _makeDisplayPanel(self, image):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        :class:`~fsl.data.image.Image` instance. 
        """

        display      = self._displayCtx.getDisplayProperties(image)
        displayPanel = DisplayStrip(self,
                                    self._imageList,
                                    self._displayCtx,
                                    image,
                                    display)

        self._sizer.Add(displayPanel, flag=wx.EXPAND, proportion=1)
        
        return displayPanel

    
    def _getDisplayPanel(self, image):
        """Returns a display panel for the given image. One is created
        if it does not already exist.
        """
        # check to see if a display
        # panel exists for this image
        try: panel = self._displayPanels[image]

        # if one doesn't, make one and 
        # add the image to the list box
        except KeyError:
                
            log.debug('Creating display panel for '
                      'image: {}'.format(image.name))
            panel = self._makeDisplayPanel(image)
            self._displayPanels[image] = panel

        return panel

        
    def _imageListChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.images` list
        changes. Creates/destroys display panels for added/removed images,
        and ensures that the correct display panel is visible.
        """

        # First check to see if there are any display
        # panels for which the corresponding image is
        # no longer present in the list.
        for img, displayPanel in self._displayPanels.items():

            if img not in self._imageList:
                self._sizer.Detach(displayPanel)
                displayPanel.Destroy()
                self._displayPanels.pop(img)
        
        # Now check to see if any images have been added,
        # and we need to create a display panel for them
        for i, image in enumerate(self._imageList):
            self._getDisplayPanel(image)

        # When images are added/removed, the selected image
        # index may not have changed, but the image which
        # said index points to might have. So here we make
        # sure that the correct display panel is visible.
        self._selectedImageChanged()


    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.image.ImageList.selectedImage`
        index changes. Ensures that the correct display panel is visible.
        """

        idx = self._displayCtx.selectedImage

        for i, image in enumerate(self._imageList):

            displayPanel = self._getDisplayPanel(image)
            
            if i == self._displayCtx.selectedImage:
                log.debug('Showing display panel for '
                          'image {} ({})'.format(image.name, idx))
            
            displayPanel.Show(i == idx)

        self.Layout()
