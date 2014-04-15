#!/usr/bin/env python
#
# runwindow.py - Run a process, display its output in a wx window.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import signal
import logging

import subprocess as subp
import threading  as thread
import Queue      as queue

import wx


log = logging.getLogger(__name__)


class RunPanel(wx.Panel):
    """
    A panel which displays a multiline text control, and a collection of
    buttons along the bottom.
    """

    def __init__(self, parent, buttons=[]):
        """
        Creates and lays out a text control, and the buttons specified
        in the given (label, callback function) tuple list.
        """
        wx.Panel.__init__(self, parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.text  = wx.TextCtrl(self,
                                 style=wx.TE_MULTILINE | \
                                       wx.TE_READONLY  | \
                                       wx.TE_DONTWRAP  | \
                                       wx.HSCROLL)

        self.sizer.Add(self.text, flag=wx.EXPAND, proportion=1)

        if len(buttons) > 0:

            self.btnPanel = wx.Panel(self)
            self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.buttons  = {}

            self.btnPanel.SetSizer(self.btnSizer)

            self.sizer.Add(self.btnPanel, flag=wx.EXPAND)

            for btnSpec in buttons:

                label, callback = btnSpec

                btn = wx.Button(self.btnPanel, label=label)
                btn.Bind(wx.EVT_BUTTON, lambda e,cb=callback: cb())

                self.buttons[label] = btn
                self.btnSizer.Add(btn, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self.sizer)


def checkAndRun(toolName, opts, parent, cmdFunc,
                optLabels={},
                modal=True,
                onFinish=None):
    """
    Validates the given options. If invalid, a dialog is shown, informing
    the user about the errors. Otherwise, the tool is executed, and its
    output shown in a dialog window. Parameters:
    
      - toolName:  Name of the tool, used in the window title
    
      - opts:      HasProperties object to be validated
    
      - parent:    wx object to be used as parent
    
      - cmdFunc:   Function which takes a HasProperties object, and returns
                   a command to be executed (as a list of strings), which
                   will be passed to the run() function.
    
      - optLabels: Dictionary containing property name -> label mappings.
    
      - modal:     If true, the command window will be modal.

      - onFinish:  Function to be called when the process ends.
    """

    errors = opts.validateAll()

    if len(errors) > 0:

        msg = 'There are numerous errors which need '\
              'to be fixed before {} can be run:\n'.format(toolName)

        for name,error in errors:
            
            if name in optLabels: name = optLabels[name]
            msg = msg + '\n - {}: {}'.format(name, error)

        wx.MessageDialog(
            parent,
            message=msg,
            style=wx.OK | wx.ICON_ERROR).ShowModal()
        
    else:
        cmd = cmdFunc(opts)
        run(toolName, cmd, parent, modal, onFinish)


def run(name, cmd, parent, modal=True, onFinish=None, actions=None):
    """
    Runs the given command, displaying the output in a wx window.
    Parameters:
    
      - name:     Name of the tool to be run, used in the window title.
    
      - cmd:      List of strings, specifying the command (+args) to be
                  executed.
    
      - parent:   wx parent object.
    
      - modal:    If true, the command window will be modal.

      - onFinish: Function to be called when the process ends. Must
                  accept two parameters - a reference to the wx
                  frame/dialog displaying the process output, and
                  the exit code of the application.
          
    """

    if actions is None: actions = []

    frame = None # wx.Frame or Dialog, the parent window
    panel = None # Panel containing process output and control buttons
    proc  = None # Object representing the process
    outq  = None # Queue used for reading process output
    
    def writeToDialog():
        """
        Reads a string from the output queue,
        and appends it to the interface.
        """
        
        try:                output = outq.get_nowait()
        except queue.Empty: output = None

        if output is not None:

            # ignore errors - the user may have closed the
            # dialog window before the process has completed
            try:    panel.text.WriteText(output)
            except: pass

            
    def pollOutput():
        """
        Reads the output of the process, line by line, and
        writes it (asynchronously) to the interface. When
        the process ends, the onFinish method (if there is
        one) is called.
        """
        
        for line in proc.stdout:
            
            log.debug('Process output: {}'.format(line.strip()))
            outq.put(line)
            wx.CallAfter(writeToDialog)

        # When the above for loop ends, it means that the stdout
        # pipe has been broken. But it doesn't mean that the
        # subprocess is finished. So here, we wait until the
        # subprocess terminates, before continuing,
        proc.wait()

        retcode = proc.returncode
        
        log.debug('Process finished with return code {}'.format(retcode))
            
        outq.put('\nProcess finished\n')
        wx.CallAfter(writeToDialog)

        if onFinish is not None:
            wx.CallAfter(onFinish, frame, retcode)

        def updateKillButton():

            # ignore errors - see writeToDialog
            try:    panel.buttons['Terminate process'].Enable(False)
            except: pass

        wx.CallAfter(updateKillButton)


    def termProc():
        """
        Callback function for the 'Kill process' button. 
        """
        try:
            log.debug('Attempting to send SIGTERM to '\
                      'process group with pid {}'.format(proc.pid))
            os.killpg(proc.pid, signal.SIGTERM)
            outq.put('\nSIGTERM sent to process\n\n')
            wx.CallAfter(writeToDialog)
            
        except:
            pass # why am i ignoring errors here?
            
    # Create the GUI
    if modal:
        frame = wx.Dialog(
            parent,
            title=name,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
    else:
        frame = wx.Frame(parent, title=name)

    # Default buttons 
    actions.append(('Terminate process', termProc))
    actions.append(('Close window',      frame.Close))

    panel = RunPanel(frame, actions)

    # Put the command string at the top of the text control
    panel.text.WriteText(' '.join(cmd) + '\n\n')

    # Run the command
    log.debug('Running process: "{}"'.format(' '.join(cmd)))
    proc = subp.Popen(cmd,
                      stdout=subp.PIPE,
                      bufsize=1,
                      stderr=subp.STDOUT,
                      preexec_fn=os.setsid)
        
    # poll the process output on a separate thread
    outq                = queue.Queue()
    outputThread        = thread.Thread(target=pollOutput)
    outputThread.daemon = True
    outputThread.start()

    # layout and show the window
    frame.Layout()
    if modal: frame.ShowModal()
    else:     frame.Show()
