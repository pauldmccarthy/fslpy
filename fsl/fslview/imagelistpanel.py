#!/usr/bin/env python
#
# imagelistpanel.py - A panel which displays an image list, and a 'console'
# allowing the display properties of each image to be changed, and images
# to be added/removed from the list. 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A panel which displays an image list, and a 'console' allowing the
display properties of each image to be changed, and images
to be added/removed from the list.  See :class:`~fsl.data.fslimage.ImageList`.
"""

import logging
log = logging.getLogger(__name__)

import os.path as op

import wx

import pwidgets.elistbox as elistbox
import props


class ImageListPanel(wx.Panel):
    """A panel which contains a list box displaying the list of loaded images
    and a control panel allowing the display properties of the currently
    selected image to be modified.  The list box allows the image order
    to be changed, and allows images to be added and removed from the list.
    """

    
    def __init__(self, parent, imageList):
        """Create and lay out an :class:`ImageListPanel`.

        :param parent:    The :mod:`wx` parent object.
        :param imageList: A :class:`~fsl.data.fslimage.ImageList` instance.
        """
        
        wx.Panel.__init__(self, parent)
        self._imageList = imageList

        self._name = '{}_{}'.format(self.__class__.__name__, id(self))

        # list box containing the list of images - it 
        # is populated in the _imageListChanged method
        self._listBox = elistbox.EditableListBox(
            self,
            style=elistbox.ELB_REVERSE | elistbox.ELB_TOOLTIP)

        # listeners for when the user does
        # something with the list box
        self._listBox.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._imageSelected)
        self._listBox.Bind(elistbox.EVT_ELB_MOVE_EVENT,   self._imageMoved)
        self._listBox.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self._imageRemoved)
        self._listBox.Bind(elistbox.EVT_ELB_ADD_EVENT,    self._addImage)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._listBox, flag=wx.EXPAND, proportion=1)

        self._imageList.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)
        
        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged)

        # This dictionary contains {id(image) -> display panel}
        # mappings for all display panels that that currently exist.
        # It is maintained by the _imageListChanged method.
        self._displayPanels = {}

        self._imageListChanged()
        self._selectedImageChanged()

        self.Layout()

        
    def _imageListChanged(self, *a):
        """Called when the image list changes. Destroys and/or creates
        display panels as necessary, for images which have been
        added/removed to/from the list.
        """

        imgIds = map(id, self._imageList)

        # First check to see if there are any display panels
        # for which the corresponding image is no longer
        # present in the list.
        for imgId, displayPanel in self._displayPanels.items():

            if imgId not in imgIds:
                self._sizer.Detach(displayPanel)
                displayPanel.Destroy()
                self._displayPanels.pop(imgId)
        
        # Now check to see if any images have been added,
        # and we need to create a display panel for them
        for i, image in enumerate(self._imageList):

            # check to see if a display
            # panel exists for this image
            try: self._displayPanels[id(image)]

            # if one doesn't, make one and 
            # add the image to the list box
            except KeyError:
                self._makeDisplayPanel(image)
                self._listBox.Append(image.name,
                                     image,
                                     op.abspath(image.imageFile))

        
    def _selectedImageChanged(self, *a):
        """Called when the :attr:`~fsl.data.fslimage.ImageList.selectedImage`
        property changes. Shows the display panel for the newly selected
        image.
        """
        self._showDisplayPanel(self._imageList.selectedImage)

        
    def _makeDisplayPanel(self, image):
        """Creates a panel containing widgets allowing the user to
        edit the display properties of the given image. A reference
        to the panel is stored in the :attr:`_displayPanels` dict.
        """

        parentPanel = wx.Panel(self)
            
        displayPanel = props.buildGUI(parentPanel, image.display)
        imagePanel   = props.buildGUI(parentPanel, image)

        parentSizer = wx.BoxSizer(wx.HORIZONTAL)
        parentPanel.SetSizer(parentSizer)
        parentSizer.Add(displayPanel, flag=wx.EXPAND, proportion=1)
        parentSizer.Add(imagePanel,   flag=wx.EXPAND)

        parentSizer.Layout()
        
        self._sizer.Add(parentPanel, flag=wx.EXPAND, proportion=2)

        self._displayPanels[id(image)] = parentPanel
        return parentPanel


    def _showDisplayPanel(self, idx):
        """Shows the display panel for the image at the specified index."""
        
        for i, image in enumerate(self._imageList):

            displayPanel = self._displayPanels[id(image)]
            
            if i == idx:
                log.debug('Showing display panel for '
                          'image {}'.format(image.name))
            
            displayPanel.Show(i == idx)

        self._listBox.SetSelection(idx)
        self.GetParent().Layout()
        self.GetParent().Refresh()

        
    def _imageMoved(self, ev):
        """Called when an image name is moved in the
        :class:`~pwidgets.elistbox.EditableListBox`. Reorders the
        :class:`~fsl.data.fslimage.ImageList` to reflect the change.
        """
        self._imageList.move(ev.oldIdx, ev.newIdx)

        
    def _imageSelected(self, ev):
        """Called when an image is selected in the
        :class:`~pwidgets.elistbox.EditableListBox`. Displays the
        corresponding image display panel.
        """
        self._imageList.selectedImage = ev.idx

        
    def _addImage(self, ev):
        """Called when the 'add' button on the list box is pressed.

        Pops up an open file dialog prompting the user to choose one or more
        image files, then opens those files, adds them to the image list, and
        creates display panels for each of them.  See the
        :meth:`~fsl.data.fslimage.ImageList.addImages` method.
        """
        self._imageList.addImages()

        # Tell the parent window to lay itself out in
        # case the image list was 0, and is now non-0,
        # in which case  this ImageListPanel will have
        # changed size.
        if len(self._imageList) > 0:
            self.GetParent().Layout()
            self.GetParent().Refresh()


    def _imageRemoved(self, ev):
        """
        Called when an item is removed from the image listbox. Removes the
        corresponding image from the image list. The corresponding display
        panel will removed via the :meth:`~_imageListChanged` method, which
        is registered as a listener on the
        :attr:`~fsl.data.fslimage.ImageList.images` list.
        """
        self._imageList.pop(ev.idx)

        # if the image list is now empty, there are no more
        # display panels, and hence the size of this
        # ImageListPanel will have changed. So tell the parent
        # to lay itself out again
        if len(self._imageList) == 0:
            self.GetParent().Layout()
            self.GetParent().Refresh()

        # Even though the image list has changed, the selected
        # image index may not have changed. So we make doubly
        # sure that the correct display panel is visible
        else:
            self._selectedImageChanged()
