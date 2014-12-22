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
            self, imageList, displayCtx)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        
        self.SetSizer(self._sizer)

        self._sizer.Add(self._imageSelect, flag=wx.EXPAND)

        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged)
 
        self._displayCtx.addListener(
            'imageOrder',
            self._name,
            self._selectedImageChanged)
        
        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        

        def onDestroy(ev):
            ev.Skip()

            # Stupid. Window destroy handlers of a panel
            # get called when children of said panel are
            # destroyed.
            if ev.GetEventObject() != self: return
            
            self._imageList .removeListener('images',        self._name)
            self._displayCtx.removeListener('imageOrder',    self._name)
            self._displayCtx.removeListener('selectedImage', self._name)

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        # trigger initial display panel creation
        self._imageListChanged()

        
    def _makeDisplayPanel(self, image):
        """Creates and returns panel containing widgets allowing
        the user to edit the display properties of the given
        :class:`~fsl.data.image.Image` instance. 
        """
        display      = self._displayCtx.getDisplayProperties(image)
        displayPanel = props.buildGUI(self, display)
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
        self.Refresh()

        # If the image list is empty, or was empty and
        # is now not empty, this panel will have changed
        # size. So we tell our parent to refresh itself
        self.GetParent().Layout()
        self.GetParent().Refresh()
