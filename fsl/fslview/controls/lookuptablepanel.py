#!/usr/bin/env python
#
# lookuptablepanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import numpy as np

import props

import pwidgets.elistbox          as elistbox

import fsl.fslview.panel          as fslpanel
import fsl.fslview.displaycontext as fsldisplay
import fsl.data.strings           as strings


log = logging.getLogger(__name__)



class LabelWidget(wx.Panel):
    
    def __init__(self, lutPanel, overlayOpts, lut, value):
        wx.Panel.__init__(self, lutPanel)

        self.lutPanel = lutPanel
        self.opts     = overlayOpts
        self.lut      = lut
        self.value    = value

        # TODO Change the enable box to a toggle
        #      button with an eye icon
        
        self.valueLabel   = wx.StaticText(self,
                                          style=wx.ALIGN_CENTRE_VERTICAL |
                                                wx.ALIGN_RIGHT)
        self.enableBox    = wx.CheckBox(self)
        self.colourButton = wx.ColourPickerCtrl(self)

        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.sizer.Add(self.valueLabel,   flag=wx.ALIGN_CENTRE, proportion=1)
        self.sizer.Add(self.enableBox,    flag=wx.ALIGN_CENTRE, proportion=1)
        self.sizer.Add(self.colourButton, flag=wx.ALIGN_CENTRE, proportion=1)

        label  = lut.get(value)
        colour = [np.floor(c * 255.0) for c in label.colour()]

        self.valueLabel  .SetLabel(str(value))
        self.colourButton.SetColour(colour)
        self.enableBox   .SetValue(label.enabled())

        self.enableBox   .Bind(wx.EVT_CHECKBOX,             self.__onEnable)
        self.colourButton.Bind(wx.EVT_COLOURPICKER_CHANGED, self.__onColour)


    def __onEnable(self, ev):

        self.lut.set(self.value, enabled=self.enableBox.GetValue())
        self.__notifyLut()


    def __notifyLut(self):

        # Disable the LookupTablePanel listener
        # on the lut property, otherwise it will
        # re-create the label list
        self.opts.disableListener('lut', self.lutPanel._name)
        self.opts.notify('lut')
        self.opts.enableListener('lut', self.lutPanel._name)        


    def __onColour(self, ev):

        newColour = self.colourButton.GetColour()
        newColour = [c / 255.0 for c in newColour]

        self.lut.set(self.value, colour=newColour)
        self.__notifyLut()



class LookupTablePanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        # If non-lut image is shown, just show a message

        # Overlay name
        # Change lookup table
        # Add label
        # Save lut
        # Load lut

        self.__controlRow = wx.Panel(self)

        self.__disabledLabel = wx.StaticText(self,
                                             style=wx.ALIGN_CENTER_VERTICAL |
                                                   wx.ALIGN_CENTER_HORIZONTAL)
        self.__labelList     = elistbox.EditableListBox(
            self,
            style=elistbox.ELB_NO_MOVE | elistbox.ELB_EDITABLE)

        self.__overlayNameLabel = wx.StaticText(self,
                                                style=wx.ST_ELLIPSIZE_MIDDLE)

        self.__lutWidget        = None
        self.__newLutButton     = wx.Button(self.__controlRow)
        self.__saveLutButton    = wx.Button(self.__controlRow)
        self.__loadLutButton    = wx.Button(self.__controlRow)

        self.__controlRowSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer           = wx.BoxSizer(wx.VERTICAL)

        self.__controlRow.SetSizer(self.__controlRowSizer)
        self             .SetSizer(self.__sizer)

        self.__controlRowSizer.Add(self.__newLutButton,
                                   flag=wx.EXPAND, proportion=1) 
        self.__controlRowSizer.Add(self.__loadLutButton,
                                   flag=wx.EXPAND, proportion=1)
        self.__controlRowSizer.Add(self.__saveLutButton,
                                   flag=wx.EXPAND, proportion=1)

        self.__sizer.Add(self.__overlayNameLabel, flag=wx.EXPAND)
        self.__sizer.Add(self.__controlRow,       flag=wx.EXPAND)
        self.__sizer.Add(self.__disabledLabel,    flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__labelList,        flag=wx.EXPAND, proportion=1)

        # Label the labels and buttons
        self.__disabledLabel.SetLabel(strings.messages[self, 'notLutOverlay'])
        self.__newLutButton .SetLabel(strings.labels[  self, 'newLut'])
        self.__loadLutButton.SetLabel(strings.labels[  self, 'loadLut'])
        self.__saveLutButton.SetLabel(strings.labels[  self, 'saveLut'])

        # Make the label name a bit smaller
        font = self.__overlayNameLabel.GetFont()
        font.SetPointSize(font.GetPointSize() - 2)
        font.SetWeight(wx.FONTWEIGHT_LIGHT)
        self.__overlayNameLabel.SetFont(font)

        # Listen for listbox events
        self.__labelList.Bind(elistbox.EVT_ELB_ADD_EVENT,
                              self.__onLabelAdd)
        self.__labelList.Bind(elistbox.EVT_ELB_REMOVE_EVENT,
                              self.__onLabelRemove)
        self.__labelList.Bind(elistbox.EVT_ELB_EDIT_EVENT,
                              self.__onLabelEdit) 

        self.__selectedOpts    = None
        self.__selectedOverlay = None

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()
    

    def __selectedOverlayChanged(self, *a):

        newOverlay = self._displayCtx.getSelectedOverlay()

        if self.__selectedOverlay == newOverlay:
            return

        if self.__selectedOverlay is not None:
            
            display = self._displayCtx.getDisplay(self.__selectedOverlay)
            
            display.removeListener('name',        self._name)
            display.removeListener('overlayType', self._name)

        self.__selectedOverlay = newOverlay

        if newOverlay is not None:
            display = self._displayCtx.getDisplay(newOverlay)
            display.addListener('name',
                                self._name,
                                self.__overlayNameChanged)
            display.addListener('overlayType',
                                self._name,
                                self.__overlayTypeChanged)

        self.__overlayNameChanged()
        self.__overlayTypeChanged()


    def __overlayNameChanged(self, *a):

        overlay = self.__selectedOverlay

        if overlay is None:
            self.__overlayNameLabel.SetLabel('')
            return

        display = self._displayCtx.getDisplay(overlay)

        self.__overlayNameLabel.SetLabel(display.name)
        

    def __overlayTypeChanged(self, *a):

        if self.__lutWidget is not None:
            self.__controlRowSizer.Detach(self.__lutWidget)
            self.__lutWidget.Destroy()
            self.__lutWidget = None

        if self.__selectedOpts is not None:
            self.__selectedOpts.removeListener('lut', self._name)
            self.__selectedOpts = None

        overlay = self.__selectedOverlay
        enabled = False

        if overlay is not None:
            opts = self._displayCtx.getOpts(overlay)

            if isinstance(opts, fsldisplay.LabelOpts):
                enabled = True

        self.__overlayNameLabel.Show(    enabled)
        self.__controlRow      .Show(    enabled)
        self.__labelList       .Show(    enabled)
        self.__disabledLabel   .Show(not enabled)

        if not enabled:
            self.Layout()
            return

        opts = self._displayCtx.getOpts(overlay)

        opts.addListener('lut', self._name, self.__initLabelList)
        
        self.__selectedOpts = opts
        self.__lutWidget    = props.makeWidget(
            self.__controlRow, opts, 'lut')

        self.__controlRowSizer.Insert(
            0, self.__lutWidget, flag=wx.EXPAND, proportion=1)

        self.__initLabelList()

        self.Layout()


    def __initLabelList(self, *a):

        self.__labelList.Clear()

        if self.__selectedOpts is None:
            return

        opts = self.__selectedOpts
        lut  = opts.lut
        

        for i, label in enumerate(lut.labels):

            self.__labelList.Append(label.name())

            widget = LabelWidget(self, opts, lut, label.value())
            self.__labelList.SetItemWidget(i, widget)


    def __onNewLut(self, ev):
        pass

    
    def __onLoadLut(self, ev):
        pass

    
    def __onSaveLut(self, ev):
        pass 

    
    def __onLabelAdd(self, ev):
        pass

    
    def __onLabelRemove(self, ev):
        pass


    def __onLabelEdit(self, ev):
        pass
