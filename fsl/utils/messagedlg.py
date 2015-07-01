#!/usr/bin/env python
#
# messagedlg.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.data.strings as strings


class ProcessingDialog(wx.Dialog):

    def __init__(self, task, message, *args, **kwargs):
        """
        :arg task:
        
        :arg message:
        

        :arg passFuncs:

        :arg messageFunc:

        :arg errorFunc:
        """

        passFuncs = kwargs.get('passFuncs', False)
        
        if not passFuncs:
            kwargs.pop('messageFunc', None)
            kwargs.pop('errorFunc',   None)
        else:
            kwargs['messageFunc'] = kwargs.get('messageFunc',
                                               self.__defaultMessageFunc)
            kwargs['errortFunc']  = kwargs.get('errorFunc',
                                               self.__defaultErrorFunc)

        self.task   = task
        self.args   = args
        self.kwargs = kwargs
        
        wx.Dialog.__init__(
            self, wx.GetApp().GetTopWindow(),
            style=wx.STAY_ON_TOP)
        
        self.message = wx.StaticText(self, style=wx.ST_ELLIPSIZE_MIDDLE)
        
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.message,
                       border=25,
                       proportion=1,
                       flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTRE)
        
        self.SetSizer(self.sizer)
        self.SetSize((400, 100))
        self.SetMessage(message)


    def Run(self):

        disable = wx.WindowDisabler()

        self.CentreOnParent()
        self.Show()
        self.SetFocus()
        self.Update()

        result  = self.task(*self.args, **self.kwargs)
        
        self.Close()
        self.Destroy()

        del disable
        
        return result


    def SetMessage(self, msg):
        self.message.SetLabel(str(msg))
        self.Layout()
        self.Refresh()
        self.Update()

        
    def __defaultMessageFunc(self, msg):
        self.SetMessage(msg)

    
    def __defaultErrorFunc(self, msg, err):
        err   = str(err)
        msg   = strings.messages[self, 'error'].format(msg, err)
        title = strings.titles[  self, 'error']
        wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 
