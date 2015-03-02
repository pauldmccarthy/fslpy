#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides two classes - the :class:`FSLViewPanel`, and the
:class:`FSLViewToolBar`.

A :class:`FSLViewPanel` object is a :class:`wx.Panel` which provides some
sort of view of a collection of :class:`~fsl.data.image.Image` objects,
contained within an :class:`~fsl.data.image.ImageList`. Similarly, a
:class:`FSLViewToolBar` is a :class:`wx.lib.agw.aui.AuiToolBar` which
provides some sort of control over the view.

Instances of these classes are also
:class:`~fsl.fslview.actions.ActionProvider` instances - any actions which
are specified during construction may be exposed to the user. Furthermore,
any display configuration options which should be made available available
to the user should be added as :class:`~props.PropertyBase` attributes of
the :class:`FSLViewPanel` subclass.

See the following for examples of :class:`FSLViewPanel` subclasses:

  - :class:`~fsl.fslview.views.OrthoPanel`
  - :class:`~fsl.fslview.views.LightBoxPanel`
  - :class:`~fsl.fslview.views.TimeSeriesPanel`
  - :class:`~fsl.fslview.controls.ImageListPanel`
  - :class:`~fsl.fslview.controls.ImageDisplayPanel`
  - :class:`~fsl.fslview.controls.LocationPanel`
"""


import logging

import wx

import fsl.data.image as fslimage

import actions
import displaycontext


log = logging.getLogger(__name__)


class _FSLViewPanel(actions.ActionProvider):
    """Superclass for FSLView view panels.

    A :class:`ViewPanel` has the following attributes, intended to be
    used by subclasses:
    
      - :attr:`_imageList`: A reference to the
        :class:`~fsl.data.image.ImageList` instance which contains the images
        to be displayed.
    
      - :attr:`_displayCtx`: A reference to the
        :class:`~fsl.fslview.displaycontext.DisplayContext` instance, which
        contains display related properties about the :attr:`_imageList`.
    
      - :attr:`_name`: A unique name for this :class:`ViewPanel`.
    """ 

    
    def __init__(self,
                 imageList,
                 displayCtx,
                 actionz=None):
        """Create a :class:`ViewPanel`.

        :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.
        
        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         instance.

        :arg actionz:    A dictionary containing ``{name -> function}``
                         actions (see
                         :class:`~fsl.fslview.actions.ActionProvider`).
        """
        
        actions.ActionProvider.__init__(self, imageList, displayCtx, actionz)

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.image.ImageList instance')

        if not isinstance(displayCtx, displaycontext.DisplayContext):
            raise TypeError(
                'displayCtx must be a '
                'fsl.fslview.displaycontext.DisplayContext instance') 

        self._imageList  = imageList
        self._displayCtx = displayCtx
        self._name       = '{}_{}'.format(self.__class__.__name__, id(self))
        self.__destroyed = False

        
    def destroy(self):
        """This method must be called by whatever is managing this
        :class:`FSLViewPanel` when it is to be closed/destroyed. It seems to
        be impossible to define a single handler (on either the
        :attr:`wx.EVT_CLOSE` and/or :attr:`wx.EVT_WINDOW_DESTROY` events)
        which handles both cases where the window is destroyed (in the
        process of destroying a parent window), and where the window is
        explicitly closed by the user (e.g. when embedded as a page in
        a Notebook). 

        This issue is probably caused by my use of the AUI framework for
        layout management, as the AUI manager/notebook classes do not seem to
        call close/destroy in all cases. Everything that I've tried, which
        relies upon EVT_CLOSE/EVT_WINDOW_DESTROY events, inevitably results in
        the event handlers not being called, or in segmentation faults
        (presumably due to double-frees at the C++ level).

        Subclasses which need to perform any cleaning up when they are closed
        may override this method, and should be able to assume that it will be
        called. So this method *must* be called by managing code when a panel
        is deleted.

        Overriding subclass implementations should also call this base class
        method, otherwise warnings will probably be output to the log (see 
        :meth:`__del__`)
        """
        self.__destroyed = True

    
    def __del__(self):

        if not self.__destroyed:
            log.warning('The {}.destroy() method has not been called '
                        '- unless the application is shutting down, '
                        'this is probably a bug!'.format(type(self).__name__))

        actions.ActionProvider.__del__(self)


class FSLViewPanel(_FSLViewPanel, wx.Panel):
    def __init__(self, parent, imageList, displayCtx, actionz=None):
        wx.Panel.__init__(self, parent)
        _FSLViewPanel.__init__(self, imageList, displayCtx, actionz)

        import fsl.fslview.layouts as layouts
        self.SetMinSize(layouts.minSizes.get(self, (-1, -1)))

        
    def __del__(self):
        wx.Panel     .__del__(self)
        _FSLViewPanel.__del__(self)

        
class FSLViewToolBar(_FSLViewPanel, wx.Panel):
    """
    """


    class Tool(object):

        
        def __init__(self, tool, label, labelText):
            self.tool      = tool
            self.label     = label
            self.labelText = labelText


        def __str__(self):
            return '{}: {} ({}, {})'.format(
                type(self)      .__name__,
                type(self.tool) .__name__,
                type(self.label).__name__,
                self.labelText)

            
    def __init__(self, parent, imageList, displayCtx, actionz=None):
        wx.Panel.__init__(self, parent)
        _FSLViewPanel.__init__(self, imageList, displayCtx, actionz)

        import fsl.fslview.layouts as layouts
        self.SetMinSize(layouts.minSizes.get(self, (-1, -1)))

        self.__sizer = wx.GridBagSizer()
        self.__tools = []
        
        self.SetSizer(self.__sizer)


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

        self.__tools.insert(index, FSLViewToolBar.Tool(tool, label, labelText))
        self.__LayoutTools()

        
    def __LayoutTools(self):

        self.__sizer.Clear()

        for i, tool in enumerate(self.__tools):

            flag = wx.ALIGN_CENTRE

            if tool.label is None:
                self.__sizer.Add(tool.tool,  (0, i), (2, 1), flag=flag)

            else:
                self.__sizer.Add(tool.tool,  (0, i), flag=flag)
                self.__sizer.Add(tool.label, (1, i), flag=wx.EXPAND)

        self.Layout()

    
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
        wx.Panel     .__del__(self)
        _FSLViewPanel.__del__(self)        
