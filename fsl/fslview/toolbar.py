#!/usr/bin/env python
#
# toolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import numpy as np

import props

import fsl.fslview.panel   as fslpanel
import fsl.fslview.actions as actions
import fsl.data.strings    as strings

log = logging.getLogger(__name__)

        
class FSLViewToolBar(fslpanel._FSLViewPanel, wx.Panel):
    """
    """


    class Tool(wx.Panel):

        
        def __init__(self, parent, tool, label, labelText):
            wx.Panel.__init__(self, parent)
            
            self.tool      = tool
            self.label     = label
            self.labelText = labelText

            tool.Reparent(self)

            self.sizer = wx.BoxSizer(wx.VERTICAL)
            self.SetSizer(self.sizer)
            
            if label is not None:
                label.Reparent(self)
                self.sizer.Add(label, flag=wx.ALIGN_CENTRE)
                
            self.sizer.Add(self.tool, flag=wx.EXPAND)
            self.Layout()
            

        def __str__(self):
            return '{}: {} ({}, {})'.format(
                type(self)      .__name__,
                type(self.tool) .__name__,
                type(self.label).__name__,
                self.labelText)

            
    def __init__(self, parent, imageList, displayCtx, actionz=None):
        wx.Panel.__init__(self, parent)
        fslpanel._FSLViewPanel.__init__(self, imageList, displayCtx, actionz)

        self.__tools      = []
        self.__index      = 0
        self.__numVisible = None

        import fsl.fslview.layouts as layouts
        self.SetMinSize(layouts.minSizes.get(self, (-1, -1)))

        self.__leftButton  = wx.Button(self, label='<', style=wx.BU_EXACTFIT)
        self.__rightButton = wx.Button(self, label='>', style=wx.BU_EXACTFIT) 

        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.__sizer) 

        self.__leftButton .Bind(wx.EVT_BUTTON,     self.__onLeftButton)
        self.__rightButton.Bind(wx.EVT_BUTTON,     self.__onRightButton)
        self              .Bind(wx.EVT_MOUSEWHEEL, self.__onMouseWheel)
        self              .Bind(wx.EVT_SIZE,       self.__drawToolBar)
        

    def __onMouseWheel(self, ev):

        wheelDir = ev.GetWheelRotation()
        if   wheelDir < 0: self.__onRightButton()
        elif wheelDir > 0: self.__onLeftButton()


    def __onLeftButton(self, ev=None):

        self.__index -= 1

        if self.__index <= 0:
            self.__index = 0

        log.debug('Left button pushed - setting start '
                  'tool index to {}'.format(self.__index)) 

        self.__drawToolBar()

        
    def __onRightButton(self, ev=None):
        
        self.__index += 1

        if self.__index + self.__numVisible >= len(self.__tools):
            self.__index = len(self.__tools) - self.__numVisible

        log.debug('Right button pushed - setting start '
                  'tool index to {}'.format(self.__index))

        self.__drawToolBar()


    def __drawToolBar(self, *a):

        sizer = self.__sizer
        tools = self.__tools

        sizer.Clear()
        
        availWidth = self.GetSize().GetWidth()
        reqdWidths = [tool.GetBestSize().GetWidth() for tool in tools]
        leftWidth  = self.__leftButton .GetBestSize().GetWidth()
        rightWidth = self.__rightButton.GetBestSize().GetWidth()

        if availWidth >= sum(reqdWidths):

            log.debug('{}: All tools fit ({} >= {})'.format(
                type(self).__name__, availWidth, sum(reqdWidths)))
            
            self.__index      = 0
            self.__numVisible = len(tools)
            
            self.__leftButton .Enable(False)
            self.__rightButton.Enable(False)
            self.__leftButton .Show(  False)
            self.__rightButton.Show(  False) 

            for tool in tools:
                tool.Show(True)
                sizer.Add(tool)

        else:
            reqdWidths = reqdWidths[self.__index:]
            cumWidths  = np.cumsum(reqdWidths) + leftWidth + rightWidth
            biggerIdxs = np.where(cumWidths > availWidth)[0]

            if len(biggerIdxs) == 0:
                lastIdx = len(tools)
            else:
                lastIdx = biggerIdxs[0] + self.__index
            
            self.__numVisible = lastIdx - self.__index

            log.debug('{}: {} tools fit ({} - {})'.format(
                type(self).__name__, self.__numVisible, self.__index, lastIdx))

            self.__leftButton .Show(True)
            self.__rightButton.Show(True)
            self.__leftButton .Enable(self.__index > 0)
            self.__rightButton.Enable(lastIdx < len(tools))

            for i in range(len(tools)):
                if i >= self.__index and i < lastIdx:
                    tools[i].Show(True)
                    sizer.Add(tools[i])
                else:
                    tools[i].Show(False)

        sizer.Insert(self.__numVisible, (0, 0), flag=wx.EXPAND, proportion=1)
        sizer.Insert(self.__numVisible + 1, self.__rightButton)
        sizer.Insert(0,                 self.__leftButton)

        widgets = [self.__leftButton, self.__rightButton] + tools
        bestHeight = max([w.GetBestSize().GetHeight() for w in widgets])

        self.SetMinSize((availWidth, bestHeight))
        self.Layout()


    def GenerateTools(self, toolSpecs, targets, add=True):
        """
        Targets may be a single object, or a dict of [toolSpec : target]
        mappings.
        """
        
        tools  = []
        labels = []

        if not isinstance(targets, dict):
            targets = {s : targets for s in toolSpecs}

        for toolSpec in toolSpecs:
            tool = props.buildGUI(
                self, targets[toolSpec], toolSpec, showUnlink=False)

            if isinstance(toolSpec, actions.ActionButton):
                label = None
            else:
                label = strings.properties[targets[toolSpec], toolSpec.key]

            tools .append(tool)
            labels.append(label)

            if add:
                self.AddTool(tool, label)

        return zip(tools, labels)

            
    def GetTools(self):
        """
        """
        return [t.tool for t in self.__tools]


    def AddTool(self, tool, labelText=None):
        self.InsertTool(tool, labelText)

        
    def InsertTools(self, tools, labels=None, index=None):

        if labels is None:
            labels = [None] * len(tools)

        for i, (tool, label) in enumerate(zip(tools, labels), index):
            self.InsertTool(tool, label, i)


    def SetTools(self, tools, labels=None, destroy=False):

        if labels is None:
            labels = [None] * len(tools)

        self.ClearTools(destroy)

        for tool, label in zip(tools, labels):
            self.InsertTool(tool, label)
        

    def InsertTool(self, tool, labelText=None, index=None):

        if index is None:
            index = len(self.__tools)

        if labelText is None:
            label = None
            
        else:
            label = wx.StaticText(self,
                                  label=labelText,
                                  style=wx.ALIGN_CENTRE)
            label.SetFont(label.GetFont().Smaller().Smaller())

        log.debug('{}: adding tool at index {}: {}'.format(
            type(self).__name__, index, labelText))

        self.__tools.insert(
            index, FSLViewToolBar.Tool(self, tool, label, labelText))
        self.__drawToolBar()

    
    def ClearTools(self, destroy=False, startIdx=None, endIdx=None):

        if startIdx is None: startIdx = 0
        if endIdx   is None: endIdx   = len(self.__tools)

        for i in range(startIdx, endIdx):
            tool = self.__tools[i]

            self.__sizer.Detach(tool.tool)
            
            if destroy:
                tool.tool.Destroy()

            if tool.label is not None:
                self.__sizer.Detach(tool.label)
                tool.label.Destroy()

        self.__tools[startIdx:endIdx] = []
        self.Layout()

        
    def __del__(self):
        wx.Panel              .__del__(self)
        fslpanel._FSLViewPanel.__del__(self)        
