#!/usr/bin/env python
#
# clusterpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.fslview.panel   as fslpanel
import fsl.data.strings    as strings
import fsl.data.featimage  as featimage


class ClusterPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx):
        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        self.__disabledText = wx.StaticText(
            self,
            style=(wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)

        self.__sizer.Add(self.__disabledText, flag=wx.EXPAND, proportion=1)

        overlayList.addListener('overlays',
                                self._name,
                                self.__selectedOverlayChanged)
        displayCtx .addListener('selectedOverlay',
                                self._name,
                                self.__selectedOverlayChanged)

        self.__selectedOverlayChanged()
        

    def __selectedOverlayChanged(self, *a):

        if len(self._overlayList) == 0:
            # hide other things
            self.__sizer.Show(self.__disabledText, False)
            self.Layout()
            return

        overlay = self._displayCtx.getSelectedOverlay()
        
        if not isinstance(overlay, featimage.FEATImage):

            self.__disabledText.SetLabel(
                strings.messages[self, 'notFEAT'])

            # hide other things
            self.__sizer.Show(self.__disabledText)
            self.Layout()
            return


        self.__sizer.Show(self.__disabledText, False)
        self.Layout()
        return
