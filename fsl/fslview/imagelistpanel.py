#!/usr/bin/env python
#
# imagelistpanel.py - A panel which displays an image list, and a 'console'
# allowing the display properties of each image to be changed, and images
# to be added/removed from the list.  See fsl.data.fslimage.ImageList.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import os
import os.path as op

import wx

import fsl.data.fslimage  as fslimage
import fsl.data.imagefile as imagefile
import fsl.gui.elistbox   as elistbox
import fsl.props          as props


class ImageListPanel(wx.Panel):
    """
    """
    
    def __init__(self, parent, imageList):
        """
        """
        
        wx.Panel.__init__(self, parent)
        self.imageList = imageList

        imageNames = [img.name                    for img in imageList]
        imagePaths = [img.nibImage.get_filename() for img in imageList]
        imagePaths = map(op.abspath, imagePaths)

        # list box containing the list of images
        self.listBox = elistbox.EditableListBox(
            self,
            imageNames,
            imageList,
            tooltips=imagePaths,
            style=elistbox.ELB_REVERSE | elistbox.ELB_TOOLTIP)

        self.listBox.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._imageSelected)
        self.listBox.Bind(elistbox.EVT_ELB_MOVE_EVENT,   self._imageMoved)
        self.listBox.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self._imageRemoved)
        self.listBox.Bind(elistbox.EVT_ELB_ADD_EVENT,    self._addImage)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.listBox, flag=wx.EXPAND, proportion=1)

        # a panel for each image, containing widgets
        # allowing the image display properties to be
        # changed
        for i, image in enumerate(imageList):
            self._makeDisplayPanel(image)

        self.imageList.addListener(
            'selectedImage',
            '{}_{}'.format(self.__class__.__name__, id(self)),
            self._selectedImageChanged)

        self.imageList.selectedImage = len(imageList) - 1

        self.Layout()

        
    def _selectedImageChanged(self, *a):
        """
        Called when the ImageList.selectedImage property changes.
        Shows the control panel for the currently selected image.
        """
        self._showDisplayPanel(self.imageList.selectedImage)

        
    def _makeDisplayPanel(self, image):
        """
        Creates a panel containing widgets allowing the user to
        edit the display properties of the given image. A reference
        to the panel is added as an attribute of the image.
        """

        parentPanel = wx.Panel(self)
            
        displayPanel = props.buildGUI(parentPanel, image.display)
        imagePanel   = props.buildGUI(parentPanel, image)

        parentSizer = wx.BoxSizer(wx.HORIZONTAL)
        parentPanel.SetSizer(parentSizer)
        parentSizer.Add(displayPanel, flag=wx.EXPAND, proportion=1)
        parentSizer.Add(imagePanel,   flag=wx.EXPAND)

        parentSizer.Layout()
        
        self.sizer.Add(parentPanel, flag=wx.EXPAND, proportion=2)
        image.setAttribute(
            'displayPanel_{}'.format(id(self)), parentPanel)
        return parentPanel

        
    def _imageMoved(self, ev):
        """
        Called when an image name is moved in the ListBox. Reorders the
        ImageList to reflect the change.
        """

        self.imageList.move(ev.oldIdx, ev.newIdx)
        self.Refresh()

        
    def _imageSelected(self, ev):
        """
        Called when an image is selected in the ListBox. Displays the
        corresponding image display configuration panel.
        """
        self.imageList.selectedImage = ev.idx


    def _showDisplayPanel(self, idx):
        """
        Shows the display panel for the image at the specified index.
        """
        
        for i, image in enumerate(self.imageList):
            
            displayPanel = image.getAttribute( 
                'displayPanel_{}'.format(id(self)))

            if i == idx:
                log.debug('Showing display panel '
                          'for image {}'.format(self.imageList[i].name))
            
            displayPanel.Show(i == idx)

        self.listBox.SetSelection(idx)
        self.Layout()
        self.Refresh()

        
    def _addImage(self, ev):
        """
        """
        
        try:    lastDir = self._lastDir
        except: lastDir = os.getcwd()

        wildcard = imagefile.wildcard()

        # TODO wx wildcard handling is buggy,
        # so i'm disabling it for now
        dlg = wx.FileDialog(self.GetParent(),
                            message='Open image file',
                            defaultDir=lastDir,
                            # wildcard=wildcard,
                            style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dlg.ShowModal() != wx.ID_OK: return

        paths = dlg.GetPaths()

        for path in paths:
            image = fslimage.Image(path)
            self.imageList.append(image)
            self.listBox.Append(image.name, image, tooltip=path)

            self._makeDisplayPanel(image)

        self.imageList.selectedImage = len(self.imageList) - 1

        # This panel may have changed size, so
        # tell the parent to lay itself out
        self.GetParent().Layout()
        self.GetParent().Refresh()


    def _imageRemoved(self, ev):
        """
        """

        image        = self.imageList.pop(ev.idx)
        displayPanel = image.getAttribute('displayPanel_{}'.format(id(self)))

        displayPanel.Destroy()

        if len(self.imageList) > 0:
            self.imageList.selectedImage = self.listBox.GetSelection()

        self.GetParent().Layout()
        self.GetParent().Refresh()
