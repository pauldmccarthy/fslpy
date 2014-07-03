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

# There's a bug in OpenGL.GL.shaders (which has been fixed in
# the latest version) - it calls logging.basicConfig(), and
# thus screws up our own logging. We overcome this by configuring
# the root logger before OpenGL.GL.shaders is imported (which
# occurs when fsl.fslview.SliceCanvas is imported).
logging.basicConfig(
    format='%(levelname)8.8s '
           '%(filename)20.20s '
           '%(lineno)4d: '
           '%(funcName)-15.15s - '
           '%(message)s') 
log = logging.getLogger('fsl')

try:
    import wx
except:
    log.warn('Could not import wx - GUI functionality is not available')

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
    parseArgs = getattr(module, 'FSL_PARSEARGS', None)
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
    fsltool.parseArgs  = parseArgs
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

    epilog = 'Type fsl.py help <tool> for program-specific help. ' \
             'Available programs:\n  {}'.format('\n  '.join(allTools.keys()))

    parser = argparse.ArgumentParser(
        description='Run a FSL program',
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-v', '--verbose', action='count',
        help='Verbose output (can be used up to 3 times)')
    parser.add_argument(
        '-w', '--wxinspect', action='store_true',
        help='Run wx inspection tool')
    parser.add_argument('tool', help='FSL program to run')

    namespace, argv = parser.parse_known_args(argv)

    # if the specified tool is 'help', it should be followed by
    # one more argument, the name of the tool to print help for
    if namespace.tool == 'help':
        
        # no tool name supplied
        if len(argv) == 0:
            parser.print_help()
            sys.exit(1)

        # unknown tool name supplied
        if argv[0] not in allTools:
            raise argparse.ArgumentError(
                'tool',
                'Unknown FSL tool: {}'.format(namespace.tool))

        fslTool = allTools[argv[0]]

        # no tool specific argument parser
        if fslTool.parseArgs is None:
            print 'No help for {}'.format(argv[0])
            
        # otherwise, get help from the tool
        else:
            fslTool.parseArgs([namespace.tool, '-h'], namespace)
        sys.exit(0)

    # Unknown tool name supplied
    elif namespace.tool not in allTools:
        raise argparse.ArgumentError(
            'tool',
            'Unknown FSL tool: {}'.format(namespace.tool))

    # otherwise, give the remaining arguments to the tool parser
    fslTool = allTools[namespace.tool] 
    
    if fslTool.parseArgs is not None:
        return fslTool, fslTool.parseArgs(argv, namespace)
    else:
        return fslTool, namespace


def fslDirWarning(frame, toolName, fslEnvActive):
    """
    If fslEnvActive is False, displays a warning.
    """

    if fslEnvActive: return

    msg = 'The FSLDIR environment variable is not set - '\
          '{} may not behave correctly.'.format(toolName)

    if frame is not None:
        wx.MessageDialog(
            frame,
            message=msg,
            style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()
    else:
        log.warn(msg)
        

def buildGUI(args, fslTool, toolCtx, fslEnvActive):
    """
    """

    frame = fslTool.interface(None, args, ctx)

    menuBar = frame.GetMenuBar()

    if menuBar is None:
        menuBar  = wx.MenuBar()
        frame.SetMenuBar(menuBar)
        
    fslMenu = wx.Menu()
    menuBar.Insert(0, fslMenu, 'FSL')

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

    return frame

    
if __name__ == '__main__':

    fsldir       = os.environ.get('FSLDIR', None)
    fslEnvActive = fsldir is not None

    allTools      = loadAllFSLTools()
    fslTool, args = parseArgs(sys.argv[1:], allTools)

    if args.verbose == 1:
        log.setLevel(logging.DEBUG)

        # make some noisy things quiet
        logging.getLogger('fsl.fslview.slicecanvas').setLevel(logging.WARNING)
        logging.getLogger('props')                  .setLevel(logging.WARNING)
        logging.getLogger('pwidgets')               .setLevel(logging.WARNING)
    elif args.verbose == 2:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.WARNING)
        logging.getLogger('pwidgets').setLevel(logging.WARNING)
    elif args.verbose == 3:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.DEBUG)
        logging.getLogger('pwidgets').setLevel(logging.DEBUG) 

    if fslTool.context is not None: ctx = fslTool.context(args)
    else:                           ctx = None

    if fslTool.interface is not None:
        
        app   = wx.App()
        frame = buildGUI(args, fslTool, ctx, fslEnvActive)
        frame.Show()

        wx.CallLater(1, fslDirWarning, frame, fslTool.toolName, fslEnvActive)

        if args.wxinspect:
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        
        app.MainLoop()
