#!/usr/bin/env python
#
# locationpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.props as props




class LocationPanel(wx.Panel, props.HasProperties):

    voxelLocation = props.Point(ndims=3, real=False, labels=('X', 'Y', 'Z'))


    def _adjustFont(self, label, by, weight):
        font = label.GetFont()
        font.SetPointSize(font.GetPointSize() + by)
        font.SetWeight(weight)
        label.SetFont(font)

        
    def __init__(self, parent, imageList):

        wx.Panel.__init__(self, parent)
        props.HasProperties.__init__(self)

        self.imageList = imageList

        self._locationLabel  = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._locationWidget = props.makeWidget(self, imageList, 'location')
        self._dividerLine    = wx.StaticLine(   self, style=wx.LI_HORIZONTAL)
        self._voxelLabel     = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._voxelWidget    = props.makeWidget(self, self, 'voxelLocation')

        self._adjustFont(self._locationLabel, -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._voxelLabel,    -2, wx.FONTWEIGHT_LIGHT)

        self._locationLabel.SetLabel('World location (mm)')

        self._sizer = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self._sizer)
        self._sizer.Add(self._locationLabel,  flag=wx.EXPAND)
        self._sizer.Add(self._locationWidget, flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine,    flag=wx.EXPAND)
        self._sizer.Add(self._voxelLabel,     flag=wx.EXPAND)
        self._sizer.Add(self._voxelWidget,    flag=wx.EXPAND)

        self.Layout()

        lName = '{}_{}'.format(self.__class__.__name__, id(self))
        self.imageList.addListener('selectedImage',
                                   lName,
                                   self._selectedImageChanged)
        self.imageList.addListener('location',
                                   lName,
                                   self._worldLocationChanged)
        self.addListener(          'voxelLocation',
                                   lName,
                                   self._voxelLocationChanged)

        self._selectedImageChanged()
        self._worldLocationChanged()


    def _voxelLocationChanged(self, *a):

        image    = self.imageList[self.imageList.selectedImage]
        voxLoc   = self.voxelLocation.xyz
        worldLoc = image.voxToWorld([voxLoc])[0]
        
        self.imageList.location.xyz = worldLoc


    def _worldLocationChanged(self, *a):

        image  = self.imageList[self.imageList.selectedImage]
        loc    = self.imageList.location.xyz
        voxLoc = image.worldToVox([loc])[0]

        for i in range(3):

            # we explicitly allow voxLoc[i] == image.shape[i] -
            # the voxelLocation property values are clamped to
            # the image shape anyway
            if voxLoc[i] < 0 or voxLoc[i] > image.shape[i]:
                return

        self.voxelLocation.xyz = voxLoc
        
    def _selectedImageChanged(self, *a):

        image = self.imageList[self.imageList.selectedImage]
        
        self._voxelLabel.SetLabel('Voxel coordinates ({})'.format(image.name))

        for i in range(3):
            self.voxelLocation.setLimits(i, 0, image.shape[i])
