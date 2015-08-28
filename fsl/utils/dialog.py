#!/usr/bin/env python
#
# dialog.py - Miscellaneous dialogs.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a collection of basic dialog classes, available for
use throughout ``fslpy``. The available dialogs are:

.. autosummary::
   :nosignatures:

   SimpleMessageDialog
   TimeoutDialog
   ProcessingDialog
   TextEditDialog
   FSLDirDialog
"""


import threading

import wx

import fsl.data.strings as strings


class SimpleMessageDialog(wx.Dialog):
    """A simple, no-frills :class:`wx.Dialog` for displaying a message. The
    message can be updated via the :meth:`SetMessage` method. As a simple
    usage example::

        import fsl.utils.dialog as fsldlg
        dlg = fsldlg.SimpleMessageDialog(message='Loading data ...')

        dlg.Show()
    
        # load the data, like
        # you said you would

        # Data is loaded, so we
        # can kill the dialog
        dlg.Close()
        dlg.Destroy()

    
    The ``SimpleMessageDialog`` class supports the following styles:

    .. autosummary::
       SMD_KEEP_CENTERED
    

    a ``SimpleMessageDialog`` looks something like this:

    .. image:: images/simplemessagedialog.png
       :scale: 50%
       :align: center
    """

    
    def __init__(self, parent=None, message='', style=None):
        """Create a ``SimpleMessageDialog``.

        :arg parent:  The :mod:`wx` parent object. 

        :arg message: The initial message to show.

        :arg style:   Only one style flag  is supported,
                      :data:`SMD_KEEP_CENTERED`. This flag is enabled by
                      default.
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
        """Updates the message shown on this ``SimpleMessageDialog``.

        If the :data:`SMD_KEEP_CENTERED` style is set, the dialog is
        re-centered on its parent, to account for changes in the message width.
        """

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
    """A :class:`SimpleMessageDialog` which automatically destroys itself
    after a specified timeout period.

     .. note:: The timeout functionality will not work if you show the dialog
               by any means other than the :meth:`wx.Dialog.Show` or
               :meth:`wx.Dialog.ShowModal` methods ... but is there any other
               way of showing a :class:`wx.Dialog`?
    """


    def __init__(self, parent, message, timeout=1000, **kwargs):
        """Create a ``TimeoutDialog``.

        :arg parent:  The :mod:`wx` parent object.

        :arg message: The initial message to display.

        :arg timeout: Timeout period in milliseconds. 

        :arg kwargs:  Passed through to :meth:`SimpleMessageDialog.__init__`.
        """

        SimpleMessageDialog.__init__(self, parent, message, **kwargs)
        self.__timeout = timeout


    def __close(self):
        """Closes and destroys this ``TimeoutDialog``. """
        self.Close()
        self.Destroy()

        
    def Show(self):
        """Shows this ``TimeoutDialog``, and sets up a callback to
        close it after the specified ``timeout``.
        """
        wx.CallLater(self.__timeout, self.__close)
        SimpleMessageDialog.Show(self)


    def ShowModal(self):
        """Shows this ``TimeoutDialog``, and sets up a callback to
        close it after the specified ``timeout``.
        """ 
        wx.CallLater(self.__timeout, self.__close)
        SimpleMessageDialog.ShowModal(self)

        
class ProcessingDialog(SimpleMessageDialog):
    """A :class:`SimpleMessageDialog` which displays a message and runs a
    task in the background. User interaction is blocked while the task runs,
    and the dialog closes and destroys itself automatically on task
    completion.

    
    The task is simply passed in as a function. If the task supports it,
    the ``ProcessingDialog`` will pass it two message-updating functions,
    which can be used by the task to update the message being displayed.
    This functionality is controlled by the ``passFuncs``, ``messageFunc``
    and ``errorFunc`` parameters to :meth:`__init__`.

    
    A ``ProcessingDialog`` must be displayed via the :meth:`Run` method,
    *not* with the :meth:`wx.Dialog.Show` or :meth:`wx.Dialog.ShowModal`
    methods.
    """

    def __init__(self, parent, message, task, *args, **kwargs):
        """Create a ``ProcessingDialog``.

        :arg parent:       The :mod:`wx` parent object.
        
        :arg message:      Initial message to display.
        
        :arg task:         The function to run.

        :arg args:         Positional arguments passed to the ``task``
                           function.

        :arg kwargs:       Keyword arguments passed to the ``task`` function.

        
        Some special keyword arguments are also accepted:

        ===============  =================================================
        Name             Description
        ===============  =================================================
        ``passFuncs``    If ``True``, two extra keyword arguments  are
                         passed to the ``task`` function - ``messageFunc``
                         and ``errorFunc``.

                         ``messageFunc`` is a function which accepts a
                         single string as its argument; when it is called,
                         the dialog  message is updated to display the
                         string.

                         ``errorFunc`` is a function which accepts two
                         arguemnts - a message string and an
                         :exc:`Exception` instance. If the task detects
                         an error, it may call this function. A new
                         dialog is shown, containing the details of the
                         error, to inform the user.
        ``messageFunc``  Overrides the default ``messageFunc`` described
                         above.
        ``errorFunc``    Overrides the default ``errorFunc`` described
                         above.
        ===============  =================================================
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
        """Shows this ``ProcessingDialog``, and runs the ``task`` function
        passed to :meth:`__init__`. When the task completes, this dialog
        is closed and destroyed.

        :arg mainThread: If ``True`` the task is run in the current thread.
                         Otherwise, the default behaviour is to run the
                         task in a separate thread.

        :returns: the return value of the ``task`` function.

        .. note:: If ``mainThread=True``, the task should call
                  :func:`wx.Yield` periodically - under GTK, there is a
                  chance that this ``ProcessingDialog`` will not get drawn
                  before the task begins.
        """

        self.SetMessage(self.message)
        wx.Dialog.Show(self)
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

    
    def Show(self):
        """Raises a :exc:`NotImplementedError`."""
        raise NotImplementedError('Use the Run method')

    
    def ShowModal(self):
        """Raises a :exc:`NotImplementedError`."""
        raise NotImplementedError('Use the Run method') 

        
    def __defaultMessageFunc(self, msg):
        """Default ``messageFunc``. Updates the message which is displayed
        on this ``ProcessingDialog``. See :meth:`SetMessage`.
        """
        self.SetMessage(msg)

    
    def __defaultErrorFunc(self, msg, err):
        """Default ``errorFunc``. Opens a new dialog (a :class:`wx.MessageBox`)
        which contains a description of the error.
        """
        err   = str(err)
        msg   = strings.messages[self, 'error'].format(msg, err)
        title = strings.titles[  self, 'error']
        wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 


class TextEditDialog(wx.Dialog):
    """A dialog which shows an editable/selectable text field.


    ``TextEditDialog`` supports the following styles:

    .. autosummary::
       TED_READONLY
       TED_MULTILINE
       TED_OK
       TED_CANCEL
       TED_OK_CANCEL
       TED_COPY

    A ``TextEditDialog`` looks something like this:

    .. image:: images/texteditdialog.png
       :scale: 50%
       :align: center
    """

    def __init__(self,
                 parent,
                 title='',
                 message='',
                 text='',
                 icon=None,
                 style=None):
        """Create a ``TextEditDialog``.

        :arg parent:  The :mod:`wx` parent object.

        :arg title:   Dialog title.
        
        :arg message: Dialog message.
        
        :arg text:    String  to display in the text field.
        
        :arg icon:    A :mod:`wx` icon identifier, such as 
                      :data:`wx.ICON_INFORMATION` or :data:`wx.ICON_WARNING`.
        
        :arg style:   A combination of :data:`TED_READONLY`,
                      :data:`TED_MULTILINE`, :data:`TED_OK`, 
                      :data:`TED_CANCEL`, :data:`TED_OK_CANCEL`, and
                      :data:`TED_COPY`. Defaults to :data:`TED_OK`.
        """

        if style is None:
            style = TED_OK

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
        """Called when the *Ok* button is pressed. Ends the dialog. """
        self.EndModal(wx.ID_OK)

        
    def __onCancel(self, ev):
        """Called when the *Cancel* button is pressed. Ends the dialog. """
        self.EndModal(wx.ID_CANCEL)

        
    def __onCopy(self, ev):
        """Called when the *Copy* button is pressed. Copies the text
        to the system clipboard, and pops up a :class:`TimeoutDialog`
        informing the user.
        """
        text = self.__textEdit.GetValue()

        cb = wx.TheClipboard

        if cb.Open():
            cb.SetData(wx.TextDataObject(text))
            cb.Close()
            td = TimeoutDialog(self, 'Copied!', 1000)
            td.Show()

            
    def SetMessage(self, message):
        """Set the message displayed on the dialog."""
        self.__message.SetLabel(message)

        
    def SetOkLabel(self, label):
        """Set the label to show on the *Ok* button."""
        self.__ok.SetLabel(label)

        
    def SetCopyLabel(self, label):
        """Sets the label to show on the *Copy* button."""
        self.__copy.SetLabel(label)

        
    def SetCancelLabel(self, label):
        """Sets the label to show on the *Cancel* button."""
        self.__cancel.SetLabel(label)


    def SetText(self, text):
        """Sets the text to show in the text field."""
        self.__textEdit.SetValue(text)


    def GetText(self):
        """Returns the text shown in the text field."""
        return self.__textEdit.GetValue()


class FSLDirDialog(wx.Dialog):
    """A dialog which warns the user that the ``$FSLDIR`` environment
    variable is not set, and prompts them to identify the FSL
    installation directory.

    If the user selects a directory, the :meth:`getFSLDir` method can be
    called to retrieve their selection after the dialog has been closed.

    A ``FSLDirDialog`` looks something like this:

    .. image:: images/fsldirdialog.png
       :scale: 50%
       :align: center
    """

    def __init__(self, parent, toolName):
        """Create a ``FSLDirDialog``.

        :arg parent:   The :mod:`wx` parent object.

        :arg toolName: The name of the tool which is running.
        """

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

        self.__labelSizer.Add(self.__icon,
                              flag=wx.ALL | wx.CENTRE,
                              border=20)
        self.__labelSizer.Add(self.__message,
                              flag=wx.ALL | wx.CENTRE,
                              proportion=1,
                              border=20)

        self.__buttonSizer.AddStretchSpacer()
        self.__buttonSizer.Add(self.__locate,
                               flag=wx.ALL | wx.CENTRE,
                               border=10)
        self.__buttonSizer.Add(self.__skip,
                               flag=(wx.TOP    |
                                     wx.RIGHT  |
                                     wx.BOTTOM |
                                     wx.CENTRE),
                               border=10)
        self.__buttonSizer.Add((-1, 20))

        self.__sizer.Add(self.__labelSizer,  flag=wx.EXPAND, proportion=1)
        self.__sizer.Add(self.__buttonSizer, flag=wx.EXPAND)

        self.SetSizer(self.__sizer)
        self.Fit()

        
    def GetFSLDir(self):
        """If the user selected a directory, this method returns their
        selection. Otherwise, it returns ``None``.
        """
        return self.__fsldir
 

    def __onSkip(self, ev):
        """Called when the *Skip* button is pushed. """
        self.EndModal(wx.ID_CANCEL)


    def __onLocate(self, ev):
        """Called when the *Locate* button is pushed. Opens a
        :class:`wx.DirDialog` which allows the user to locate the
        FSL installation directory.
        """

        dlg = wx.DirDialog(
            self,
            message=strings.messages[self, 'selectFSLDir'],
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() != wx.ID_OK:
            self.EndModal(wx.ID_CANCEL)
            return

        self.__fsldir = dlg.GetPath()
 
        self.EndModal(wx.ID_OK)


# SimpleMessageDialog style flags
SMD_KEEP_CENTERED = 1
"""If set, the dialog will be re-centred on its parent whenever its message
changes.
"""


# TextEditDialog style flags


TED_READONLY = 1
"""If set, the user will not be able to change the text field contents."""


TED_MULTILINE = 2
"""If set, the text field will span multiple lines. """


TED_OK = 4
"""If set, an *Ok* button will be shown. """


TED_CANCEL = 8
"""If set, a *Cancel* button will be shown. """


TED_OK_CANCEL = 12
"""If set, *Ok* and *Cancel* buttons will be shown. Equivalent to
``TED_OK | TED_CANCEL``.
"""


TED_COPY = 16
"""If set, a *Copy* button will be shown, allowing the use to copy
the text to the system clipboard.
"""
