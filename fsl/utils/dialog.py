#!/usr/bin/env python
#
# dialog.py - Miscellaneous dialogs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.data.strings as strings


class SimpleMessageDialog(wx.Dialog):

    
    def __init__(self, parent=None, message=''):

        wx.Dialog.__init__(self, parent, style=wx.STAY_ON_TOP)
        
        self.__message = wx.StaticText(
            self,
            style=(wx.ST_ELLIPSIZE_MIDDLE     |
                   wx.ALIGN_CENTRE_HORIZONTAL |
                   wx.ALIGN_CENTRE_VERTICAL))
        
        self.__sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__sizer.Add(self.__message,
                         border=25,
                         proportion=1,
                         flag=wx.CENTRE | wx.ALL)

        self.SetBackgroundColour((225, 225, 200))
        
        self.SetSizer(self.__sizer)
        self.SetMessage(message)

        
    def SetMessage(self, msg):

        msg = str(msg)
        
        self.__message.SetLabel(msg)

        # Figure out the dialog size
        # required to fit the message
        dc = wx.ClientDC(self.__message)
        
        defWidth, defHeight = 25, 25
        msgWidth, msgHeight = dc.GetTextExtent(msg)

        if msgWidth  > defWidth:  width  = msgWidth  + 25
        else:                     width  = defWidth
        
        if msgHeight > defHeight: height = msgHeight + 25
        else:                     height = defHeight

        self.__message.SetMinSize((width, height))

        self.Fit()
        self.Refresh()
        self.Update()


class TimeoutDialog(SimpleMessageDialog):


    def __init__(self, parent, message, timeout=1000):

        SimpleMessageDialog.__init__(self, parent, message)
        self.__timeout = timeout


    def __close(self):
        self.Close()
        self.Destroy()

        
    def Show(self):
        wx.CallLater(self.__timeout, self.__close)
        SimpleMessageDialog.Show(self)


    def ShowModal(self):
        wx.CallLater(self.__timeout, self.__close)
        SimpleMessageDialog.ShowModal(self)

        
class ProcessingDialog(SimpleMessageDialog):

    def __init__(self, parent, message, task, *args, **kwargs):
        """
        
        :arg message:
        
        :arg task:

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
        
        SimpleMessageDialog.__init__(self, parent, message)


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

        
    def __defaultMessageFunc(self, msg):
        self.SetMessage(msg)

    
    def __defaultErrorFunc(self, msg, err):
        err   = str(err)
        msg   = strings.messages[self, 'error'].format(msg, err)
        title = strings.titles[  self, 'error']
        wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 



TED_READONLY  = 1
TED_MULTILINE = 2
TED_OK        = 4
TED_CANCEL    = 8
TED_OK_CANCEL = 12
TED_COPY      = 16


class TextEditDialog(wx.Dialog):
    """A dialog which shows an editable/selectable text field."""

    def __init__(self,
                 parent,
                 title='',
                 message='',
                 text='',
                 icon=None,
                 style=TED_OK):

        wx.Dialog.__init__(self,
                           parent,
                           title=title,
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        textStyle = 0
        if style & TED_READONLY:  textStyle |= wx.TE_READONLY
        if style & TED_MULTILINE: textStyle |= wx.TE_MULTILINE

        self.__message  = wx.StaticText(self)
        self.__textEdit = wx.TextCtrl(  self, style=textStyle)

        self.__message .SetLabel(message)
        self.__textEdit.SetValue(text)

        # set the min size of the text 
        # ctrl so it can fit a few lines
        self.__textEdit.SetMinSize((-1, 120))

        self.__ok     = (-1, -1)
        self.__copy   = (-1, -1)
        self.__cancel = (-1, -1)
        self.__icon   = (-1, -1)

        if icon is not None:
            
            icon = wx.ArtProvider.GetMessageBoxIcon(icon)
            bmp  = wx.EmptyBitmap(icon.GetWidth(), icon.GetHeight())
            bmp.CopyFromIcon(icon)
            self.__icon = wx.StaticBitmap(self)
            self.__icon.SetBitmap(bmp)

        if style & TED_OK:
            self.__ok = wx.Button(self, id=wx.ID_OK)
            self.__ok.Bind(wx.EVT_BUTTON, self.__onOk)
            
        if style & TED_CANCEL:
            self.__cancel = wx.Button(self, id=wx.ID_CANCEL)
            self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)

        if style & TED_COPY:
            self.__copy = wx.Button(self, label='Copy to clipboard')
            self.__copy.Bind(wx.EVT_BUTTON, self.__onCopy) 

        textSizer = wx.BoxSizer(wx.VERTICAL)
        iconSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer  = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        textSizer.Add(self.__message,
                      flag=wx.ALL | wx.CENTRE,
                      border=20)
        textSizer.Add(self.__textEdit,
                      flag=wx.ALL | wx.EXPAND,
                      border=20,
                      proportion=1)

        iconSizer.Add(self.__icon, flag=wx.ALL | wx.CENTRE, border=20)
        iconSizer.Add(textSizer, flag=wx.EXPAND, proportion=1)

        btnSizer.AddStretchSpacer()
        btnSizer.Add(self.__ok,
                     flag=wx.ALL | wx.CENTRE,
                     border=10)
        btnSizer.Add(self.__copy,
                     flag=wx.ALL | wx.CENTRE,
                     border=10) 
        btnSizer.Add(self.__cancel,
                     flag=wx.ALL | wx.CENTRE,
                     border=10)
        btnSizer.Add((-1, 20))

        mainSizer.Add(iconSizer, flag=wx.EXPAND, proportion=1)
        mainSizer.Add(btnSizer,  flag=wx.EXPAND)

        self.SetSizer(mainSizer)
        self.Fit()

        
    def __onOk(self, ev):
        self.EndModal(wx.ID_OK)

        
    def __onCancel(self, ev):
        self.EndModal(wx.ID_CANCEL)

        
    def __onCopy(self, ev):
        text = self.__textEdit.GetValue()

        cb = wx.TheClipboard

        if cb.Open():
            cb.SetData(wx.TextDataObject(text))
            cb.Close()
            td = TimeoutDialog(self, 'Copied!')
            td.CentreOnParent()
            td.Show()

            
    def SetMessage(self, message):
        self.__message.SetLabel(message)

        
    def SetOkLabel(self, label):
        self.__ok.SetLabel(label)

    def SetCopyLabel(self, label):
        self.__copy.SetLabel(label)

        
    def SetCancelLabel(self, label):
        self.__cancel.SetLabel(label)


    def SetText(self, text):
        self.__textEdit.SetValue(text)


    def GetText(self):
        return self.__textEdit.GetValue()
