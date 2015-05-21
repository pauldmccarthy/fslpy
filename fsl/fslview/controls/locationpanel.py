#!/usr/bin/env python
#
# locationpanel.py - provides the LocationPanel class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`LocationPanel` class, a panel which
displays controls allowing the user to change the currently displayed location
in both world and local coordinates, both in the space of the currently
selected overlay.

These changes are propagated to the current display coordinate system
location, managed by the display context (and external changes to the display
context location are propagated back to the local/world location properties
managed by a :class:`LocationPanel`).
"""

import logging

import wx
import wx.html as wxhtml

import numpy as np

import props

import fsl.utils.transform as transform
import fsl.data.image      as fslimage
import fsl.data.strings    as strings
import fsl.fslview.panel   as fslpanel


log = logging.getLogger(__name__)


class LocationPanel(fslpanel.FSLViewPanel):
    """
    A wx.Panel which displays information about the current location,
    for each overlay in the overlay list.
    """

    
    voxelLocation = props.Point(ndims=3, real=False, labels=('X', 'Y', 'Z'))
    """If the currently selected overlay is a :class:`.Image`, this property
    tracks the current display location in voxel coordinates.
    """
    
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

        
    def __init__(self, parent, overlayList, displayCtx):
        """
        Creates and lays out the LocationPanel, and sets up a few property
        event listeners.
        """

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        # The world and voxel locations dispalyed by the LocationPanel
        # are only really relevant to volumetric (i.e. NIFTI) overlay
        # types. However, other overlay types (e.g. Model instances)
        # may have an associated 'reference' image, from which details
        # of the coordinate system may be obtained.
        #
        # When the current overlay is either an Image instance, or has
        # an associated reference image, these attributes are used to
        # store references to the image, and to the matrices that allow
        # transformations between the different coordinate systems.
        self._refImage          = None
        self._voxToDisplayMat   = None
        self._displayToVoxMat   = None
        self._worldToDisplayMat = None
        self._displayToWorldMat = None
        self._voxToWorldMat     = None
        self._worldToVoxMat     = None

        # When the currently selected overlay is 4D,
        # this attribute will refer to the
        # corresponding DisplayOpts instance, which
        # has a volume property that controls the
        # volume - see e.g. the ImageOpts class. This
        # attribute is set in _selectedOverlayChanged.
        self.volumeTarget = None

        self.column1 = wx.Panel(self)
        self.column2 = wx.Panel(self)
        self.info    = wxhtml.HtmlWindow(self)

        self.worldLabel  = wx.StaticText(
            self.column1, label=strings.labels[self, 'worldLocation'])
        self.volumeLabel = wx.StaticText(
            self.column1, label=strings.labels[self, 'volume']) 
        self.voxelLabel  = wx.StaticText(
            self.column2, label=strings.labels[self, 'voxelLocation'])

        worldX, worldY, worldZ = props.makeListWidgets(
            self.column1,
            self,
            'worldLocation',
            slider=False,
            spin=True,
            showLimits=False)

        voxelX, voxelY, voxelZ = props.makeListWidgets(
            self.column2,
            self,
            'voxelLocation',
            slider=False,
            spin=True,
            showLimits=False) 

        self.worldX = worldX
        self.worldY = worldY
        self.worldZ = worldZ
        self.voxelX = voxelX
        self.voxelY = voxelY
        self.voxelZ = voxelZ
        self.volume = wx.SpinCtrl(self.column2)
        self.volume.SetValue(0)

        self.column1Sizer = wx.BoxSizer(wx.VERTICAL)
        self.column2Sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer        = wx.BoxSizer(wx.HORIZONTAL)

        self.column1Sizer.Add(self.worldLabel,  flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldX,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldY,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.worldZ,      flag=wx.EXPAND)
        self.column1Sizer.Add(self.volumeLabel, flag=wx.ALIGN_RIGHT)

        self.column2Sizer.Add(self.voxelLabel, flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelX,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelY,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.voxelZ,     flag=wx.EXPAND)
        self.column2Sizer.Add(self.volume,     flag=wx.EXPAND)
        
        self.sizer.Add(self.column1, flag=wx.EXPAND)
        self.sizer.Add((5, -1))
        self.sizer.Add(self.column2, flag=wx.EXPAND)
        self.sizer.Add((5, -1))
        self.sizer.Add(self.info,    flag=wx.EXPAND, proportion=1)

        self._adjustFont(self.voxelLabel,  -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.worldLabel,  -2, wx.FONTWEIGHT_LIGHT)
        self._adjustFont(self.volumeLabel, -2, wx.FONTWEIGHT_LIGHT)

        self.column1.SetSizer(self.column1Sizer)
        self.column2.SetSizer(self.column2Sizer)
        self        .SetSizer(self.sizer)

        self.Layout()
        
        self._overlayList.addListener('overlays',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('overlayOrder',
                                      self._name,
                                      self._selectedOverlayChanged) 
        self._displayCtx .addListener('selectedOverlay',
                                      self._name,
                                      self._selectedOverlayChanged)
        self._displayCtx .addListener('location',
                                      self._name,
                                      self._displayLocationChanged)
        self.addListener(             'voxelLocation',
                                      self._name,
                                      self._voxelLocationChanged)
        self.addListener(             'worldLocation',
                                      self._name,
                                      self._worldLocationChanged)

        self._selectedOverlayChanged()

        self.SetMinSize(self.sizer.GetMinSize())


    def destroy(self):
        """Deregisters property listeners."""
        fslpanel.FSLViewPanel.destroy(self)

        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._displayCtx .removeListener('overlayOrder',    self._name)
        self._displayCtx .removeListener('location',        self._name)

        
    def _selectedOverlayChanged(self, *a):
        """Called when the selected overlay is changed. Updates the voxel label
        (which contains the overlay name), and sets the voxel location limits.
        """

        self._updateReferenceImage()
        self._updateWidgets()

        if len(self._overlayList) == 0:
            self._updateLocationInfo()
            return

        # Register a listener on the DisplayOpts 
        # instance of the currently selected overlay
        overlay = self._displayCtx.getSelectedOverlay()
        for ovl in self._overlayList:
            opts = self._displayCtx.getOpts(ovl)
            if ovl is overlay:
                opts.addGlobalListener(self._name,
                                       self._overlayOptsChanged,
                                       overwrite=True)
            else:
                opts.removeGlobalListener(self._name)

        # Refresh the world/voxel location properties
        self._displayLocationChanged()


    def _overlayOptsChanged(self, *a):

        self._updateReferenceImage()
        self._updateWidgets()
        self._displayLocationChanged()
        

    def _updateReferenceImage(self):
        """Called by the :meth:`_selectedOverlayChanged` method. Looks at the
        currently selected overlay, and figures out if there is a reference
        image that can be used to transform between display, world, and voxel
        coordinate systems.
        """

        refImage = None
        
        # Look at the currently selected overlay, and
        # see if there is an associated NIFTI image
        # that can be used as a reference image
        if len(self._overlayList) > 0:

            overlay  = self._displayCtx.getSelectedOverlay()
            opts     = self._displayCtx.getOpts(overlay)
            refImage = opts.getReferenceImage()

            log.debug('Reference image for overlay {}: {}'.format(
                overlay, refImage))

        self._refImage = refImage

        if refImage is not None:
            opts = self._displayCtx.getOpts(refImage)
            self._voxToDisplayMat   = opts.getTransform('voxel',   'display')
            self._displayToVoxMat   = opts.getTransform('display', 'voxel')
            self._worldToDisplayMat = opts.getTransform('world',   'display')
            self._displayToWorldMat = opts.getTransform('display', 'world')
            self._voxToWorldMat     = opts.getTransform('voxel',   'world')
            self._worldToVoxMat     = opts.getTransform('world',   'voxel')
        else:
            self._voxToDisplayMat   = None
            self._displayToVoxMat   = None
            self._worldToDisplayMat = None
            self._displayToWorldMat = None
            self._voxToWorldMat     = None
            self._worldToVoxMat     = None


    def _updateWidgets(self):

        refImage = self._refImage

        haveRef = refImage is not None

        self.voxelX     .Enable(haveRef)
        self.voxelY     .Enable(haveRef)
        self.voxelZ     .Enable(haveRef)
        self.voxelLabel .Enable(haveRef)

        ######################
        # World location label
        ######################

        label = strings.labels[self, 'worldLocation']
        
        if haveRef: label += strings.anatomy[refImage,
                                             'space',
                                             refImage.getXFormCode()]
        else:       label += strings.labels[ self,
                                             'worldLocation',
                                             'unknown']

        self.worldLabel.SetLabel(label)

        ####################################
        # Voxel/world location widget limits
        ####################################

        # Figure out the limits for the
        # voxel/world location widgets
        if self._refImage is not None:
            shape    = self._refImage.shape[:3]
            vlo      = [0, 0, 0]
            vhi      = np.array(shape) - 1
            wlo, whi = transform.axisBounds(shape, self._voxToWorldMat)
        else:
            vlo     = [0, 0, 0]
            vhi     = [0, 0, 0]
            wbounds = self._displayCtx.bounds[:]
            wlo     = wbounds[0::2]
            whi     = wbounds[1::2]

        # Update the voxel and world location limits,
        # but don't trigger a listener callback, as
        # this would change the display location.
        self.disableNotification('worldLocation')
        self.disableNotification('voxelLocation')

        log.debug('Setting voxelLocation limits: {} - {}'.format(vlo, vhi))
        log.debug('Setting worldLocation limits: {} - {}'.format(wlo, whi))

        for i in range(3):
            self.voxelLocation.setLimits(i, vlo[i], vhi[i])
            self.worldLocation.setLimits(i, wlo[i], whi[i])
            
        self.enableNotification('worldLocation')
        self.enableNotification('voxelLocation')

        ###############
        # Volume widget
        ###############

        # Unbind any listeners between the previous
        # reference image and the volume widget
        if self.volumeTarget is not None:
            props.unbindWidget(self.volume,
                               self.volumeTarget,
                               'volume',
                               (wx.EVT_SPIN, wx.EVT_SPINCTRL))
            
            self.volume.Unbind(wx.EVT_MOUSEWHEEL)
            self.volumeTarget = None
            self.volume.SetValue(0)

        # Enable/disable the volume widget if the
        # overlay is a 4D image, and bind/unbind
        # the widget to the volume property of
        # the associated ImageOpts instance
        if haveRef and refImage.is4DImage():
            opts = self._displayCtx.getOpts(refImage)
            self.volumeTarget = opts

            def onMouse(ev):
                if not self.volume.IsEnabled():
                    return

                wheelDir = ev.GetWheelRotation()

                if   wheelDir < 0: opts.volume -= 1
                elif wheelDir > 0: opts.volume += 1

            props.bindWidget(
                self.volume, opts, 'volume', (wx.EVT_SPIN, wx.EVT_SPINCTRL))

            self.volume.Bind(wx.EVT_MOUSEWHEEL, onMouse)

            self.volume     .Enable()
            self.volumeLabel.Enable()
        else:
            self.volume     .Disable()
            self.volumeLabel.Disable() 

            
    def _prePropagate(self):

        self            .disableNotification('voxelLocation')
        self            .disableNotification('worldLocation')
        self._displayCtx.disableListener(    'location', self._name)

        self.Freeze()

        
    def _propagate(self, source, target, xform):

        if   source == 'display': coords = self._displayCtx.location.xyz
        elif source == 'voxel':   coords = self.voxelLocation.xyz
        elif source == 'world':   coords = self.worldLocation.xyz

        if xform is not None: xformed = transform.transform([coords], xform)[0]
        else:                 xformed = coords

        log.debug('Updating location ({} {} -> {} {})'.format(
            source, coords, target, xformed))

        if   target == 'display': self._displayCtx.location.xyz =   xformed
        elif target == 'voxel':   self.voxelLocation.xyz = np.round(xformed)
        elif target == 'world':   self.worldLocation.xyz =          xformed
        
    
    def _postPropagate(self):
        self            .enableNotification('voxelLocation')
        self            .enableNotification('worldLocation')
        self._displayCtx.enableListener(    'location', self._name)

        self.Thaw()
        self.Refresh()
        self.Update()

    
    def _displayLocationChanged(self, *a):
        """Called when the :attr:`.DisplayContext.location` changes.
        Propagates the change on to the :attr:`voxelLocation`
        and :attr:`worldLocation` properties.
        """

        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('display', 'voxel', self._displayToVoxMat)
        self._propagate('display', 'world', self._displayToWorldMat)
        self._postPropagate()
        self._updateLocationInfo()


    def _worldLocationChanged(self, *a):
        
        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('world', 'voxel',   self._worldToVoxMat)
        self._propagate('world', 'display', self._worldToDisplayMat)
        self._postPropagate()
        self._updateLocationInfo()

        
    def _voxelLocationChanged(self, *a):
        
        if len(self._overlayList) == 0: return

        self._prePropagate()
        self._propagate('voxel', 'world',   self._voxToWorldMat)
        self._propagate('voxel', 'display', self._voxToDisplayMat)
        self._postPropagate()
        self._updateLocationInfo()


    def _updateLocationInfo(self):

        if len(self._overlayList) == 0:
            self.info.SetPage('')
            return
        

        overlays = self._displayCtx.getOrderedOverlays()
        selOvl   = self._displayCtx.getSelectedOverlay()
        
        overlays.remove(selOvl)
        overlays.insert(0, selOvl)

        lines = []
        for overlay in overlays:

            title = '<b>{}</b>'.format(overlay.name)
            info  = None

            if not isinstance(overlay, fslimage.Image):
                info = '{}'.format(strings.labels[self, 'noData'])
            else:
                opts = self._displayCtx.getOpts(overlay)
                vloc = transform.transform(
                    [self._displayCtx.location.xyz],
                    opts.getTransform('display', 'voxel'))[0]

                # The above transformation gives us
                # values between [x - 0.5, x + 0.5]
                # for voxel x, so we need to round
                # to the nearest integer to get the
                # corresponding voxel coordinates
                vloc = tuple(map(int, np.round(vloc)))

                if overlay.is4DImage():
                    vloc = vloc + (opts.volume,)

                inBounds = True
                for i in range(3):
                    if vloc[i] < 0 or vloc[i] >= overlay.shape[i]:
                        inBounds = False

                if inBounds:
                    vval = overlay.data[vloc]
                    info = '[{}]: {}'.format(' '.join(map(str, vloc)), vval)
                else:
                    info = strings.labels[self, 'outOfBounds']

            lines.append(title)
            if info is not None:
                lines.append(info)

            self.info.SetPage('<br>'.join(lines))
            self.info.Refresh()
