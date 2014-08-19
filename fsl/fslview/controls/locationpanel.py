#!/usr/bin/env python
#
# locationpanel.py - Panel which displays controls allowing the user to change
# the currently displayed location in both real world and voxel coordinates
# (with the latter in terms of the currently selected image)
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import numpy as np

import props

import fsl.fslview.controlpanel as controlpanel
import imageselectpanel         as imageselect

class LocationPanel(controlpanel.ControlPanel, props.HasProperties):
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

        
    def __init__(self, parent, imageList, displayCtx):
        """
        Creates and lays out the LocationPanel, and sets up a few property
        event listeners.
        """

        controlpanel.ControlPanel.__init__(self, parent, imageList, displayCtx)

        self._voxelPanel = wx.Panel(self)

        self._imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx)

        self._locationLabel  = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._locationWidget = props.makeWidget(self, displayCtx, 'location')
        
        self._dividerLine1   = wx.StaticLine(   self, style=wx.LI_HORIZONTAL)
        self._voxelWidget    = props.makeWidget(self, self, 'voxelLocation')
        
        self._dividerLine2   = wx.StaticLine(   self, style=wx.LI_HORIZONTAL) 
        self._volumeLabel    = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._volumeWidget   = props.makeWidget(self, displayCtx, 'volume')
        
        self._voxelLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_LEFT)
        self._valueLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_RIGHT)

        self._adjustFont(self._locationLabel, -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._volumeLabel,   -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._voxelLabel,    -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._valueLabel,    -2, wx.FONTWEIGHT_LIGHT)

        self._locationLabel.SetLabel('World location (mm)')
        self._voxelLabel   .SetLabel('Voxel coordinates')
        self._volumeLabel  .SetLabel('Volume (index)')

        self._voxelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._voxelPanel.SetSizer(self._voxelSizer)

        self._voxelSizer.Add(self._voxelLabel, flag=wx.EXPAND)
        self._voxelSizer.Add((1, 1),           flag=wx.EXPAND, proportion=1)
        self._voxelSizer.Add(self._valueLabel, flag=wx.EXPAND)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._imageSelect,    flag=wx.EXPAND)
        self._sizer.Add(self._locationLabel,  flag=wx.EXPAND)
        self._sizer.Add(self._locationWidget, flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine1,   flag=wx.EXPAND)
        self._sizer.Add(self._voxelPanel,     flag=wx.EXPAND)
        self._sizer.Add(self._voxelWidget,    flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine2,   flag=wx.EXPAND) 
        self._sizer.Add(self._volumeLabel,    flag=wx.EXPAND)
        self._sizer.Add(self._volumeWidget,   flag=wx.EXPAND)

        self._voxelPanel.Layout()
        self.Layout()
        
        self._imageList.addListener( 'images',
                                     self._name,
                                     self._selectedImageChanged) 
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        self._displayCtx.addListener('volume',
                                     self._name,
                                     self._volumeChanged) 
        self._displayCtx.addListener('location',
                                     '{}_worldToVox'.format(self._name),
                                     self._worldLocationChanged)
        self.addListener(            'voxelLocation',
                                     '{}_voxToWorld'.format(self._name),
                                     self._voxelLocationChanged)

        def onDestroy(ev):
            ev.Skip()
            self._imageList.removeListener( 'images',        self._name)
            self._displayCtx.removeListener('selectedImage', self._name)
            self._displayCtx.removeListener('volume',        self._name)
            self._displayCtx.removeListener('location',
                                            '{}_worldToVox'.format(self._name))
            
        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)

        self._selectedImageChanged()
        self._volumeChanged()
        self._worldLocationChanged()


    def _updateVoxelValue(self, voxVal=None):
        """
        Retrieves the value of the voxel at the current location in the
        currently selected image, and displays it on the value label.
        If the voxVal argument is provided, it is displayed. Otherwise
        the value at the current voxel location is displayed.
        """

        if voxVal is not None:
            self._valueLabel.SetLabel('{}'.format(voxVal))
            self._voxelPanel.Layout()
            return
        
        image  = self._imageList[self._displayCtx.selectedImage]
        volume = self._displayCtx.volume
        voxLoc = self.voxelLocation.xyz
        
        if voxVal is None:

            # There's a chance that the voxel location will temporarily
            # be out of bounds when the selected image is changed.
            # So we'll be safe and check them.
            for i in range(3):
                if voxLoc[i] < 0 or voxLoc[i] >= image.shape[i]:
                    return

            # 3D image
            if len(image.shape) == 3:
                voxVal = image.data[voxLoc[0], voxLoc[1], voxLoc[2]]

            # 4D image. This will crash on non-4D images,
            # which is intentional for the time being.
            else:
                if volume >= image.shape[3]:
                    return
                voxVal = image.data[voxLoc[0], voxLoc[1], voxLoc[2], volume]

            if   np.isnan(voxVal): voxVal = 'NaN'
            elif np.isinf(voxVal): voxVal = 'Inf'

        self._valueLabel.SetLabel('{}'.format(voxVal))
        self._voxelPanel.Layout()

        
    def _volumeChanged(self, *a):
        """Called when the
        :attr:`fsl.fslview.displaycontext.DisplayContext.volume`
        property changes. Updates the voxel value label.
        """

        volume  = self._displayCtx.volume

        if len(self._imageList) == 0:
            return

        image  = self._imageList[self._displayCtx.selectedImage]
        voxVal = None
        
        if image.is4DImage():
            if volume >= image.shape[3]:
                voxVal = strings.locationPanelOutOfBounds
            
        elif volume > 0:
            voxVal = strings.locationPanelOutOfBounds

        self._updateVoxelValue(voxVal)


    def _voxelLocationChanged(self, *a):
        """
        Called when the current voxel location is changed. Propagates the
        change on to the display context world location.
        """

        image       = self._imageList[self._displayCtx.selectedImage]
        voxLoc      = self.voxelLocation.xyz
        worldLoc    = image.voxToWorld([voxLoc])[0]
        worldVoxLoc = image.worldToVox([self._displayCtx.location.xyz])[0]
        worldVoxLoc = np.round(worldVoxLoc)

        self._updateVoxelValue()

        # if the current image list location is already equal to the
        # new voxel location, don't change it. The voxel location,
        # transformed to world coordinates, will be in the centre of
        # voxel. But the world location can be anywhere within a
        # voxel. So if the world location is already in the correct
        # voxel, we don't want it to be shifted to the voxel centre.
        if all([vl == wvl for (vl, wvl) in zip(voxLoc, worldVoxLoc)]): return
        
        self._displayCtx.location.xyz = worldLoc


    def _worldLocationChanged(self, *a):
        """
        Called when the current location in the image list world changes.
        Propagates the change on to the voxel location in the currently
        selected image.
        """

        if len(self._imageList) == 0: return

        image  = self._imageList[self._displayCtx.selectedImage]
        loc    = self._displayCtx.location.xyz
        voxLoc = np.round(image.worldToVox([loc]))[0]

        inBounds = True

        # If the selected world location is not within the selected
        # image, we're going to temporarily disable notification on
        # the voxel location property, because this would otherwise
        # cause some infinite-property-listener-callback-recursion
        # nastiness.
        for i in range(3):

            # allow the voxel location values to be equal to the image
            if voxLoc[i] < 0 or voxLoc[i] > image.shape[i]:
                inBounds = False

        if not inBounds:
            self._updateVoxelValue(voxVal=strings.locationPanelOutOfBounds)
            self.voxelLocation.disableNotification()

        self.voxelLocation.xyz = voxLoc
        self.voxelLocation.enableNotification()

        
    def _selectedImageChanged(self, *a):
        """
        Called when the selected image is changed. Updates the voxel label
        (which contains the image name), and sets the voxel location limits.
        """

        if len(self._imageList) == 0:
            self._updateVoxelValue('')
            self._voxelPanel.Layout()
            return

        image = self._imageList[self._displayCtx.selectedImage]
        
        self._voxelPanel.Layout()

        oldLoc = self._displayCtx.location.xyz
        voxLoc = np.round(image.worldToVox([oldLoc]))[0]

        for i in range(3):
            self.voxelLocation.setLimits(i, 0, image.shape[i] - 1)

        self.voxelLocation.xyz = voxLoc

        # The voxel coordinates may have inadvertently been
        # changed due to a change in their limits. So we'll
        # restore the old location from the real world
        # coordinates.
        self._displayCtx.location.xyz = oldLoc

# strings imports locationpanel, so this is
# at the bottom to avoid a circular import
import fsl.fslview.strings as strings
