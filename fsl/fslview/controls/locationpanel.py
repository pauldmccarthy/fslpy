#!/usr/bin/env python
#
# locationpanel.py - provides the LocationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LocationPanel` class, a panel which
displays controls allowing the user to change the currently displayed location
in both real world and voxel coordinates, both in the space of the currently
selected image.

These changes are propagated to the current display coordinate system
location, managed by the display context (and external changes to the display
context location are propagated back to the voxel/world location properties
managed by a :class:`LocationPanel`).
"""

import logging

import wx

import numpy as np

import props

import fsl.utils.transform as transform
import fsl.data.strings    as strings
import fsl.fslview.panel   as fslpanel


log = logging.getLogger(__name__)


class LocationPanel(fslpanel.FSLViewPanel):
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

        fslpanel.FSLViewPanel.__init__(self, parent, imageList, displayCtx)

        voxX, voxY, voxZ = props.makeListWidgets(
            self,
            self,
            'voxelLocation',
            slider=False,
            spin=True,
            showLimits=False)
        worldX, worldY, worldZ = props.makeListWidgets(
            self,
            self,
            'worldLocation',
            slider=False,
            spin=True,
            showLimits=False) 

        self.voxX      = voxX
        self.voxY      = voxY
        self.voxZ      = voxZ
        self.worldX    = worldX
        self.worldY    = worldY
        self.worldZ    = worldZ
        self.volume    = props.makeWidget(self,
                                          displayCtx,
                                          'volume',
                                          slider=False,
                                          spin=True,
                                          showLimits=False)
        
        self.intensity = wx.TextCtrl(self, style=wx.TE_READONLY)
        self.space     = wx.TextCtrl(self, style=wx.TE_READONLY)

        self.voxLabel   = wx.StaticText(
            self, label=strings.labels[self, 'voxelLocation'])
        self.worldLabel = wx.StaticText(
            self, label=strings.labels[self, 'worldLocation'])
        self.volumeLabel = wx.StaticText(
            self, label=strings.labels[self, 'volume'])
        self.spaceLabel = wx.StaticText(
            self, label=strings.labels[self, 'space']) 
        self.intensityLabel = wx.StaticText(
            self, label=strings.labels[self, 'intensity']) 

        self.sizer = wx.FlexGridSizer(4, 4)
        self.SetSizer(self.sizer)

        self.sizer.Add(self.voxLabel,       flag=wx.EXPAND)
        self.sizer.Add(self.worldLabel,     flag=wx.EXPAND)
        self.sizer.Add((0, 0))
        self.sizer.Add((0, 0))
        self.sizer.Add(self.voxX,           flag=wx.EXPAND)
        self.sizer.Add(self.worldX,         flag=wx.EXPAND)
        self.sizer.Add(self.volumeLabel,    flag=wx.EXPAND)
        self.sizer.Add(self.volume,         flag=wx.EXPAND)
        
        self.sizer.Add(self.voxY,           flag=wx.EXPAND)
        self.sizer.Add(self.worldY,         flag=wx.EXPAND)
        self.sizer.Add(self.intensityLabel, flag=wx.EXPAND) 
        self.sizer.Add(self.intensity,      flag=wx.EXPAND) 
        self.sizer.Add(self.voxZ,           flag=wx.EXPAND)
        self.sizer.Add(self.worldZ,         flag=wx.EXPAND)
        self.sizer.Add(self.spaceLabel,     flag=wx.EXPAND)
        self.sizer.Add(self.space,          flag=wx.EXPAND)

        self._adjustFont(self.voxLabel,       -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.worldLabel,     -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.volumeLabel,    -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.spaceLabel,     -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.intensityLabel, -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.intensity,      -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.space,          -2, wx.FONTWEIGHT_LIGHT)

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

        self._selectedImageChanged()
        self._volumeChanged()

        self.SetMinSize(self.sizer.GetMinSize())


    def destroy(self):
        """Deregisters property listeners."""
        fslpanel.FSLViewPanel.destroy(self)

        self._imageList.removeListener( 'images',        self._name)
        self._displayCtx.removeListener('selectedImage', self._name)
        self._displayCtx.removeListener('imageOrder',    self._name)
        self._displayCtx.removeListener('volume',        self._name)
        self._displayCtx.removeListener('location',      self._name)


    def _updateVoxelValue(self, voxVal=None):
        """
        Retrieves the value of the voxel at the current location in the
        currently selected image, and displays it on the value label.
        If the voxVal argument is provided, it is displayed. Otherwise
        the value at the current voxel location is displayed.
        """

        if len(self._imageList) == 0:
            voxVal = ''

        if voxVal is not None:
            self.intensity.SetValue('{}'.format(voxVal))
            return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        dloc   = self._displayCtx.location.xyz
        vloc   = transform.transform(
            [dloc], display.getTransform('display', 'voxel'))[0]
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
            voxVal = strings.labels[self, 'outOfBounds']
            
        else:
            
            log.debug('Looking up voxel value in {} ({}, {} -> {})'.format(
                image, vloc, volume, image.shape))
            
            # 3D image
            if len(image.shape) == 3:
                voxVal = image.data[vloc[0], vloc[1], vloc[2]]

            # No support for images of more
            # than 4 dimensions at the moment
            else:
                voxVal = image.data[vloc[0], vloc[1], vloc[2], volume]

            if   np.isnan(voxVal): voxVal = 'NaN'
            elif np.isinf(voxVal): voxVal = 'Inf'

        self.intensity.SetValue('{}'.format(voxVal))

        
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
        vloc = transform.transform(
            [dloc], display.getTransform('display', 'voxel'))[0]
        wloc = transform.transform(
            [dloc], display.getTransform('display', 'world'))[0]

        import fsl.utils.trace as trace
        trace.trace('LocationPanel')

        log.debug('Updating location ({} -> vox {}, world {})'.format(
            dloc, vloc, wloc))
        
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
        dloc = transform.transform(
            [vloc], display.getTransform('voxel', 'display'))[0]
        wloc = transform.transform(
            [vloc], display.getTransform('voxel', 'world'))[  0]

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
        dloc = transform.transform(
            [wloc], display.getTransform('world', 'display'))[0]
        vloc = transform.transform(
            [wloc], display.getTransform('world', 'voxel'))[  0]

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

        if len(self._imageList) == 0:
            self._updateVoxelValue(   '')
            self.space.SetValue('')
            return

        image   = self._displayCtx.getSelectedImage()
        display = self._displayCtx.getDisplayProperties(image)

        # Update the label which
        # displays the image space 
        spaceLabel = strings.anatomy['Image', 'space', image.getXFormCode()]
        self.space.SetValue(spaceLabel)

        # Update the voxel and world location limits,
        # but don't trigger a listener callback, as
        # this would change the display location.
        self.disableNotification('worldLocation')
        self.disableNotification('voxelLocation')

        self._displayCtx.disableListener('location', self._name)
        
        for i in range(3):
            vlo, vhi = 0, image.shape[i] - 1
            wlo, whi = transform.axisBounds(
                image.shape, display.getTransform('voxel', 'world'), i)

            self.voxelLocation.setLimits(i, vlo, vhi)
            self.worldLocation.setLimits(i, wlo, whi)

        self._displayCtx.enableListener('location', self._name) 

        self.enableNotification('worldLocation')
        self.enableNotification('voxelLocation')

        # Refresh the world/voxel location properties
        self._displayLocationChanged()
