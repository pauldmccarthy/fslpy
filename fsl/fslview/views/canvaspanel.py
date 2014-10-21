#!/usr/bin/env python
#
# canvaspanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import wx

import props

import fsl.fslview.viewpanel as viewpanel
import colourbarpanel 


class CanvasPanel(viewpanel.ViewPanel):

    
    showCursor = props.Boolean(default=True)

    
    posSync = props.Boolean(default=True)
    """Should the position shown in each of the
    :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` instances 
    be synchronised to the :class:`~fsl.data.image.ImageList.location`
    :attr:`~fsl.data.image.ImageList.location` property?
    """
    
    showColourBar = props.Boolean(default=False)

    
    colourBarLocation = props.Choice({
        'top'    : 'Top',
        'bottom' : 'Bottom',
        'left'   : 'Left',
        'right'  : 'Right'})

    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide

    
    _labels = {
        'showCursor'         : 'Show cursor',
        'posSync'            : 'Synchronise location',
        'showColourBar'      : 'Show/hide colour bar',
        'colourBarLocation'  : 'Colour bar location',
        'colourBarLabelSide' : 'Colour bar label side'
    } 


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        viewpanel.ViewPanel.__init__(self,
                                     parent,
                                     imageList,
                                     displayCtx)

        self.__canvasPanel = wx.Panel(self)

        self.__colourBar = colourbarpanel.ColourBarPanel(
            self,
            self._imageList,
            self._displayCtx)


        self.bindProps('colourBarLabelSide', self.__colourBar, 'labelSide')

        self._configColourBar()

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('showColourBar',
                         lName,
                         self._configColourBar)
        self.addListener('colourBarLocation',
                         lName,
                         self._configColourBar)

    def getCanvasPanel(self):
        return self.__canvasPanel

        
    def _configColourBar(self, *a):
        """
        """


        if not self.showColourBar:
            self.__colourBar.Show(False)
            
            self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.__sizer.Add(self.__canvasPanel, flag=wx.EXPAND, proportion=1)
            
            self.SetSizer(self.__sizer)
            self.Layout()
            return
            
        if self.colourBarLocation in ('top', 'bottom'):
            self.__sizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.__sizer = wx.BoxSizer(wx.HORIZONTAL)

        if self.colourBarLocation in ('top', 'bottom'):
            self.__colourBar.orientation = 'horizontal'
        elif self.colourBarLocation == 'left':
            self.__colourBar.orientation = 'vertical'
        elif self.colourBarLocation == 'right':
            self.__colourBar.orientation = 'vertical'

        if self.colourBarLocation in ('top', 'left'):
            self.__sizer.Add(self.__colourBar,   flag=wx.EXPAND)
            self.__sizer.Add(self.__canvasPanel, flag=wx.EXPAND, proportion=1)
        else:
            self.__sizer.Add(self.__canvasPanel, flag=wx.EXPAND, proportion=1)
            self.__sizer.Add(self.__colourBar,   flag=wx.EXPAND)

        self.__colourBar.Show(True)
                
        self.SetSizer(self.__sizer)
        self.Layout()
