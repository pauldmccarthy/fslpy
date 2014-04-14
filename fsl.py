#!/usr/bin/env python
#
# fsl.py - Front end to FSL tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import logging
import argparse
import wx

# There's a bug in OpenGL.GL.shaders (which has been fixed in
# the latest version) - it calls logging.basicConfig(), and
# thus screws up our own logging. We overcome this by configuring
# the root logger before OpenGL.GL.shaders is imported (which
# occurs when fsl.tools.bet imports fsl.utils.ImageView).
logging.basicConfig(
    format='%(levelname)8s '\
           '%(filename)20s '\
           '%(lineno)4d: '\
           '%(funcName)s - '\
           '%(message)s')
log = logging.getLogger('fsl')

import fsl.tools         as tools
import fsl.utils.webpage as webpage



def getArgs():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        'toolname', help='Name of FSL tool to run')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output')
    
    return parser.parse_args()


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

    args = getArgs()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Search in fsl.tools for the named module
    toolname = args.toolname
    toolmod  = getattr(tools, toolname, None)

    if toolmod is None:
        log.error('Unknown tool: {}'.format(modname))
        sys.exit(1)
    
    fsldir = os.environ.get('FSLDIR', None)

    fslEnvActive = fsldir is not None

    app   = wx.App()
    frame = buildGUI(toolmod, fslEnvActive)
    frame.Show()

    wx.CallLater(1, fslDirWarning, frame, toolname, fslEnvActive)
    
    #import wx.lib.inspection
    #wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
