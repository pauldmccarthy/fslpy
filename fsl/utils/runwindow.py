#!/usr/bin/env python
#
# runwindow.py - Run a process, display its output in a wx window.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Run a process, display its output in a :class:`RunPanel`.

This module has two entry points - the :func:`checkAndRun` function, and the
:func:`run` function.
"""

import os
import signal
import logging

import subprocess as subp
import threading  as thread
import Queue      as queue

import wx


log = logging.getLogger(__name__)


class RunPanel(wx.Panel):
    """A panel which displays a multiline text control, and a couple of buttons
    along the bottom.
    """

    def __init__(self, parent):
        """Creates and lays out a text control, and two buttons.

        One of the buttons is intended to closes the window in which this
        panel is contained. The second button is intended to terminate the
        running process. Both buttons are unbound by default, so must be
        manually bound to callback functions.

        :ivar closeButton: The `Close window` button.
        :ivar killButton:  The `Terminate process` button.
        """
        wx.Panel.__init__(self, parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer) 
        
        # Horizontal scrolling no work in OSX
        # mavericks. I think it's a wxwidgets bug.
        self.text  = wx.TextCtrl(self,
                                 style=wx.TE_MULTILINE |
                                       wx.TE_READONLY  |
                                       wx.TE_DONTWRAP  |
                                       wx.HSCROLL)

        self.sizer.Add(self.text, flag=wx.EXPAND, proportion=1)

        self.btnPanel = wx.Panel(self)
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnPanel.SetSizer(self.btnSizer)
        
        self.sizer.Add(self.btnPanel, flag=wx.EXPAND)

        self.killButton  = wx.Button(self.btnPanel, label='Terminate process')
        self.closeButton = wx.Button(self.btnPanel, label='Close window')

        self.btnSizer.Add(self.killButton,  flag=wx.EXPAND, proportion=1)
        self.btnSizer.Add(self.closeButton, flag=wx.EXPAND, proportion=1)


class ProcessManager(thread.Thread):
    """A thread which manages the execution of a child process, and capture of its
    output.
    """

    def __init__(self, cmd, parent, runPanel, onFinish):
        """Create a ProcessManager thread object. Does nothing special.
        
        :arg cmd:      String or list of strings, the command to be
                       executed.
        
        :arg parent:   GUI parent object.
        
        :arg runPanel: :class:`RunPanel` object, for displaying the child 
                       process output.
        
        :arg onFinish: Callback function to be called when the process
                       finishes. May be ``None``. Must accept two parameters,
                       the GUI parent object, and the process return code.
        """
        thread.Thread.__init__(self, name=cmd[0])
        
        self.cmd      = cmd
        self.parent   = parent
        self.runPanel = runPanel
        self.onFinish = onFinish

        # Handle to the Popen object which represents
        # the child process. Created in run().
        self.proc = None

        # A queue for sharing data between the thread which
        # is blocking on process output (this thread object),
        # and the wx main thread which writes that output to
        # the runPanel
        self.outq = queue.Queue()
 
        # Put the command string at the top of the text control
        self.outq.put(' '.join(self.cmd) + '\n\n')
        wx.CallAfter(self.writeToPanel)


    def writeToPanel(self):
        """Reads a string from the output queue, and appends it
        to the :class:`RunPanel`. This method is intended to be
        executed via :func:`wx.CallAfter`.
        """
        
        try:                output = self.outq.get_nowait()
        except queue.Empty: output = None

        if output is None: return

        # ignore errors - the user may have closed the
        # runPanel window before the process has completed
        try:    self.runPanel.text.WriteText(output)
        except: pass
 

    def run(self):
        """Starts the process, then reads its output line by line, writing
        each line asynchronously to the :class:`RunPanel`.  When the
        process ends, the ``onFinish`` method (if there is one) is called. 
        If the process finishes abnormally (with a non-0 exit code) a warning
        dialog is displayed.
        """

        # Run the command. The preexec_fn parameter creates
        # a process group, so we are able to kill the child
        # process, and all of its children, if necessary. 
        log.debug('Running process: "{}"'.format(' '.join(self.cmd)))
        self.proc = subp.Popen(self.cmd,
                               stdout=subp.PIPE,
                               bufsize=1,
                               stderr=subp.STDOUT,
                               preexec_fn=os.setsid)

        # read process output, line by line, pushing
        # each line onto the output queue and
        # asynchronously writing it to the runPanel
        for line in self.proc.stdout:
            
            log.debug('Process output: {}'.format(line.strip()))
            self.outq.put(line)
            wx.CallAfter(self.writeToPanel)

        # When the above for loop ends, it means that the stdout
        # pipe has been broken. But it doesn't mean that the
        # subprocess is finished. So here, we wait until the
        # subprocess terminates, before continuing,
        self.proc.wait()

        retcode = self.proc.returncode
        
        log.debug(    'Process finished with return code {}'.format(retcode))
        self.outq.put('Process finished with return code {}'.format(retcode))

        wx.CallAfter(self.writeToPanel)

        # Disable the 'terminate' button on the run panel
        def updateKillButton():

            # ignore errors - see writeToPanel
            try:    self.runPanel.killButton.Enable(False)
            except: pass

        wx.CallAfter(updateKillButton)

        # Run the onFinish handler, if there is one
        if self.onFinish is not None:
            wx.CallAfter(self.onFinish, self.parent, retcode)

        
    def termProc(self):
        """Attempts to kill the running child process."""
        try:
            log.debug('Attempting to send SIGTERM to '
                      'process group with pid {}'.format(self.proc.pid))
            os.killpg(self.proc.pid, signal.SIGTERM)

            # put a message on the runPanel
            self.outq.put('\nSIGTERM sent to process\n\n')
            wx.CallAfter(self.writeToPanel)
            
        except:
            pass  # why am i ignoring errors here?


def run(name, cmd, parent, onFinish=None, modal=True):
    """Runs the given command, displaying the output in a :class:`RunPanel`.
    
    :arg name:     Name of the tool to be run, used in the window title.
    
    :arg cmd:      String or list of strings, specifying the command to be
                   executed.
    
    :arg parent:   :mod:`wx` parent object.
    
    :arg modal:    If ``True``, the command frame will be modal.

    :arg onFinish: Function to be called when the process ends. Must
                   accept two parameters - a reference to the :mod:`wx`
                   frame/dialog displaying the process output, and
                   the exit code of the application.
    """

    # Create the GUI - if modal, the easiest approach is to use a wx.Dialog
    if modal:
        frame = wx.Dialog(
            parent,
            title=name,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    else:
        frame = wx.Frame(parent, title=name)

    panel = RunPanel(frame)

    # Create the thread which runs the child process
    mgr = ProcessManager(cmd, parent, panel, onFinish)

    # Bind the panel control buttons so they do stuff
    panel.closeButton.Bind(wx.EVT_BUTTON, lambda e: frame.Close())
    panel.killButton .Bind(wx.EVT_BUTTON, lambda e: mgr.termProc())

    # Run the thread which runs the child process
    mgr.start()

    # layout and show the window
    frame.Layout()
    if modal: frame.ShowModal()
    else:     frame.Show()
 

def checkAndRun(name,
                opts,
                parent,
                cmdFunc,
                optLabels={},
                modal=True,
                onFinish=None):
    """Validates the given options. If invalid, a dialog is shown,
    informing the user about the errors. Otherwise, the tool is
    executed, and its output shown in a dialog window. Parameters:
    
    :arg name:      Name of the tool, used in the window title.
    
    :arg opts:      A :class:`~props.properties.HasProperties` object to be
                    validated.
    
    :arg parent:    :mod:`wx` object to be used as parent.
    
    :arg cmdFunc:   Function which takes a
                    :class:`~props.properties.HasProperties` object, 
                    and returns a command to be executed (as a list of
                    strings), which will be passed to the :func:`run`
                    function.
    
    :arg optLabels: Dictionary containing property ``{name : label}`` mappings.
                    Used in the error dialog, if any options are invalid.
    
    :arg modal:     If true, the command window will be modal.

    :arg onFinish:  Function to be called when the process ends.
    """

    errors = opts.validateAll()

    if len(errors) > 0:

        msg = 'There are numerous errors which need '\
              'to be fixed before {} can be run:\n'.format(name)

        for opt, error in errors:
            
            if opt in optLabels: name = optLabels[opt]
            msg = msg + '\n - {}: {}'.format(opt, error)

        wx.MessageDialog(
            parent,
            message=msg,
            style=wx.OK | wx.ICON_ERROR).ShowModal()
        
    else:
        cmd = cmdFunc(opts)
        run(name, cmd, parent, onFinish, modal)
