#!/usr/bin/env python
#
# runtool.py - Run a process, display its output in a wx window.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import subprocess as subp
import threading  as thread
import Queue      as queue

import wx

def checkAndRun(toolName, opts, parent, cmdFunc, optLabels={}, modal=True):
    """
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
        run(cmd, parent, modal) 


def run(cmd, parent, modal=True):
    """
    Runs the given command, displaying the output in a wx window.
    """

    proc   = None
    frame  = wx.Frame(parent, title=cmd[0])
    panel  = wx.Panel(frame)
    sizer  = wx.GridBagSizer()

    text        = wx.TextCtrl(panel, style=wx.TE_MULTILINE)
    killButton  = wx.Button(  panel, label='Kill process')
    closeButton = wx.Button(  panel, label='Close window')

    sizer.Add(text,        pos=(0,0), span=(1,2), flag=wx.EXPAND)
    sizer.Add(killButton,  pos=(1,0),             flag=wx.EXPAND)
    sizer.Add(closeButton, pos=(1,1),             flag=wx.EXPAND)

    sizer.AddGrowableRow(0)

    sizer.Fit(panel)
    panel.Layout()

    def kill():
        try:    proc.terminate()
        except: pass

    killButton .Bind(wx.EVT_BUTTON, kill)
    closeButton.Bind(wx.EVT_BUTTON, frame.Destroy)

    text.WriteText(' '.join(cmd) + '\n\n')

    # Run the command
    proc = subp.Popen(cmd, stdout=subp.PIPE, bufsize=1, stderr=subp.STDOUT)
    outq = queue.Queue()

    
    def writeToDialog():
        """
        Reads a string from the output queue,
        and appends it to the interface.
        """
        
        try:                output = outq.get_nowait()
        except queue.Empty: output = None

        if output is not None:
            try:    text.WriteText(output)
            except: pass

        
    def pollOutput():
        """
        Reads the output of the process, line by line, and
        writes it (asynchronously) to the interface.
        """
        
        for line in proc.stdout:
            print(line)
            outq.put(line)
            wx.CallLater(1, writeToDialog)
            
        outq.put('\nProcess finished\n')
        wx.CallLater(1, writeToDialog)

        def updateKillButton():
            try:    killButton.SetEnabled(False)
            except: pass

        wx.CallLater(1, updateKillButton)

        
    # poll the process output on a separate thread
    outputThread        = thread.Thread(target=pollOutput)
    outputThread.daemon = True
    outputThread.start()

    # make this window modal
    if modal: frame.ShowModal()
    else:     frame.Show()
