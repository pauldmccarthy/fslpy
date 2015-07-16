#!/usr/bin/env python
#
# toolbar.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx
import wx.lib.newevent as wxevent

import numpy as np

import props

import fsl.fslview.panel   as fslpanel
import fsl.fslview.actions as actions
import fsl.data.strings    as strings

log = logging.getLogger(__name__)


_ToolBarEvent, _EVT_TOOLBAR_EVENT = wxevent.NewEvent()


EVT_TOOLBAR_EVENT = _EVT_TOOLBAR_EVENT
"""Identifier for the :data:`ToolBarEvent` event. """


ToolBarEvent = _ToolBarEvent
"""Event emitted when one or more tools is/are added/removed to/from the
toolbar.
"""


class FSLViewToolBar(fslpanel._FSLViewPanel, wx.PyPanel):
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
                
            self.sizer.Add(self.tool, flag=wx.EXPAND | wx.ALIGN_CENTRE)
            self.Layout()
            self.SetMinSize(self.sizer.GetMinSize())
            

        def __str__(self):
            return '{}: {} ({}, {})'.format(
                type(self)      .__name__,
                type(self.tool) .__name__,
                type(self.label).__name__,
                self.labelText)

            
    def __init__(self, parent, overlayList, displayCtx, actionz=None):
        wx.PyPanel.__init__(self, parent)
        fslpanel._FSLViewPanel.__init__(self, overlayList, displayCtx, actionz)

        self.__tools      = []
        self.__index      = 0
        self.__numVisible = None

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
                sizer.Add(tool, flag=wx.EXPAND | wx.ALIGN_CENTRE)

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
                    sizer.Add(tools[i], flag=wx.EXPAND | wx.ALIGN_CENTRE)
                else:
                    tools[i].Show(False)

        sizer.Insert(self.__numVisible, (0, 0), flag=wx.EXPAND, proportion=1)
        sizer.Insert(self.__numVisible + 1, self.__rightButton)
        sizer.Insert(0,                     self.__leftButton)

        self.Layout()


    def GenerateTools(self, toolSpecs, targets, add=True):
        """
        Targets may be a single object, or a dict of [toolSpec : target]
        mappings.
        """
        
        tools  = []
        labels = []

        if not isinstance(targets, dict):
            targets = {s.key : targets for s in toolSpecs}

        for toolSpec in toolSpecs:
            tool = props.buildGUI(
                self, targets[toolSpec.key], toolSpec, showUnlink=False)

            if isinstance(toolSpec, actions.ActionButton):
                label = None
            else:
                
                label = strings.properties.get(
                    (targets[toolSpec.key], toolSpec.key), toolSpec.key)

            tools .append(tool)
            labels.append(label)

            if add:
                self.InsertTool(tool, label, postevent=False)

        if add:
            wx.PostEvent(self, ToolBarEvent())

        return zip(tools, labels)

            
    def GetTools(self):
        """
        """
        return self.__tools[:]


    def AddTool(self, tool, labelText=None):
        self.InsertTool(tool, labelText)

        
    def InsertTools(self, tools, labels=None, index=None):

        if labels is None:
            labels = [None] * len(tools)

        for i, (tool, label) in enumerate(zip(tools, labels), index):
            self.InsertTool(tool, label, i, postevent=False)

        wx.PostEvent(self, ToolBarEvent())


    def SetTools(self, tools, labels=None, destroy=False):

        if labels is None:
            labels = [None] * len(tools)

        self.ClearTools(destroy, postevent=False)

        for tool, label in zip(tools, labels):
            self.InsertTool(tool, label, postevent=False)

        wx.PostEvent(self, ToolBarEvent())
        

    def InsertTool(self, tool, labelText=None, index=None, postevent=True):

        if index is None:
            index = len(self.__tools)

        if labelText is None:
            label = None
            
        else:
            label = wx.StaticText(self,
                                  label=labelText,
                                  style=wx.ALIGN_CENTRE)
            label.SetFont(label.GetFont().Smaller().Smaller())

            # Mouse wheel on the label will scroll
            # through the toolbar items. We don't
            # bind on the tool widget, because it
            # might already be intercepting mouse
            # wheel events
            label.Bind(wx.EVT_MOUSEWHEEL, self.__onMouseWheel)

        log.debug('{}: adding tool at index {}: {}'.format(
            type(self).__name__, index, labelText))

        toolPanel = FSLViewToolBar.Tool(self, tool, label, labelText)
        
        toolPanel.Bind(wx.EVT_MOUSEWHEEL, self.__onMouseWheel)

        self.__tools.insert(index, toolPanel)

        self.InvalidateBestSize()
        self.__drawToolBar()

        if postevent:
            wx.PostEvent(self, ToolBarEvent())
            

    def DoGetBestSize(self):
        # Calculate the minimum/maximum size
        # for this toolbar, given the addition
        # of the new tool
        ttlWidth  = 0
        minWidth  = 0
        minHeight = 0

        for tool in self.__tools:
            tw, th = tool.GetBestSize().Get()
            if tw > minWidth:  minWidth  = tw
            if th > minHeight: minHeight = th

            ttlWidth += tw

        leftWidth  = self.__leftButton .GetBestSize().GetWidth()
        rightWidth = self.__rightButton.GetBestSize().GetWidth()

        minWidth = minWidth + leftWidth + rightWidth

        # The agw.AuiManager does not honour the best size when
        # toolbars are floated, but it does honour the minimum
        # size. So I'm just setting the minimum size to the best
        # size.
        log.debug('Setting toolbar sizes: min {}, best {}'.format(
            (ttlWidth, minHeight), (ttlWidth, minHeight)))
        
        self.SetMinSize((   ttlWidth, minHeight))
        self.SetMaxSize((   ttlWidth, minHeight))
        self.CacheBestSize((ttlWidth, minHeight))
        
        return (ttlWidth, minHeight)
        

    
    def ClearTools(
            self,
            destroy=False,
            startIdx=None,
            endIdx=None,
            postevent=True):
 
        if len(self.__tools) == 0:
            return

        if startIdx is None: startIdx = 0
        if endIdx   is None: endIdx   = len(self.__tools)

        for i in range(startIdx, endIdx):
            tool = self.__tools[i]

            self.__sizer.Detach(tool)
            
            if destroy:
                tool.Destroy()

        self.__tools[startIdx:endIdx] = []

        self.InvalidateBestSize()
        self.Layout()

        if postevent:
            wx.PostEvent(self, ToolBarEvent())
