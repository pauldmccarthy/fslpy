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


import            os
import os.path as op
import            threading

import            six
import            wx

from .platform import platform as fslplatform


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
                         flag=wx.EXPAND | wx.CENTRE | wx.ALL)

        self.SetTransparent(240)
        self.SetBackgroundColour((225, 225, 255))
        
        self.SetSizer(self.__sizer)

        self.SetMessage(message)


    def Show(self):
        """Overrides ``wx.Dialog.Show``. Calls that method, and calls
        ``wx.Yield``.
        """
        wx.Dialog.Show(self)
        wx.Yield()

        
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
        self.__message.Layout()

        if self.__style & SMD_KEEP_CENTERED:
            self.CentreOnParent()

        # This ridiculousness seems to be
        # necessary to force a repaint on
        # all platforms (OSX, GTK, GTK/SSH)
        wx.Yield()
        self.Refresh()
        self.Update()
        self.__message.Refresh()
        self.__message.Update() 
        wx.Yield()


# SimpleMessageDialog style flags
SMD_KEEP_CENTERED = 1
"""If set, the dialog will be re-centred on its parent whenever its message
changes.
"""
            

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

        if mainThread:
            try:
                result = self.task(*self.args, **self.kwargs)
            except:
                self.Close()
                self.Destroy()
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
        msg   = 'An error hass occurred: {}\n\nDetails: {}'.format(msg, err)
        title = 'Error'
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
       TED_COPY_MESSAGE

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
                      :data:`TED_CANCEL`, :data:`TED_OK_CANCEL`, 
                      :data:`TED_COPY` and :data:`TED_COPY_MESSAGE` . Defaults
                      to :data:`TED_OK`.
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

        self.__showCopyMessage = style & TED_COPY_MESSAGE

        # set the min size of the text 
        # ctrl so it can fit a few lines
        self.__textEdit.SetMinSize((-1, 120))

        self.__ok      = (-1, -1)
        self.__copy    = (-1, -1)
        self.__cancel  = (-1, -1)
        self.__icon    = (-1, -1)
        self.__buttons = []

        if icon is not None:
            
            icon = wx.ArtProvider.GetMessageBoxIcon(icon)

            if fslplatform.wxFlavour == fslplatform.WX_PHOENIX:
                bmp = wx.Bitmap()
            else:
                bmp = wx.EmptyBitmap(icon.GetWidth(), icon.GetHeight())
                
            bmp.CopyFromIcon(icon)
            self.__icon = wx.StaticBitmap(self)
            self.__icon.SetBitmap(bmp)

        if style & TED_OK:
            self.__ok = wx.Button(self, id=wx.ID_OK)
            self.__ok.Bind(wx.EVT_BUTTON, self.__onOk)
            self.__buttons.append(self.__ok)
            
        if style & TED_CANCEL:
            self.__cancel = wx.Button(self, id=wx.ID_CANCEL)
            self.__cancel.Bind(wx.EVT_BUTTON, self.__onCancel)
            self.__buttons.append(self.__cancel)

        if style & TED_COPY:
            self.__copy = wx.Button(self, label='Copy to clipboard')
            self.__copy.Bind(wx.EVT_BUTTON, self.__onCopy)
            self.__buttons.append(self.__copy)

        self.__textEdit.Bind(wx.EVT_CHAR_HOOK, self.__onCharHook)

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


    def __onCharHook(self, ev):
        """Called on ``EVT_CHAR_HOOK`` events generated by the ``TextCtrl``.
        Implements tab-navigation, and makes the enter key behave as if
        the user had clicked the OK button.
        """

        key = ev.GetKeyCode()

        if key not in (wx.WXK_TAB, wx.WXK_RETURN):
            ev.Skip()
            return

        # Dodgy, but I've had loads of trouble
        # under OSX - Navigate/HandleAsNavigationKey
        # do not work.
        if key == wx.WXK_TAB and len(self.__buttons) > 0:
            self.__buttons[0].SetFocus()

        elif key == wx.WXK_RETURN:
            self.__onOk(None)

        
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

            if self.__showCopyMessage:
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


TED_COPY_MESSAGE = 32
"""If set, and if :attr:`TED_COPY` is also set, when the user chooses
to copy the text to the system clipboard, a popup message is displayed.
"""


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

        wx.Dialog.__init__(self, parent, title='$FSLDIR is not set')

        self.__fsldir  = None
        self.__icon    = wx.StaticBitmap(self)
        self.__message = wx.StaticText(  self)
        self.__locate  = wx.Button(      self, id=wx.ID_OK)
        self.__skip    = wx.Button(      self, id=wx.ID_CANCEL)

        icon = wx.ArtProvider.GetMessageBoxIcon(wx.ICON_EXCLAMATION)

        if fslplatform.wxFlavour == fslplatform.WX_PYTHON:
            bmp  = wx.EmptyBitmap(icon.GetWidth(), icon.GetHeight())
        else:
            bmp = wx.Bitmap()
            
        bmp.CopyFromIcon(icon)

        self.__icon.SetBitmap(bmp)
        self.__message.SetLabel(
            'The $FSLDIR environment variable is not set - {} '
            'may not behave correctly.'.format(toolName))
        self.__locate .SetLabel('Locate $FSLDIR')
        self.__skip   .SetLabel('Skip')

        self.__skip  .Bind(wx.EVT_BUTTON, self.__onSkip)
        self.__locate.Bind(wx.EVT_BUTTON, self.__onLocate)

        self.__mainSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__contentSizer = wx.BoxSizer(wx.VERTICAL)
        self.__buttonSizer  = wx.BoxSizer(wx.HORIZONTAL)

        self.__buttonSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        self.__buttonSizer.Add(self.__locate)
        self.__buttonSizer.Add((20, 1))
        self.__buttonSizer.Add(self.__skip)

        self.__contentSizer.Add(self.__message, flag=wx.EXPAND, proportion=1)
        self.__contentSizer.Add((1, 20))
        self.__contentSizer.Add(self.__buttonSizer, flag=wx.EXPAND)

        # If running on OSX, add a message
        # telling the user about the
        # cmd+shift+g shortcut
        if fslplatform.os == 'Darwin':

            self.__hint = wx.StaticText(
                self,
                label=six.u('Hint: Press \u2318+\u21e7+G in the file '
                            'dialog to manually type in a location.'))

            self.__hint.SetForegroundColour('#888888')

            self.__contentSizer.Insert(2, self.__hint, flag=wx.EXPAND)
            self.__contentSizer.Insert(3, (1, 20))
            
        else:
            self.__hint = None
            
        self.__mainSizer.Add(self.__icon,
                             flag=wx.ALL | wx.CENTRE,
                             border=20)
        self.__mainSizer.Add(self.__contentSizer,
                             flag=wx.EXPAND | wx.ALL,
                             proportion=1,
                             border=20)

        self.__message.Wrap(self.GetSize().GetWidth())

        self.SetSizer(self.__mainSizer)
        self.__mainSizer.Layout()
        self.__mainSizer.Fit(self)

        self.CentreOnParent()

        
    def GetFSLDir(self):
        """If the user selected a directory, this method returns their
        selection. Otherwise, it returns ``None``.
        """
        return self.__fsldir
 

    def __onSkip(self, ev):
        """called when the *Skip* button is pushed. """
        self.EndModal(wx.ID_CANCEL)


    def __onLocate(self, ev):
        """Called when the *Locate* button is pushed. Opens a
        :class:`wx.DirDialog` which allows the user to locate the
        FSL installation directory.
        """

        dlg = wx.DirDialog(
            self,
            message='Select the directory in which FSL is installed',
            defaultPath=op.join(os.sep, 'usr', 'local'),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)

        # If the user cancels the file
        # dialog, focus returns to the
        # original 'Choose dir' / 'Skip'
        # dialog.
        if dlg.ShowModal() != wx.ID_OK:
            return

        self.__fsldir = dlg.GetPath()
 
        self.EndModal(wx.ID_OK)


class CheckBoxMessageDialog(wx.Dialog):
    """A ``wx.Dialog`` which displays a message, one or more ``wx.CheckBox``
    widgets, with associated messages, an *Ok* button, and (optionally) a
    *Cancel* button.
    """

    
    def __init__(self,
                 parent,
                 title=None,
                 message=None,
                 cbMessages=None,
                 cbStates=None,
                 yesText=None,
                 noText=None,
                 cancelText=None,
                 hintText=None,
                 focus=None,
                 icon=None,
                 style=None):
        """Create a ``CheckBoxMessageDialog``.

        :arg parent:        A ``wx`` parent object.
        
        :arg title:         The dialog frame title.
        
        :arg message:       Message to show on the dialog.
        
        :arg cbMessages:    A list of labels, one for each ``wx.CheckBox``.
        
        :arg cbStates:      A list of initial states (boolean values) for
                            each ``wx.CheckBox``.
        
        :arg yesText:       Text to show on the *yes*/confirm button. Defaults 
                            to *OK*.

        :arg noText:        Text to show on the *no* button. If not provided,
                            there will be no *no* button.

        :arg cancelText:    Text to show on the *cancel* button. If not 
                            provided, there will be no cancel button.

        :arg hintText:      If provided, shown as a "hint", in a slightly 
                            faded font, between the checkboxes and the buttons.

        :arg focus:         One of ``'yes'``, ``'no'```, or ``'cancel'``,
                            specifying which button should be given initial
                            focus.
        
        :arg icon:          A ``wx`` icon identifier (e.g. 
                            ``wx.ICON_EXCLAMATION``).
        
        :arg style:         Passed through to the ``wx.Dialog.__init__``
                            method. Defaults to ``wx.DEFAULT_DIALOG_STYLE``.
        """

        if style      is None: style      = wx.DEFAULT_DIALOG_STYLE
        if title      is None: title      = ''
        if message    is None: message    = ''
        if cbMessages is None: cbMessages = ['']
        if cbStates   is None: cbStates   = [False] * len(cbMessages)
        if yesText    is None: yesText    = 'OK'

        wx.Dialog.__init__(self, parent, title=title, style=style)

        if icon is not None:
            icon = wx.ArtProvider.GetMessageBoxIcon(icon) 
            self.__icon = wx.StaticBitmap(self)

            if fslplatform.wxFlavour == fslplatform.WX_PYTHON:
                bmp = wx.EmptyBitmap(icon.GetWidth(), icon.GetHeight())
            else:
                bmp = wx.Bitmap()
                
            bmp.CopyFromIcon(icon)
            self.__icon.SetBitmap(bmp)
        else:
            self.__icon = (1, 1)

        self.__checkboxes = []
        for msg, state in zip(cbMessages, cbStates):
            cb = wx.CheckBox(self, label=msg)
            cb.SetValue(state)
            self.__checkboxes.append(cb)
            
        self.__message   = wx.StaticText(self, label=message)
        self.__yesButton = wx.Button(    self, label=yesText, id=wx.ID_YES)

        self.__yesButton.Bind(wx.EVT_BUTTON, self.__onYesButton)

        if noText is not None:
            self.__noButton = wx.Button(self, label=noText, id=wx.ID_NO)
            self.__noButton.Bind(wx.EVT_BUTTON, self.__onNoButton)

        else:
            self.__noButton = None
 
        if cancelText is not None:
            self.__cancelButton = wx.Button(self,
                                            label=cancelText,
                                            id=wx.ID_CANCEL)
            self.__cancelButton.Bind(wx.EVT_BUTTON, self.__onCancelButton)
        else:
            self.__cancelButton = None

        if hintText is not None:
            self.__hint = wx.StaticText(self, label=hintText)
            self.__hint.SetForegroundColour('#888888')
        else:
            self.__hint = None

        self.__mainSizer    = wx.BoxSizer(wx.HORIZONTAL)
        self.__contentSizer = wx.BoxSizer(wx.VERTICAL)
        self.__btnSizer     = wx.BoxSizer(wx.HORIZONTAL)

        self.__contentSizer.Add(self.__message,  flag=wx.EXPAND, proportion=1)
        self.__contentSizer.Add((1, 20), flag=wx.EXPAND)
        for cb in self.__checkboxes:
            self.__contentSizer.Add(cb, flag=wx.EXPAND)

        if self.__hint is not None:
            self.__contentSizer.Add((1, 20), flag=wx.EXPAND)
            self.__contentSizer.Add(self.__hint, flag=wx.EXPAND)

        self.__contentSizer.Add((1, 20), flag=wx.EXPAND)
        self.__btnSizer.Add((1, 1), flag=wx.EXPAND, proportion=1)

        buttons = [self.__yesButton, self.__noButton, self.__cancelButton]
        buttons = [b for b in buttons if b is not None]

        for i, b in enumerate(buttons):
            self.__btnSizer.Add(b)
            if i != len(buttons) - 1:
                self.__btnSizer.Add((5, 1), flag=wx.EXPAND)
        
        self.__contentSizer.Add(self.__btnSizer, flag=wx.EXPAND)

        self.__mainSizer.Add(self.__icon,
                             flag=wx.ALL | wx.CENTRE,
                             border=20)
        self.__mainSizer.Add(self.__contentSizer,
                             flag=wx.EXPAND | wx.ALL,
                             proportion=1,
                             border=20)

        self.__message.Wrap(self.GetSize().GetWidth())

        yes  = self.__yesButton
        no   = self.__noButton
        cncl = self.__cancelButton

        if   focus == 'yes':                         yes .SetDefault()
        elif focus == 'no'     and no   is not None: no  .SetDefault()
        elif focus == 'cancel' and cncl is not None: cncl.SetDefault()

        self.SetSizer(self.__mainSizer)
        self.Layout()
        self.Fit()
        self.CentreOnParent()


    def CheckBoxState(self, index=0):
        """After this ``CheckBoxMessageDialog`` has been closed, this method
        will retrieve the state of the dialog ``CheckBox``.
        """
        return self.__checkboxes[index].GetValue()


    def __onYesButton(self, ev):
        """Called when the button on this ``CheckBoxMessageDialog`` is
        clicked. Closes the dialog.
        """
        self.EndModal(wx.ID_YES)

        
    def __onNoButton(self, ev):
        """Called when the button on this ``CheckBoxMessageDialog`` is
        clicked. Closes the dialog.
        """
        self.EndModal(wx.ID_NO)

        
    def __onCancelButton(self, ev):
        """If the ``CHECKBOX_MSGDLG_CANCEL_BUTTON`` style was set, this method
        is called when the cancel button is clicked. Closes the dialog.
        """
        self.EndModal(wx.ID_CANCEL)
