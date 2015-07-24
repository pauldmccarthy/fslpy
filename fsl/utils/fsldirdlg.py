#!/usr/bin/env python
#
# fsldirdlg.py 
# 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
This module defines a dialog which can be used, when the ``$FSLDIR``
environment variable is not set, to prompt the user to identify the
FSL installation location.
"""


import wx

import fsl.data.strings as strings


class FSLDirDialog(wx.Dialog):

    def __init__(self, parent, toolName):

        wx.Dialog.__init__(self, parent, title=strings.titles[self])

        self.__fsldir  = None
        self.__icon    = wx.StaticBitmap(self)
        self.__message = wx.StaticText(  self, style=wx.ALIGN_CENTRE)
        self.__locate  = wx.Button(      self, id=wx.ID_OK)
        self.__skip    = wx.Button(      self, id=wx.ID_CANCEL)

        icon = wx.ArtProvider.GetMessageBoxIcon(wx.ICON_EXCLAMATION)
        bmp  = wx.EmptyBitmap(icon.GetWidth(), icon.GetHeight())
        bmp.CopyFromIcon(icon)

        self.__icon.SetBitmap(bmp)
        self.__message.SetLabel(
            strings.messages[self, 'FSLDirNotSet'].format(toolName))
        self.__locate .SetLabel(strings.labels[self, 'locate'])
        self.__skip   .SetLabel(strings.labels[self, 'skip'])

        self.__skip  .Bind(wx.EVT_BUTTON, self.__onSkip)
        self.__locate.Bind(wx.EVT_BUTTON, self.__onLocate)

        self.__sizer       = wx.BoxSizer(wx.VERTICAL)
        self.__labelSizer  = wx.BoxSizer(wx.HORIZONTAL)
        self.__buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__labelSizer.Add(self.__icon, flag=wx.ALL | wx.CENTRE,
                              border=20)
        self.__labelSizer.Add(self.__message,
                              flag=wx.ALL | wx.CENTRE,
                              proportion=1,
                              border=20)

        self.__buttonSizer.AddStretchSpacer()
        self.__buttonSizer.Add(self.__locate,
                               flag=wx.ALL | wx.CENTRE,
                               border=10,
                               proportion=1)
        self.__buttonSizer.Add(self.__skip,
                               flag=wx.ALL | wx.CENTRE,
                               border=10,
                               proportion=1)
        self.__buttonSizer.Add((20, -1))

        self.__sizer.Add(self.__labelSizer,  flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__buttonSizer, flag=wx.EXPAND)
        self.__sizer.Add((-1, 20))

        self.SetSizer(self.__sizer)
        self.Fit()

        
    def GetFSLDir(self):
        return self.__fsldir
 

    def __onSkip(self, ev):
        self.EndModal(wx.ID_CANCEL)


    def __onLocate(self, ev):

        dlg = wx.DirDialog(
            self,
            message=strings.messages[self, 'selectFSLDir'],
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() != wx.ID_OK:
            self.EndModal(wx.ID_CANCEL)

        self.__fsldir = dlg.GetPath()
 
        self.EndModal(wx.ID_OK)
