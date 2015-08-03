#!/usr/bin/env python
#
# overlayinfopanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import collections

import wx
import wx.html as wxhtml

import fsl.data.strings  as strings
import fsl.fslview.panel as fslpanel


class OverlayInfo(object):
    """A little class which encapsulates human-readable information about
    one overlay. ``OverlayInfo`` objects are created and returned by the
    ``OverlayInfoPanel.__get*Info`` methods.
    """

    def __init__(self, title):
        
        self.title    = title
        self.info     = []
        self.sections = collections.OrderedDict()

        
    def addSection(self, section):
        self.sections[section] = []

        
    def addInfo(self, name, info, section=None):
        if section is None: self.info             .append((name, info))
        else:               self.sections[section].append((name, info))
        


class OverlayInfoPanel(fslpanel.FSLViewPanel):


    def __init__(self, parent, overlayList, displayCtx):

        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__info  = wxhtml.HtmlWindow(self)
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__info, flag=wx.EXPAND, proportion=1)
        
        self.SetSizer(self.__sizer)

        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)
        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__currentOverlay = None
        self.__currentDisplay = None
        self.__selectedOverlayChanged()
        self.Layout()

    def destroy(self):
        self._displayCtx .removeListener('selectedOverlay', self._name)
        self._overlayList.removeListener('overlays',        self._name)

        if self.__currentDisplay is not None:
            self.__currentDisplay.removeListener('name', self._name)

        self.__currentOverlay = None
        self.__currentDisplay = None

        fslpanel.FSLViewPanel.destroy(self)


    def __selectedOverlayChanged(self, *a):

        overlay = self._displayCtx.getSelectedOverlay()

        if overlay == self.__currentOverlay:
            return
        
        if self.__currentDisplay is not None:
            self.__currentDisplay.removeListener('name', self._name)
            
        self.__currenOverlay = None
        self.__currenDisplay = None
        
        if overlay is not None:
            self.__currentOverlay = overlay
            self.__currentDisplay = self._displayCtx.getDisplay(overlay)

            self.__currentDisplay.addListener('name',
                                              self._name,
                                              self.__overlayNameChanged)
        
        self.__updateInformation()

        
    def __overlayNameChanged(self, *a):
        self.__updateInformation()


    def __updateInformation(self):

        overlay  = self.__currentOverlay
        display  = self.__currentDisplay
        infoFunc = '_{}__get{}Info'.format(type(self)   .__name__,
                                           type(overlay).__name__)
        infoFunc = getattr(self, infoFunc, None)
        
        if infoFunc is None:
            self.__info.SetPage('')
            return

        info = infoFunc(overlay, display)

        self.__info.SetPage(self.__formatOverlayInfo(info))


    def __formatOverlayInfo(self, info):
        lines  = [info.title]
        lines += map(str, info.info)

        for sec in info.sections.keys():
            lines += [sec]
            lines += map(str, info.sections[sec])
        
        return '<br>'.join(lines)


    def __getImageInfo(self, overlay, display):
        
        info = OverlayInfo(display.name)
        img  = overlay.nibImage
        hdr  = img.get_header()

        voxUnits, timeUnits = hdr.get_xyzt_units()
        
        dimSect    = strings.labels[self, overlay, 'dimensions']
        xformSect  = strings.labels[self, overlay, 'transform']
        orientSect = strings.labels[self, overlay, 'orient']

        info.addSection(dimSect)
        info.addSection(xformSect)
        info.addSection(orientSect)

        info.addInfo(strings.nifti['dataSource'], overlay.dataSource)
        info.addInfo(strings.nifti['datatype'],
                     strings.nifti['datatype', int(hdr['datatype'])])
        info.addInfo(strings.nifti['descrip'], hdr['descrip'])

        info.addInfo(strings.nifti['vox_units'],  voxUnits,  section=dimSect)
        info.addInfo(strings.nifti['time_units'], timeUnits, section=dimSect)
        
        info.addInfo(strings.nifti['dimensions'],
                     '{}D'.format(len(overlay.shape)),
                     section=dimSect)

        for i in range(len(overlay.shape)):
            info.addInfo(strings.nifti['dim{}'.format(i + 1)],
                         str(overlay.shape[i]),
                         section=dimSect)

        for i in range(len(overlay.shape)):
            
            pixdim = hdr['pixdim'][i + 1]

            if   i  < 3: pixdim = '{} {}'.format(pixdim, voxUnits)
            elif i == 3: pixdim = '{} {}'.format(pixdim, timeUnits)
                
            info.addInfo(
                strings.nifti['pixdim{}'.format(i + 1)],
                pixdim,
                section=dimSect)

        info.addInfo(strings.nifti['qform_code'],
                     strings.anatomy['Image', 'space', int(hdr['qform_code'])],
                     section=xformSect)
        info.addInfo(strings.nifti['sform_code'],
                     strings.anatomy['Image', 'space', int(hdr['sform_code'])],
                     section=xformSect)

        # TODO matrix formatting (you'll need to use
        #      HTML, or maybe get the formatOverlayInfo
        #      method to support different types)
        info.addInfo(strings.nifti['qform'],
                     str(img.get_qform()),
                     section=xformSect)
        info.addInfo(strings.nifti['sform'],
                     str(img.get_sform()),
                     section=xformSect) 

        for i in range(3):
            orient = overlay.getVoxelOrientation(i)
            orient = '{} - {}'.format(
                strings.anatomy['Image', 'lowlong',  orient],
                strings.anatomy['Image', 'highlong', orient])
            info.addInfo(strings.nifti['voxOrient.{}'.format(i)],
                         orient,
                         section=orientSect)

        for i in range(3):
            orient = overlay.getWorldOrientation(i, code='sform')
            orient = '{} - {}'.format(
                strings.anatomy['Image', 'lowlong',  orient],
                strings.anatomy['Image', 'highlong', orient])
            info.addInfo(strings.nifti['sformOrient.{}'.format(i)],
                         orient,
                         section=orientSect)

        for i in range(3):
            orient = overlay.getWorldOrientation(i, code='qform')
            orient = '{} - {}'.format(
                strings.anatomy['Image', 'lowlong',  orient],
                strings.anatomy['Image', 'highlong', orient])
            info.addInfo(strings.nifti['qformOrient.{}'.format(i)],
                         orient,
                         section=orientSect) 

        return info


    def __getFEATImageInfo(self, overlay, display):
        return self.__getImageInfo(overlay)

    
    def __getModelInfo(self, overlay, display):
        info = OverlayInfo(display.name)

        return info
