#!/usr/bin/env python
#
# locationpanel.py - Panel which displays controls allowing the user to change
# the currently displayed location in both real world and voxel coordinates,
# both in the space of the currently selected image. These changes are
# propagated to the current display coordinate system location, managed by the
# display context (and external changes to the display context location are
# propagated back to the voxel/world location properties managed by a
# Location Panel).
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import wx

import numpy as np

import props

import fsl.utils.transform      as transform
import fsl.fslview.controlpanel as controlpanel
import imageselectpanel         as imageselect

log = logging.getLogger(__name__)


class LocationPanel(controlpanel.ControlPanel, props.HasProperties):
    """
    A wx.Panel which contains widgets for changing the currently displayed
    location in both world coordinates, and voxel coordinates (in terms of the
    currently selected image). Also contains a label which contains the name
    of the currently selected image and the value, in that image, at the
    currently selected voxel.
    """

    
    voxelLocation = props.Point(ndims=3, real=False, labels=('X', 'Y', 'Z'))

    
    worldLocation = props.Point(ndims=3, real=True,  labels=('X', 'Y', 'Z'))


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
        import fsl.fslview.strings as strings

        controlpanel.ControlPanel.__init__(self, parent, imageList, displayCtx)

        self._voxelPanel = wx.Panel(self)
        self._worldPanel = wx.Panel(self)

        self._imageSelect = imageselect.ImageSelectPanel(
            self, imageList, displayCtx)

        self._worldLabel   = wx.StaticText(   self._worldPanel,
                                              style=wx.ALIGN_LEFT)
        self._spaceLabel   = wx.StaticText(   self._worldPanel,
                                              style=wx.ALIGN_LEFT)
        self._worldWidget  = props.makeWidget(self, self, 'worldLocation')
        
        self._dividerLine1 = wx.StaticLine(   self, style=wx.LI_HORIZONTAL)
        self._voxelWidget  = props.makeWidget(self, self, 'voxelLocation')
        
        self._dividerLine2 = wx.StaticLine(   self, style=wx.LI_HORIZONTAL) 
        self._volumeLabel  = wx.StaticText(   self, style=wx.ALIGN_LEFT)
        self._volumeWidget = props.makeWidget(self, displayCtx, 'volume')
        
        self._voxelLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_LEFT)
        self._valueLabel = wx.StaticText(self._voxelPanel,
                                         style=wx.ALIGN_RIGHT)

        self._adjustFont(self._worldLabel,  -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._spaceLabel,  -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._volumeLabel, -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._voxelLabel,  -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self._valueLabel,  -2, wx.FONTWEIGHT_LIGHT)

        self._worldLabel .SetLabel(strings.locationPanelWorldLabel)
        self._voxelLabel .SetLabel(strings.locationPanelVoxelLabel)
        self._volumeLabel.SetLabel(strings.locationPanelVolumeLabel)

        self._worldSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._worldPanel.SetSizer(self._worldSizer)

        self._worldSizer.Add(self._worldLabel, flag=wx.EXPAND)
        self._worldSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        self._worldSizer.Add(self._spaceLabel, flag=wx.EXPAND)

        self._voxelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self._voxelPanel.SetSizer(self._voxelSizer)

        self._voxelSizer.Add(self._voxelLabel, flag=wx.EXPAND)
        self._voxelSizer.Add((1, 1),           flag=wx.EXPAND, proportion=1)
        self._voxelSizer.Add(self._valueLabel, flag=wx.EXPAND)

        self._sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self._sizer)

        self._sizer.Add(self._imageSelect,  flag=wx.EXPAND)
        self._sizer.Add(self._worldPanel,   flag=wx.EXPAND)
        self._sizer.Add(self._worldWidget,  flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine1, flag=wx.EXPAND)
        self._sizer.Add(self._voxelPanel,   flag=wx.EXPAND)
        self._sizer.Add(self._voxelWidget,  flag=wx.EXPAND)
        self._sizer.Add(self._dividerLine2, flag=wx.EXPAND) 
        self._sizer.Add(self._volumeLabel,  flag=wx.EXPAND)
        self._sizer.Add(self._volumeWidget, flag=wx.EXPAND)

        self._voxelPanel.Layout()
        self.Layout()
        
        self._imageList.addListener( 'images',
                                     self._name,
                                     self._selectedImageChanged)
        self._displayCtx.addListener('imageOrder',
                                     self._name,
                                     self._selectedImageChanged) 
        self._displayCtx.addListener('selectedImage',
                                     self._name,
                                     self._selectedImageChanged)
        self._displayCtx.addListener('volume',
                                     self._name,
                                     self._volumeChanged) 
        self._displayCtx.addListener('location',
                                     self._name,
                                     self._displayLocationChanged)
        self.addListener(            'voxelLocation',
                                     self._name,
                                     self._voxelLocationChanged)
        self.addListener(            'worldLocation',
                                     self._name,
                                     self._worldLocationChanged)

        def onDestroy(ev):
            ev.Skip()
            self._imageList.removeListener( 'images',        self._name)
            self._displayCtx.removeListener('selectedImage', self._name)
            self._displayCtx.removeListener('imageOrder',    self._name)
            self._displayCtx.removeListener('volume',        self._name)
            self._displayCtx.removeListener('location',      self._name)
            
        self.Bind(wx.EVT_WINDOW_DESTROY, onDestroy)
        
        self._selectedImageChanged()
        self._displayLocationChanged()
        self._volumeChanged()


    def _updateVoxelValue(self, voxVal=None):
        """
        Retrieves the value of the voxel at the current location in the
        currently selected image, and displays it on the value label.
        If the voxVal argument is provided, it is displayed. Otherwise
        the value at the current voxel location is displayed.
        """

        import fsl.fslview.strings as strings

        if len(self._imageList) == 0:
            voxVal = ''

        if voxVal is not None:
            self._valueLabel.SetLabel('{}'.format(voxVal))
            self._voxelPanel.Layout()
            return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        dloc   = self._displayCtx.location.xyz
        vloc   = transform.transform([dloc], display.displayToVoxMat)[0]
        vloc   = np.round(vloc)
        volume = self._displayCtx.volume

        # Test to see if the voxel
        # location/volume is out of bounds
        inBounds = True
        for i in range(3):
            if vloc[i] < 0 or vloc[i] >= image.shape[i]:
                inBounds = False

        if image.is4DImage():
            if volume >= image.shape[3]:
                inBounds = False

        # If the value is out of the voxel bounds,
        # display some appropriate text
        if not inBounds:
            voxVal = strings.locationPanelOutOfBounds
            
        else:
            
            # 3D image
            if len(image.shape) == 3:
                voxVal = image.data[vloc[0], vloc[1], vloc[2]]

            # No support for images of more
            # than 4 dimensions at the moment
            else:
                voxVal = image.data[vloc[0], vloc[1], vloc[2], volume]

            if   np.isnan(voxVal): voxVal = 'NaN'
            elif np.isinf(voxVal): voxVal = 'Inf'

        self._valueLabel.SetLabel('{}'.format(voxVal))
        self._voxelPanel.Layout()

        
    def _volumeChanged(self, *a):
        """Called when the
        :attr:`fsl.fslview.displaycontext.DisplayContext.volume`
        property changes. Updates the voxel value label.
        """
        self._updateVoxelValue()
        

    def _displayLocationChanged(self, *a):

        if len(self._imageList) == 0: return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        dloc = self._displayCtx.location.xyz
        vloc = transform.transform([dloc], display.displayToVoxMat)[  0]
        wloc = transform.transform([dloc], display.displayToWorldMat)[0]

        self            .disableListener('voxelLocation', self._name)
        self            .disableListener('worldLocation', self._name)
        self._displayCtx.disableListener('location',      self._name)
        
        self.voxelLocation.xyz       = np.round(vloc)
        self.worldLocation.xyz       = wloc

        self            .enableListener('voxelLocation', self._name)
        self            .enableListener('worldLocation', self._name)
        self._displayCtx.enableListener('location',      self._name)

        self._updateVoxelValue()


    def _voxelLocationChanged(self, *a):
        """
        Called when the current voxel location is changed. Propagates the
        change on to the display context world location.
        """

        if len(self._imageList) == 0: return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        
        vloc = self.voxelLocation.xyz
        dloc = transform.transform([vloc], display.voxToDisplayMat)[0]
        wloc = transform.transform([vloc], display.voxToWorldMat)[  0]

        self            .disableListener('voxelLocation', self._name)
        self            .disableListener('worldLocation', self._name)
        self._displayCtx.disableListener('location',      self._name) 
        
        self._displayCtx.location.xyz = dloc
        self.worldLocation       .xyz = wloc

        self            .enableListener('voxelLocation', self._name)
        self            .enableListener('worldLocation', self._name)
        self._displayCtx.enableListener('location',      self._name) 

        self._updateVoxelValue()
        

    def _worldLocationChanged(self, *a):
        """
        Called when the current location in the image list world changes.
        Propagates the change on to the voxel location in the currently
        selected image.
        """

        if len(self._imageList) == 0: return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)
        
        wloc = self.worldLocation.xyz
        dloc = transform.transform([wloc], display.worldToDisplayMat)[0]
        vloc = transform.transform([wloc], display.worldToVoxMat)[    0]

        self            .disableListener('voxelLocation', self._name)
        self            .disableListener('worldLocation', self._name)
        self._displayCtx.disableListener('location',      self._name)
        
        self._displayCtx.location.xyz = dloc
        self.voxelLocation       .xyz = np.round(vloc)

        self            .enableListener('voxelLocation', self._name)
        self            .enableListener('worldLocation', self._name)
        self._displayCtx.enableListener('location',      self._name)
        
        self._updateVoxelValue()

        
    def _selectedImageChanged(self, *a):
        """
        Called when the selected image is changed. Updates the voxel label
        (which contains the image name), and sets the voxel location limits.
        """

        import fsl.fslview.strings as strings

        if len(self._imageList) == 0:
            self._updateVoxelValue(   '')
            self._spaceLabel.SetLabel('')
            self._worldPanel.Layout()
            return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        # Update the label which
        # displays the image space 
        spaceLabel = strings.imageSpaceLabels[image.getXFormCode()]
        spaceLabel = strings.locationPanelSpaceLabel.format(spaceLabel)
        self._spaceLabel.SetLabel(spaceLabel)
        self._worldPanel.Layout()

        # Update the voxel and world location limits,
        # but don't trigger a listener callback, as
        # this would change the display location.
        self.disableNotification('worldLocation')
        self.disableNotification('voxelLocation')

        self._displayCtx.disableListener('location', self._name)
        
        for i in range(3):
            vlo, vhi = 0, image.shape[i] - 1
            wlo, whi = transform.axisBounds(image.shape,
                                            display.voxToWorldMat,
                                            i)

            self.voxelLocation.setLimits(i, vlo, vhi)
            self.worldLocation.setLimits(i, wlo, whi)

        self._displayCtx.enableListener('location', self._name) 

        self.enableNotification('worldLocation')
        self.enableNotification('voxelLocation')

        # Refresh the world/voxel location properties
        self._displayLocationChanged()
