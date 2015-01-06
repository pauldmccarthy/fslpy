#!/usr/bin/env python
#
# imagelistpanel.py - A panel which displays a list of images in the image
# list.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A panel which displays a list of image list in the image list (see
:class:`~fsl.data.image.ImageList`), and allows the user to add/remove
images, and to change their order.
"""

import logging
log = logging.getLogger(__name__)


import wx

import props

import pwidgets.elistbox as elistbox

import fsl.fslview.panel as fslpanel

class ListItemWidget(wx.Panel):

    _enabledFG  = '#000000'
    _disabledFG = '#CCCCCC'

    def __init__(self, parent, image, display, listBox):
        wx.Panel.__init__(self, parent)

        self.image   = image
        self.display = display
        self.listBox = listBox
        self.name    = '{}_{}'.format(self.__class__.__name__, id(self))

        self.visibility = props.makeWidget(self, display, 'enabled')

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.sizer)

        self.sizer.Add(self.visibility, flag=wx.EXPAND, proportion=1)

        self.display.addListener('enabled', self.name, self._vizChanged)
        self.image  .addListener('saved',   self.name, self._saveStateChanged)

        self.Bind(wx.EVT_WINDOW_DESTROY, self._onDestroy)

        self._vizChanged()
        self._saveStateChanged()

        
    def _onDestroy(self, ev):
        ev.Skip()
        self.display.removeListener('enabled', self.name)
        self.image  .removeListener('saved',   self.name)

        
    def _saveStateChanged(self, *a):
        idx = self.listBox.IndexOf(self.image)

        if self.image.saved:
            self.listBox.SetItemBackgroundColour(idx)
        else:
            self.listBox.SetItemBackgroundColour(idx, '#ffaaaa', '#993333') 

            
    def _vizChanged(self, *a):

        idx = self.listBox.IndexOf(self.image)

        if self.display.enabled: fgColour = ListItemWidget._enabledFG
        else:                    fgColour = ListItemWidget._disabledFG

        self.listBox.SetItemForegroundColour(idx, fgColour)


class ImageListPanel(fslpanel.FSLViewPanel):
    """A :class:`~fsl.fslview.panel.ControlPanel` which contains an
    :class:`~pwidgets.EditableListBox` displaying the list of loaded images.
    
    The list box allows the image order to be changed, and allows images to be
    added and removed from the list.
    """
    
    def __init__(self, parent, imageList, displayCtx):
        """Create and lay out an :class:`ImageListPanel`.

        :param parent:     The :mod:`wx` parent object.
        :param imageList:  A :class:`~fsl.data.image.ImageList` instance.
        :param displayCtx: A
                           :class:`~fsl.fslview.displaycontext.DisplayContext`
                           instance.
        """
        
        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        # list box containing the list of images - it 
        # is populated in the _imageListChanged method
        self._listBox = elistbox.EditableListBox(
            self,
            style=(elistbox.ELB_REVERSE    | 
                   elistbox.ELB_TOOLTIP    | 
                   elistbox.ELB_EDITABLE))

        # listeners for when the user does
        # something with the list box
        self._listBox.Bind(elistbox.EVT_ELB_SELECT_EVENT, self._lbSelect)
        self._listBox.Bind(elistbox.EVT_ELB_MOVE_EVENT,   self._lbMove)
        self._listBox.Bind(elistbox.EVT_ELB_REMOVE_EVENT, self._lbRemove)
        self._listBox.Bind(elistbox.EVT_ELB_ADD_EVENT,    self._lbAdd)
        self._listBox.Bind(elistbox.EVT_ELB_EDIT_EVENT,   self._lbEdit)

        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._listBox, flag=wx.EXPAND, proportion=1)

        self._imageList.addListener(
            'images',
            self._name,
            self._imageListChanged)
        
        self._displayCtx.addListener(
            'imageOrder',
            self._name,
            self._imageListChanged) 

        self._displayCtx.addListener(
            'selectedImage',
            self._name,
            self._selectedImageChanged)

        def onDestroy(ev):
            ev.Skip()

            # This handler gets called when child windows
            # are destroyed (e.g. items in the embedded
            # elistbox), so this check is necessary.
            if ev.GetEventObject() != self: return
            
            self._imageList .removeListener('images',        self._name)
            self._displayCtx.removeListener('selectedImage', self._name)
            self._displayCtx.removeListener('imageOrder',    self._name)

            # these listeners are added in the
            # _imageListChanged method, below
            for image in self._imageList:
                display = self._displayCtx.getDisplayProperties(image)
                image  .removeListener('name',    self._name)
                display.removeListener('enabled', self._name)

        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self._imageListChanged()
        self._selectedImageChanged()

        self.Layout()


    def _selectedImageChanged(self, *a):
        """Called when the
        :attr:`~fsl.fslview.displaycontext.DisplayContext.selectedImage`
        property changes. Updates the selected item in the list box.
        """

        if len(self._imageList) > 0:
            self._listBox.SetSelection(
                self._displayCtx.getImageOrder(
                    self._displayCtx.selectedImage))

        
    def _imageListChanged(self, *a):
        """Called when the :class:`~fsl.data.image.ImageList.images`
        list changes.

        If the change was due to user action on the
        :class:`~pwidgets.EditableListBox`, this method does nothing.
        Otherwise, this method updates the :class:`~pwidgets.EditableListBox`
        """
        
        self._listBox.Clear()

        for i, image in enumerate(self._displayCtx.getOrderedImages()):

            display  = self._displayCtx.getDisplayProperties(image)
            name     = image.name
            if name is None: name = ''

            self._listBox.Append(name, image, image.imageFile)

            widget = ListItemWidget(self, image, display, self._listBox)

            self._listBox.SetItemWidget(i, widget)

            def nameChanged(img):
                idx  = self._displayCtx.getImageOrder(img)
                name = img.name 
                if name is None: name = ''
                self._listBox.SetString(idx, name)

            image.addListener(
                'name',
                self._name,
                lambda c, va, vi, img=image: nameChanged(img),
                overwrite=True)

        if len(self._imageList) > 0:
            self._listBox.SetSelection(
                self._displayCtx.getImageOrder(
                    self._displayCtx.selectedImage))
        
        
    def _lbMove(self, ev):
        """Called when an image name is moved in the
        :class:`~pwidgets.elistbox.EditableListBox`. Reorders the
        :class:`~fsl.data.image.ImageList` to reflect the change.
        """
        self._displayCtx.disableListener('imageOrder', self._name)
        self._displayCtx.imageOrder.move(ev.oldIdx, ev.newIdx)
        self._displayCtx.enableListener('imageOrder', self._name)

        
    def _lbSelect(self, ev):
        """Called when an image is selected in the
        :class:`~pwidgets.elistbox.EditableListBox`. Sets the
        :attr:`fsl.data.image.ImageList.selectedImage property.
        """
        self._displayCtx.disableListener('selectedImage', self._name)
        self._displayCtx.selectedImage = self._displayCtx.imageOrder[ev.idx]
        self._displayCtx.enableListener('selectedImage', self._name)

        
    def _lbAdd(self, ev):
        """Called when the 'add' button on the list box is pressed.
        Calls the :meth:`~fsl.data.image.ImageList.addImages` method.
        """
        if self._imageList.addImages():
            self._displayCtx.selectedImage = len(self._imageList) - 1


    def _lbRemove(self, ev):
        """Called when an item is removed from the image listbox.

        Removes the corresponding image from the
        :class:`~fsl.data.image.ImageList`. 
        """
        self._imageList.pop(self._displayCtx.imageOrder[ev.idx])


    def _lbEdit(self, ev):
        """Called when an item label is edited on the image list box.
        Sets the corresponding image name to the new label.
        """
        idx      = self._displayCtx.imageOrder[ev.idx]
        img      = self._imageList[idx]
        img.name = ev.label
