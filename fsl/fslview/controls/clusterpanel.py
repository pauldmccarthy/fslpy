#!/usr/bin/env python
#
# clusterpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import                        logging
import                        wx

import pwidgets.widgetgrid as widgetgrid

import fsl.fslview.panel   as fslpanel
import fsl.utils.transform as transform
import fsl.data.strings    as strings
import fsl.data.featimage  as featimage


log = logging.getLogger(__name__)


class ClusterPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx):
        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))

        self.__overlayName    = wx    .StaticText(    self)
        self.__addZStats      = wx.Button(            self)
        self.__addClusterMask = wx.Button(            self)
        self.__statSelect     = wx    .ComboBox(      self,
                                                      style=wx.CB_READONLY)
        self.__clusterList    = widgetgrid.WidgetGrid(self)

        self.__addZStats     .SetLabel(strings.labels[self, 'addZStats'])
        self.__addClusterMask.SetLabel(strings.labels[self, 'addClusterMask'])
        
        self.__clusterList.ShowRowLabels(False)
        self.__clusterList.ShowColLabels(True)
        
        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__topSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__mainSizer = wx.BoxSizer(wx.VERTICAL)

        args = {'flag' : wx.EXPAND, 'proportion' : 1}
 
        self.__topSizer.Add(self.__overlayName,    **args)
        self.__topSizer.Add(self.__statSelect,     **args)
        self.__topSizer.Add(self.__addZStats,      **args)
        self.__topSizer.Add(self.__addClusterMask, **args)

        self.__mainSizer.Add(self.__topSizer,    flag=wx.EXPAND)
        self.__mainSizer.Add(self.__clusterList, **args)

        # Only one of the disabledText or
        # mainSizer are shown at any one time
        self.__sizer.Add(self.__disabledText, **args)
        self.__sizer.Add(self.__mainSizer,    **args)

        overlayList.addListener('overlays',
                                self._name,
                                self.__overlayListChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__statSelect    .Bind(wx.EVT_COMBOBOX, self.__statSelected)
        self.__addZStats     .Bind(wx.EVT_BUTTON,   self.__addZStatsClick)
        self.__addClusterMask.Bind(wx.EVT_BUTTON,   self.__addClusterMaskClick)

        self.__selectedOverlay = None
        self.__selectedOverlayChanged()


    def destroy(self):
        self._overlayList.removeListener('overlays',        self._name)
        self._displayCtx .removeListener('selectedOverlay', self ._name)
        fslpanel.FSLViewPanel.destroy(self)

        
    def __disable(self, message):

        self.__disabledText.SetLabel(message)
        self.__sizer.Show(self.__disabledText, True)
        self.__sizer.Show(self.__mainSizer,    False)
        self.Layout()


    def __addZStatsClick(self, ev):

        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()
        zstats   = overlay.getZStats(contrast)

        for ol in self._overlayList:
            
            # Already in overlay list
            if ol.dataSource == zstats.dataSource:
                return

        log.debug('Adding Z-statistic {} to overlay list'.format(zstats.name))
        self._overlayList.append(zstats)

        opts   = self._displayCtx.getOpts(zstats)
        zthres = float(overlay.thresholds()['z'])

        # Set some display parameters if
        # we have a z value threshold
        if zthres is not None:

            absmax = max(map(abs, (opts.dataMin, opts.dataMax)))
            
            opts.cmap            = 'Render3'
            opts.invertClipping  = True 
            opts.displayRange.x  = -absmax, absmax
            opts.clippingRange.x = -zthres, zthres

    
    def __addClusterMaskClick(self, ev):
        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()
        mask     = overlay.getClusterMask(contrast)

        for ol in self._overlayList:
            
            # Already in overlay list
            if ol.dataSource == mask.dataSource:
                return

        log.debug('Adding cluster mask {} to overlay list'.format(mask.name))
        self._overlayList.append(mask)
        self._displayCtx.getDisplay(mask).overlayType = 'label'


    def __overlayListChanged(self, *a):
        self.__selectedOverlayChanged()
        self.__enableOverlayButtons()


    def __enableOverlayButtons(self):
        
        if self.__selectedOverlay is None:
            return

        overlay  = self.__selectedOverlay
        contrast = self.__statSelect.GetSelection()

        zstat     = overlay.getZStats(     contrast)
        clustMask = overlay.getClusterMask(contrast)

        dss = [ovl.dataSource for ovl in self._overlayList]

        self.__addZStats     .Enable(zstat    .dataSource not in dss)
        self.__addClusterMask.Enable(clustMask.dataSource not in dss)
        
    
    def __selectedOverlayChanged(self, *a):

        prevOverlay            = self.__selectedOverlay
        self.__selectedOverlay = None
        
        # No overlays are loaded
        if len(self._overlayList) == 0:
            self.__disable(strings.messages[self, 'noOverlays'])
            return

        overlay = self._displayCtx.getSelectedOverlay()
        
        # Not a FEAT image, can't 
        # do anything with that
        if not isinstance(overlay, featimage.FEATImage):
            self.__disable(strings.messages[self, 'notFEAT'])
            return

        # Selected overlay is either the
        # same one (maybe the overlay list,
        # rather than the selected overlay,
        # changed) or the newly selected
        # overlay is from the same FEAT
        # analysis. No need to do anything.
        if prevOverlay is not None and (prevOverlay is overlay or 
           prevOverlay.getFEATDir() == overlay.getFEATDir()):
            self.__selectedOverlay = overlay
            return
            
        self.__statSelect .Clear()
        self.__clusterList.ClearGrid()

        self.__selectedOverlay = overlay

        self.__sizer.Show(self.__disabledText, False)
        self.__sizer.Show(self.__mainSizer,    True)

        numCons  = overlay.numContrasts()
        conNames = overlay.contrastNames()

        try:
            # clusts is a list of (contrast, clusterList) tuples 
            clusts = [(c, overlay.clusterResults(c)) for c in range(numCons)]
            clusts = filter(lambda (con, clust): clust is not None, clusts)

        # Error parsing the cluster data
        except Exception as e:
            log.warning('Error parsing cluster data for '
                        '{}: {}'.format(overlay.name, str(e)), exc_info=True)
            self.__disable(strings.messages[self, 'badData'])
            return

        # No cluster results exist
        # for any contrast
        if len(clusts) == 0:
            self.__disable(strings.messages[self, 'noClusters'])
            return

        for contrast, clusterList in clusts:
            name = conNames[contrast]
            name = strings.labels[self, 'clustName'].format(contrast + 1, name)

            self.__statSelect.Append(name, clusterList)
            
        self.__overlayName.SetLabel(overlay.getAnalysisName())

        self.__statSelect.SetSelection(0)
        self.__displayClusterData(clusts[0][1])

        self.Layout()
        return

    
    def __statSelected(self, ev):
        idx  = self.__statSelect.GetSelection()
        data = self.__statSelect.GetClientData(idx)
        self.__displayClusterData(data)
        self.__enableOverlayButtons()

        
    def __displayClusterData(self, clusters):

        cols = {'index'         : 0,
                'nvoxels'       : 1,
                'p'             : 2,
                'logp'          : 3,
                'zmax'          : 4,
                'zmaxcoords'    : 5,
                'zcogcoords'    : 6,
                'copemax'       : 7,
                'copemaxcoords' : 8,
                'copemean'      : 9}

        grid    = self.__clusterList
        overlay = self.__selectedOverlay
        opts    = self._displayCtx.getOpts(overlay)

        grid.ClearGrid()
        grid.SetGridSize(len(clusters), 10)

        for col, i in cols.items():
            grid.SetColLabel(i, strings.labels[self, col])

        def makeCoordButton(coords):

            label = wx.StaticText(grid, label='[{} {} {}]'.format(*coords))
            btn   = wx.Button(grid, label=u'\u2192', style=wx.BU_EXACTFIT)
            
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(label, flag=wx.EXPAND, proportion=1)
            sizer.Add(btn)

            def onClick(ev):
                xfm  = opts.getTransform('voxel', 'display')
                dloc = transform.transform([coords], xfm)[0]
                self._displayCtx.location = dloc

            btn.Bind(wx.EVT_BUTTON, onClick)

            return sizer

        for i, clust in enumerate(clusters):

            zmaxbtn    = makeCoordButton((clust.zmaxx,
                                          clust.zmaxy,
                                          clust.zmaxz))
            zcogbtn    = makeCoordButton((clust.zcogx,
                                          clust.zcogy,
                                          clust.zcogz))
            copemaxbtn = makeCoordButton((clust.copemaxx,
                                          clust.copemaxy,
                                          clust.copemaxz))

            fmt = lambda v: '{}'.format(v)
            grid.SetText(  i, cols['index'],         fmt(clust.index))
            grid.SetText(  i, cols['nvoxels'],       fmt(clust.nvoxels))
            grid.SetText(  i, cols['p'],             fmt(clust.p))
            grid.SetText(  i, cols['logp'],          fmt(clust.logp))
            grid.SetText(  i, cols['zmax'],          fmt(clust.zmax))
            grid.SetWidget(i, cols['zmaxcoords'],    zmaxbtn)
            grid.SetWidget(i, cols['zcogcoords'],    zcogbtn)
            grid.SetText(  i, cols['copemax'],       fmt(clust.copemax))
            grid.SetWidget(i, cols['copemaxcoords'], copemaxbtn)
            grid.SetText(  i, cols['copemean'],      fmt(clust.copemean))
