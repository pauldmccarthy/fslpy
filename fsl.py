#!/usr/bin/env python
#
# fsl.py - Front end to FSL tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import logging

import wx

import fsl.tools         as tools
import fsl.utils.webpage as webpage

def fslDirWarning(frame, toolName, fslEnvActive):
    """
    If fslEnvActive is False, displays a warning.
    """

    if fslEnvActive: return

    msg = 'The FSLDIR environment variable is not set - '\
          'you will not be able to run {}.'.format(toolName)

    wx.MessageDialog(
        frame,
        message=msg,
        style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()


def buildGUI(module, fslEnvActive):

    # Each FSL tool module must specify several things
    toolName  = getattr(module, 'FSL_TOOLNAME',  None)
    helpPage  = getattr(module, 'FSL_HELPPAGE',  'index')
    options   = getattr(module, 'FSL_OPTIONS',   None)
    interface = getattr(module, 'FSL_INTERFACE', None)
    runtool   = getattr(module, 'FSL_RUNTOOL',   None)

    if not all((toolName, options,  interface)):
        logging.error('"{}" does not appear to be a valid FSL tool'.format(
            module.__name__))
        sys.exit(1)

    opts = options()

    frame       = wx.Frame(None, title='FSL -- {}'.format(toolName))
    mainPanel   = wx.Panel(frame)
    buttonPanel = wx.Panel(mainPanel)
    toolPanel   = interface(mainPanel, opts)

    runButton   = wx.Button(buttonPanel, label='Run {}'.format(toolName))
    helpButton  = wx.Button(buttonPanel, label='Help')
    quitButton  = wx.Button(buttonPanel, label='Quit') 

    buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    mainSizer   = wx.BoxSizer(wx.VERTICAL)

    mainSizer.Add(toolPanel,   flag=wx.EXPAND, proportion=1)
    mainSizer.Add(buttonPanel, flag=wx.EXPAND)

    buttonSizer.Add(runButton,  flag=wx.EXPAND, proportion=1)
    buttonSizer.Add(helpButton, flag=wx.EXPAND, proportion=1)
    buttonSizer.Add(quitButton, flag=wx.EXPAND, proportion=1)

    if runtool is not None and fslEnvActive:
        runButton.Bind(wx.EVT_BUTTON, lambda e: runtool(frame, opts))
    else:
        runButton.Enable(False)

    if fslEnvActive:
        helpButton.Bind(wx.EVT_BUTTON, lambda e: webpage.openFSLHelp(helpPage))
    else:
        helpButton.Enable(False)

    quitButton.Bind(wx.EVT_BUTTON, lambda e: frame.Destroy())

    buttonPanel.SetSizer(buttonSizer)
    mainPanel  .SetSizer(mainSizer)
    
    buttonSizer.Layout()
    mainSizer  .Layout() 

    buttonSizer.Fit(buttonPanel)
    mainSizer  .Fit(mainPanel)
    frame      .Fit()

    return frame

    
if __name__ == '__main__':

    logging.basicConfig(
        format='%(levelname)8s %(filename)20s %(lineno)4d: %(funcName)s - %(message)s',
        level=logging.DEBUG) 

    if len(sys.argv) != 2:
        logging.error('usage: fsl.py toolname')
        sys.exit(1)

    # Search in fsl.tools for the named module
    modname = sys.argv[1]
    toolmod = getattr(tools, modname, None)

    if toolmod is None:
        logging.error('Unknown tool: {}'.format(modname))
        sys.exit(1)

    fsldir = os.environ.get('FSLDIR', None)

    fslEnvActive = fsldir is not None

    app   = wx.App() 
    frame = buildGUI(toolmod, fslEnvActive)
    frame.Show()

    wx.CallLater(1, fslDirWarning, frame, modname, fslEnvActive)
    
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
