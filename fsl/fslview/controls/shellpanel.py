#!/usr/bin/env python
#
# shellpanel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import wx.py.shell as wxshell

import fsl.fslview.panel as fslpanel


class ShellPanel(fslpanel.FSLViewPanel):

    def __init__(self, parent, overlayList, displayCtx, sceneOpts):
        fslpanel.FSLViewPanel.__init__(self, parent, overlayList, displayCtx)

        lcls = {
            'displayCtx'  : displayCtx,
            'overlayList' : overlayList,
            'sceneOpts'   : sceneOpts,
        }

        shell = wxshell.Shell(
            self,
            introText='\nFSLEyes python shell\n'
                      'Available variables are:\n'
                      '  - overlayList\n' 
                      '  - displayCtx\n'
                      '  - sceneOpts\n\n',
            locals=lcls)

        font = shell.GetFont()

        shell.SetFont(font.Larger())
        
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        sizer.Add(shell, flag=wx.EXPAND, proportion=1)


    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
