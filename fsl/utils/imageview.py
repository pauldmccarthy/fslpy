#!/usr/bin/env python
#
# imgshow.py - A wx/OpenGL widget for displaying and interacting with a
# collection of 3D images. Displays three canvases, each of which shows

#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys

if False:
    import logging
    logging.basicConfig(
        format='%(levelname)8s '\
               '%(filename)20s '\
               '%(lineno)4d: '\
               '%(funcName)s - '\
               '%(message)s',
        level=logging.DEBUG)

import wx
import wx.lib.newevent as wxevent

import fsl.props             as props
import fsl.data.fslimage     as fslimage
import fsl.utils.slicecanvas as slicecanvas

LocationEvent, EVT_LOCATION_EVENT = wxevent.NewEvent()

class EditableListBox(wx.Panel):
    """
    wx.gizmos.EditableListBox is rubbish.
    """

    ListSelectEvent, EVT_ELB_SELECT_EVENT = wxevent.NewEvent()
    ListAddEvent,    EVT_ELB_ADD_EVENT    = wxevent.NewEvent()
    ListRemoveEvent, EVT_ELB_REMOVE_EVENT = wxevent.NewEvent()
    ListMoveEvent,   EVT_ELB_MOVE_EVENT   = wxevent.NewEvent()

    def __init__(
            self,
            parent,
            choices,
            clientData):

        wx.Panel.__init__(self, parent)

        self.listBox = wx.ListBox(
            self, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)

        for choice,data in zip(choices, clientData):
            self.listBox.Append(choice, data)

        self.listBox.Bind(wx.EVT_LISTBOX, self.itemSelected)

        self.buttonPanel = wx.Panel(self)

        self.upButton     = wx.Button(self.buttonPanel, label=u'\u25B2')
        self.downButton   = wx.Button(self.buttonPanel, label=u'\u25BC')
        self.addButton    = wx.Button(self.buttonPanel, label='+')
        self.removeButton = wx.Button(self.buttonPanel, label='-')

        self.upButton    .Bind(wx.EVT_BUTTON, self.moveItemUp)
        self.downButton  .Bind(wx.EVT_BUTTON, self.moveItemDown)
        self.addButton   .Bind(wx.EVT_BUTTON, self.addItem)
        self.removeButton.Bind(wx.EVT_BUTTON, self.removeItem)

        self.buttonPanelSizer = wx.BoxSizer(wx.VERTICAL)
        self.buttonPanel.SetSizer(self.buttonPanelSizer)
        self.buttonPanelSizer.Add(self.upButton)
        self.buttonPanelSizer.Add(self.downButton)
        self.buttonPanelSizer.Add(self.addButton)
        self.buttonPanelSizer.Add(self.removeButton)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        
        self.sizer.Add(self.buttonPanel, flag=wx.EXPAND)
        self.sizer.Add(self.listBox,     flag=wx.EXPAND, proportion=1)

        self.Layout()

        
    def itemSelected(self, ev):
        idx    = ev.GetSelection()
        choice = self.listBox.GetString(idx)
        data   = self.listBox.GetClientData(idx)

        print 'selected {}'.format(idx)
        
        ev = EditableListBox.ListSelectEvent(
            idx=idx, choice=choice, data=data)
        wx.PostEvent(self, ev)

        
    def moveItem(self, oldIdx, newIdx):

        # nothing is selected
        if oldIdx  == wx.NOT_FOUND: return
        
        choice  = self.listBox.GetString(oldIdx)
        data    = self.listBox.GetClientData(oldIdx)
        choices = self.listBox.GetItems()

        if oldIdx < 0 or oldIdx >= len(choices): return
        if newIdx < 0 or newIdx >= len(choices): return
        
        self.listBox.Delete(oldIdx)
        self.listBox.Insert(choice, newIdx, data)
        self.listBox.SetSelection(newIdx)

        ev = EditableListBox.ListMoveEvent(
            oldIdx=oldIdx,
            newIdx=newIdx,
            choice=choice,
            data=data)
        wx.PostEvent(self, ev)

        
    def moveItemDown(self, ev):
        oldIdx = self.listBox.GetSelection()
        newIdx = oldIdx+1
        self.moveItem(oldIdx, newIdx)

        
    def moveItemUp(self, ev):
        oldIdx = self.listBox.GetSelection()
        newIdx = oldIdx-1
        self.moveItem(oldIdx, newIdx) 

        
    def addItem(self, ev):
        pass

        
    def removeItem(self, ev):
        pass

        
class DisplayControl(wx.Panel):
    
    def __init__(self, parent, imageList):
        
        wx.Panel.__init__(self, parent)
        self.imageList = imageList

        imageNames = [img.name for img in imageList]
        self.listBox = EditableListBox(
            self, imageNames, imageList)

        self.listBox.Bind(
            EditableListBox.EVT_ELB_SELECT_EVENT, self.imageSelected)
        self.listBox.Bind(
            EditableListBox.EVT_ELB_MOVE_EVENT, self.imageMoved) 

        self.editPanels = []
        for image in imageList:
            displayProps = props.buildGUI(self, image.display)
            self.editPanels.append(displayProps)


        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.listBox, flag=wx.EXPAND, proportion=1)
        
        for i,editPanel in enumerate(self.editPanels):
            
            self.sizer.Add(editPanel, flag=wx.EXPAND, proportion=2)
            editPanel.Show(i == 0)
            
        self.Layout()

    def imageMoved(self, ev):

        oldIdx = ev.oldIdx
        newIdx = ev.newIdx

        image = self.imageList.pop(oldIdx)
        self.imageList.insert(newIdx, image)
        self.Refresh()

        
    def imageSelected(self, ev):
        """
        """
        print 'imageSelected'
        
        for i,editPanel in enumerate(self.editPanels):
            editPanel.Show(i == ev.idx)
        self.Layout()


class ImageView(wx.Panel):

    def __init__(self, parent, imageList, *args, **kwargs):
        """
        Creates three SliceCanvas objects, each displaying a
        different axis of the given image list.
        """
        
        if isinstance(imageList, fslimage.Image):
            imageList = fslimage.ImageList(imageList)

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance')

        self.imageList = imageList

        wx.Panel.__init__(self, parent, *args, **kwargs)
        self.SetMinSize((300,100))

        self.shape = imageList[0].data.shape

        self.canvasPanel = wx.Panel(self)

        self.xcanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=0)
        self.ycanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=1, context=self.xcanvas.context)
        self.zcanvas = slicecanvas.SliceCanvas(
            self.canvasPanel, imageList, zax=2, context=self.xcanvas.context)

        self.controlPanel = DisplayControl(self, imageList)

        self.mainSizer   = wx.BoxSizer(wx.VERTICAL)
        self.canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self.mainSizer)

        self.mainSizer.Add(self.canvasPanel,  flag=wx.EXPAND, proportion=1)
        self.mainSizer.Add(self.controlPanel, flag=wx.EXPAND)
        
        self.canvasPanel.SetSizer(self.canvasSizer)

        self.canvasSizer.Add(self.xcanvas, flag=wx.EXPAND, proportion=1)
        self.canvasSizer.Add(self.ycanvas, flag=wx.EXPAND, proportion=1)
        self.canvasSizer.Add(self.zcanvas, flag=wx.EXPAND, proportion=1)

        self.canvasPanel.Layout()
        self.Layout()

        self.xcanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_LEFT_DOWN, self._setCanvasPosition)
        self.xcanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)
        self.ycanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)
        self.zcanvas.Bind(wx.EVT_MOTION,    self._setCanvasPosition)

        
    def setLocation(self, x, y, z):
        """
        Programmatically set the currently displayed location
        on each of the canvases. This does not trigger an
        EVT_LOCATION_EVENT.
        """

        self.xcanvas.xpos = y
        self.xcanvas.ypos = z
        self.xcanvas.zpos = x

        self.ycanvas.xpos = x
        self.ycanvas.ypos = z
        self.ycanvas.zpos = y
        
        self.zcanvas.xpos = x
        self.zcanvas.ypos = y
        self.zcanvas.zpos = z

        self.xcanvas.Refresh()
        self.ycanvas.Refresh()
        self.zcanvas.Refresh()

    def setXLocation(self, x):
        self.setLocation(x, self.ycanvas.zpos, self.zcanvas.zpos)

    def setYLocation(self, y):
        self.setLocation(self.xcanvas.zpos, y, self.zcanvas.zpos)

    def setZLocation(self, z):
        self.setLocation(self.xcanvas.zpos, self.ycanvas.zpos, z)


    def _setCanvasPosition(self, ev):
        """
        Called on mouse movement and left clicks. The currently
        displayed slices and cursor positions on each of the
        canvases follow mouse clicks and drags.
        """

        if not ev.LeftIsDown(): return

        mx,my  = ev.GetPositionTuple()
        source = ev.GetEventObject()
        w,h = source.GetClientSize()

        my = h - my

        x = self.xcanvas.zpos
        y = self.ycanvas.zpos
        z = self.zcanvas.zpos

        if source == self.xcanvas:

            mx = mx * self.shape[1] / float(w)
            my = my * self.shape[2] / float(h)
            y,z = mx,my

        elif source == self.ycanvas:
            mx = mx * self.shape[0] / float(w)
            my = my * self.shape[2] / float(h)
            x,z = mx,my

        elif source == self.zcanvas:
            mx = mx * self.shape[0] / float(w)
            my = my * self.shape[1] / float(h)
            x,y = mx,my

        x = int(x)
        y = int(y)
        z = int(z)

        if x < 0: x = 0
        if y < 0: y = 0
        if z < 0: z = 0

        if x >= self.shape[0]: x = self.shape[0]-1
        if y >= self.shape[1]: y = self.shape[1]-1
        if z >= self.shape[2]: z = self.shape[2]-1 

        self.setLocation(x,y,z)

        evt = LocationEvent(x=x,y=y,z=z)
        wx.PostEvent(self, evt)


class ImageFrame(wx.Frame):
    """
    Convenience class for displaying a collection of images in a standalone
    window.
    """

    def __init__(self, parent, imageList, title=None):
        wx.Frame.__init__(self, parent, title=title)

        self.panel = ImageView(self, imageList)
        self.Layout()


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print 'usage: imageview.py filename [filename]'
        sys.exit(1)

    app       = wx.App()
    images    = map(fslimage.Image, sys.argv[1:])
    imageList = fslimage.ImageList(images)
    
    frame  = ImageFrame(
        None,
        imageList,
        title=sys.argv[1])
    frame.Show()

    app.MainLoop()
