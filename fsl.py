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
# occurs when fsl.fslview.SliceCanvas is imported).
logging.basicConfig(
    format='%(levelname)8s '
           '%(filename)20s '
           '%(lineno)4d: '
           '%(funcName)s - '
           '%(message)s')
log = logging.getLogger('fsl')

import fsl.tools         as tools
import fsl.utils.webpage as webpage



def loadAllFSLTools():
    """
    Looks in the fsl.tools package, loads a description for
    every FSL tool present, and returns all descriptions in
    a {toolName->toolObj} dictionary. See loadFSLTool.
    """

    allTools = {}

    for moduleName in dir(tools):
        
        module = getattr(tools, moduleName)

        try:              fsltool = loadFSLTool(moduleName, module)
        except TypeError: continue

        allTools[moduleName] = fsltool

    return allTools



def loadFSLTool(moduleName, module):
    """
    Inspects the given module to see if it looks like a valid
    FSL tool. If it is not, a TypeError is raised. If it is,
    a container object is created and returned, containing
    all of the elements of the tool.
    """

    # Each FSL tool module may specify several things
    toolName  = getattr(module, 'FSL_TOOLNAME',  None)
    helpPage  = getattr(module, 'FSL_HELPPAGE',  'index')
    arguments = getattr(module, 'FSL_ARGUMENTS', None)
    context   = getattr(module, 'FSL_CONTEXT',   None)
    interface = getattr(module, 'FSL_INTERFACE', None)
    actions   = getattr(module, 'FSL_ACTIONS',   [])

    # But at the very least, must specify a name, and
    # a function which will create an interface
    if not all((toolName, interface)):
        raise TypeError('"{}" does not appear to be a valid FSL tool'.format(
            moduleName))

    class FSLTool(object):
        pass

    fsltool = FSLTool()

    fsltool.module     = module
    fsltool.moduleName = moduleName
    fsltool.toolName   = toolName
    fsltool.helpPage   = helpPage
    fsltool.arguments  = arguments
    fsltool.context    = context
    fsltool.interface  = interface
    fsltool.actions    = actions

    return fsltool


def parseArgs(argv, allTools):
    """
    Creates a command line ArgumentParser which will process general
    arguments for fsl.py (this script) and, arguments for all FSL
    tools which have defined their own command line arguments (see
    loadFSLTool). Returns an object containing values for all of the
    arguments that were passed in.
    """

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose output')

    subparser  = parser.add_subparsers()

    for moduleName, fslTool in allTools.items():
        
        toolParser = subparser.add_parser(
            moduleName, help='{} help'.format(fslTool.toolName))
        toolParser.set_defaults(fslTool=fslTool)
        
        if fslTool.arguments is not None:
            fslTool.arguments(toolParser)

    return parser.parse_args(argv)


def fslDirWarning(frame, toolName, fslEnvActive):
    """
    If fslEnvActive is False, displays a warning.
    """

    if fslEnvActive: return

    msg = 'The FSLDIR environment variable is not set - '\
          '{} may not behave correctly.'.format(toolName)

    wx.MessageDialog(
        frame,
        message=msg,
        style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()


def buildGUI(fslTool, toolCtx, fslEnvActive):
    """
    """

    frame     = wx.Frame(None, title='FSL -- {}'.format(fslTool.toolName))
    toolPanel = fslTool.interface(frame, ctx)
    menuBar   = wx.MenuBar()
    fslMenu   = wx.Menu()
    
    frame.SetMenuBar(menuBar) 
    menuBar.Append(fslMenu, 'File')

    actions = []

    actions.append((
        wx.ID_HELP,
        '{} Help'.format(fslTool.toolName),
        lambda *ev: webpage.openFSLHelp(fslTool.helpPage)))

    for (name, func) in fslTool.actions:
        actions.append((wx.ID_ANY, name, lambda ev, f=func: f(frame, ctx)))

    actions.append((
        wx.ID_EXIT,
        'Exit',
        lambda *ev: frame.Close()))

    for wxId, name, func in actions:
        menuItem = fslMenu.Append(wxId, name)
        frame.Bind(wx.EVT_MENU, func, menuItem)

    frame.Layout()
    frame.Fit()

    return frame

    
if __name__ == '__main__':

    fsldir       = os.environ.get('FSLDIR', None)
    fslEnvActive = fsldir is not None

    
    allTools = loadAllFSLTools()
    args     = parseArgs(sys.argv[1:], allTools)
    fslTool  = args.fslTool

    if args.verbose:
        log.setLevel(logging.DEBUG)

    if fslTool.context is not None: ctx = fslTool.context(args)
    else:                           ctx = None

    app   = wx.App()
    frame = buildGUI(fslTool, ctx, fslEnvActive)
    frame.Show()

    wx.CallLater(1, fslDirWarning, frame, fslTool.toolName, fslEnvActive)
    
    # import wx.lib.inspection
    # wx.lib.inspection.InspectionTool().Show()
    
    app.MainLoop()
