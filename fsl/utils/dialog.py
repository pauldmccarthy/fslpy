#!/usr/bin/env python
#
# dialog.py - Miscellaneous dialogs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import threading

import fsl.data.strings as strings


SMD_KEEP_CENTERED = 1


class SimpleMessageDialog(wx.Dialog):

    
    def __init__(self, parent=None, message='', style=None):
        """
        Style defaults to SMD_KEEP_CENTERED.
        """

        
        if style is None:
            style = SMD_KEEP_CENTERED

        if parent is None:
            parent = wx.GetApp().GetTopWindow()

        wx.Dialog.__init__(self,
                           parent,
                           style=wx.STAY_ON_TOP | wx.FULL_REPAINT_ON_RESIZE)

        
        self.__style = style
        
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

        self.SetTransparent(240)
        self.SetBackgroundColour((225, 225, 200))
        
        self.SetSizer(self.__sizer)

        self.SetMessage(message)

        
    def SetMessage(self, msg):

        msg = str(msg)

        self.__message.SetLabel(msg)

        # Figure out the dialog size
        # required to fit the message
        dc = wx.ClientDC(self.__message)
        
        width, height = dc.GetTextExtent(msg)

        # +50 to account for sizer borders (see __init__),
        # plus a bit more for good measure. In particular,
        # under GTK, the message seems to be vertically
        # truncated if we don't add some extra padding
        width  += 60
        height += 70

        self.SetMinClientSize((width, height))
        self.SetClientSize((   width, height))

        self.Layout()

        if self.__style & SMD_KEEP_CENTERED:
            self.CentreOnParent()

        self.Refresh()
        self.Update()
        wx.Yield()
            


class TimeoutDialog(SimpleMessageDialog):


    def __init__(self, parent, message, timeout=1000, **kwargs):

        SimpleMessageDialog.__init__(self, parent, message, **kwargs)
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

        self.task    = task
        self.args    = args
        self.kwargs  = kwargs
        self.message = message

        style = kwargs.pop('style', None)

        SimpleMessageDialog.__init__(self, parent, style=style)


    def Run(self, mainThread=False):
        """

        If mainThread=True, the task should call wx.Yield periodically
        (under GTK, there is a chance that the ProcessingDialog will not
        get drawn before the task begins).
        """

        self.SetMessage(self.message)
        self.Show()
        self.SetFocus()

        self.Refresh()
        self.Update()
        wx.Yield()

        disable = wx.WindowDisabler(self)

        if mainThread:
            try:
                result = self.task(*self.args, **self.kwargs)
            except:
                self.Close()
                self.Destroy()
                del disable
                raise
        else:
            returnVal = [None]

            def wrappedTask():
                returnVal[0] = self.task(*self.args, **self.kwargs)

            thread = threading.Thread(target=wrappedTask)
            thread.start()

            while thread.isAlive():
                thread.join(0.2)
                wx.Yield()

            result = returnVal[0]

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
            td = TimeoutDialog(self, 'Copied!', 1000)
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
