#!/usr/bin/env python
#
# imagelistpanel.py - A panel which displays an image list, and a 'console'
# allowing the display properties of each image to be changed, and images
# to be added/removed from the list. 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os

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

        imageNames = [img.name for img in imageList]

        # list box containing the list of images
        self.listBox = elistbox.EditableListBox(
            self, imageNames, imageList, style=elistbox.ELB_REVERSE)

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
        for i,image in enumerate(imageList):
            self._makeDisplayPanel(image)

        self._showDisplayPanel(len(imageList)-1)

        self.Layout()

        
    def _makeDisplayPanel(self, image):
        """
        Creates a panel containing widgets allowing the user to
        edit the display properties of the given image. A reference
        to the panel is added as an attribute of the image.
        """
            
        displayPanel = props.buildGUI(self, image.display)
        self.sizer.Add(displayPanel, flag=wx.EXPAND, proportion=2)
        image.setAttribute(
            'displayPanel_{}'.format(id(self)), displayPanel)
        return displayPanel

        
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
        self._showDisplayPanel(ev.idx)


    def _showDisplayPanel(self, idx):
        """
        Shows the display panel for the image at the specified index.
        """
        
        for i,image in enumerate(self.imageList):
            
            displayPanel = image.getAttribute( 
                'displayPanel_{}'.format(id(self)))
            
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

        # wx wildcard handling is buggy, so i'm disabling it for now
        dlg = wx.FileDialog(self.GetParent(),
                            message='Open image file',
                            defaultDir=lastDir,
#                            wildcard=wildcard,
                            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK: return

        image = fslimage.Image(dlg.GetPath())
        self.imageList.append(image)
        self.listBox.Append(image.name, image)

        self._makeDisplayPanel(image)
        self._showDisplayPanel(len(self.imageList)-1)


    def _imageRemoved(self, ev):
        """
        """

        image        = self.imageList.pop(ev.idx)
        displayPanel = image.getAttribute('displayPanel_{}'.format(id(self)))

        displayPanel.Destroy()
