#!/usr/bin/env python
#
# locationpanel.py - Panel which displays controls allowing the user to change
# the currently displayed location in both real world and voxel coordinates
# (with the latter in terms of the currently selected image)
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.props as props

class LocationPanel(wx.Panel, props.HasProperties):
    """
    A wx.Panel which contains widgets for changing the currently displayed
    location in both world coordinates, and voxel coordinates (in terms of the
    currently selected image). Also contains a label which contains the name
    of the currently selected image and the value, in that image, at the
    currently selected voxel.
    """

    voxelLocation = props.Point(ndims=3, real=False, labels=('X', 'Y', 'Z'))


    def _adjustFont(self, label, by, weight):
        """
        Adjusts the font of the given wx.StaticText widget (or any other
        widget which has a font) by the specified amount. Also sets the
        font weight to the given weight.
        """
        font = label.GetFont()
        font.SetPointSize(font.GetPointSize() + by)
        font.SetWeight(weight)
        label.SetFont(font)

        
    def __init__(self, parent, imageList):
        """
        Creates and lays out the LocationPanel, and sets up a few property
        event listeners.
        """

        wx.Panel.__init__(self, parent)
        props.HasProperties.__init__(self)

        self.imageList = imageList

        self._voxelPanel = wx.Panel(self)

        self._locationLabel  = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._locationWidget = props.makeWidget(self, imageList, 'location')
        self._dividerLine    = wx.StaticLine(   self, style=wx.LI_HORIZONTAL)
        self._voxelWidget    = props.makeWidget(self, self, 'voxelLocation')
 
        self._voxelLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_LEFT)
        self._valueLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_RIGHT)

        self._adjustFont(self._locationLabel, -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._voxelLabel,    -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._valueLabel,    -2, wx.FONTWEIGHT_LIGHT)

        self._locationLabel.SetLabel('World location (mm)')

        self._voxelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._voxelPanel.SetSizer(self._voxelSizer)

        self._voxelSizer.Add(self._voxelLabel, flag=wx.EXPAND)
        self._voxelSizer.Add((1, 1),           flag=wx.EXPAND, proportion=1)
        self._voxelSizer.Add(self._valueLabel, flag=wx.EXPAND)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)
 
        self._sizer.Add(self._locationLabel,  flag=wx.EXPAND)
        self._sizer.Add(self._locationWidget, flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine,    flag=wx.EXPAND)
        self._sizer.Add(self._voxelPanel,     flag=wx.EXPAND)
        self._sizer.Add(self._voxelWidget,    flag=wx.EXPAND)

        self._voxelPanel.Layout()
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


    def _updateVoxelValue(self):
        """
        Retrieves the value of the voxel at the current location in the
        currently selected image, and displays it on the value label.
        """
        
        image  = self.imageList[self.imageList.selectedImage]
        voxLoc = self.voxelLocation.xyz

        # 3D image
        if len(image.shape) == 3:
            voxVal = image.data[voxLoc[0], voxLoc[1], voxLoc[2]]
            
        # 4D image. This will crash on non-4D images,
        # which is intentional for the time being.
        else:

            # This will not work if an ImageDisplay
            # instance other than the image.display
            # property is in use.
            volume = image.display.volume
            voxVal = image.data[voxLoc[0], voxLoc[1], voxLoc[2], volume]

        self._valueLabel.SetLabel('{}'.format(voxVal))
        self._voxelPanel.Layout()


    def _voxelLocationChanged(self, *a):
        """
        Called when the current voxel location is changed. Propagates the
        change on to the image list world location, and updates the voxel
        value label.
        """

        image    = self.imageList[self.imageList.selectedImage]
        voxLoc   = self.voxelLocation.xyz
        worldLoc = image.voxToWorld([voxLoc])[0]
        
        self.imageList.location.xyz = worldLoc

        self._updateVoxelValue()


    def _worldLocationChanged(self, *a):
        """
        Called when the current location in the image list world changes.
        Propagates the change on to the voxel location in the currently
        selected image.
        """

        image  = self.imageList[self.imageList.selectedImage]
        loc    = self.imageList.location.xyz
        voxLoc = image.worldToVox([loc])[0]

        # We explicitly clamp the voxel location values so we don't
        # trigger any infinite property event callback loops
        for i in range(3):

            if   voxLoc[i] < 0:               voxLoc[i] = 0
            elif voxLoc[i] >= image.shape[i]: voxLoc[i] = image.shape[i] - 1

        self.voxelLocation.xyz = voxLoc

        
    def _selectedImageChanged(self, *a):
        """
        Called when the selected image is changed. Updates the voxel label
        (which contains the image name), and sets the voxel location limits.
        """

        image = self.imageList[self.imageList.selectedImage]
        
        self._voxelLabel.SetLabel('Voxel coordinates ({})'.format(image.name))
        self._voxelPanel.Layout()

        for i in range(3):
            self.voxelLocation.setLimits(i, 0, image.shape[i] - 1)
