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
# occurs when fsl.fslview.gl.slicecanvas.SliceCanvas is imported).
logging.basicConfig(
    format='%(levelname)8.8s '
           '%(filename)20.20s '
           '%(lineno)4d: '
           '%(funcName)-15.15s - '
           '%(message)s') 
log = logging.getLogger('fsl')

import fsl.tools as tools

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
    execute   = getattr(module, 'FSL_EXECUTE',   None)
    actions   = getattr(module, 'FSL_ACTIONS',   [])

    # But at the very least, must specify a name, and
    # either a function which will create an interface,
    # or a function which can be called to do some work
    if not all((toolName, any((interface, execute)))):
        raise TypeError('"{}" does not appear to be a valid FSL tool'.format(
            moduleName))

    # The tool must either provide an interface,
    # or do some non-interactive work.
    if interface and execute:
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
    fsltool.execute    = execute
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

    # find the index of the first positional argument
    try:
        firstPos = map(lambda a: not a.startswith('-'), argv).index(True)
    except ValueError:
        firstPos = len(argv)

    # Separate the top level arguments
    # from the tool arguments, and parse
    # the top level args
    fslArgv   = argv[:firstPos + 1]
    toolArgv  = argv[ firstPos + 1:]
    namespace = parser.parse_args(fslArgv)

    # if the specified tool is 'help', it should be followed by
    # one more argument, the name of the tool to print help for
    if namespace.tool == 'help':
        
        # no tool name supplied
        if len(toolArgv) == 0:
            parser.print_help()
            sys.exit(1)

        # unknown tool name supplied
        if toolArgv[0] not in allTools:
            print '\nUnknown FSL tool: {}\n'.format(namespace.tool) 
            parser.print_help()
            sys.exit(1)

        fslTool = allTools[toolArgv[0]]

        # no tool specific argument parser
        if fslTool.parseArgs is None:
            print 'No help for {}'.format(toolArgv[0])
            
        # Otherwise, get help from the tool. We assume that
        # all the argument parser for every  tool will interpret
        # '-h' as '--help', and will print some help
        else:
            fslTool.parseArgs([toolArgv[0], '-h'], namespace)
        sys.exit(0)

    # Unknown tool name supplied
    elif namespace.tool not in allTools:
        print '\nUnknown FSL tool: {}\n'.format(namespace.tool)
        parser.print_help()
        sys.exit(1)

    # otherwise, give the remaining arguments to the tool parser
    fslTool = allTools[namespace.tool] 
    
    if fslTool.parseArgs is not None:
        return fslTool, fslTool.parseArgs(toolArgv, namespace)
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
        import wx
        wx.MessageDialog(
            frame,
            message=msg,
            style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()
    else:
        log.warn(msg)
        

def buildGUI(args, fslTool, toolCtx, fslEnvActive):
    """
    """

    import wx
    import fsl.utils.webpage as webpage

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
        logging.getLogger('fsl.fslview.gl')   .setLevel(logging.WARNING)
        logging.getLogger('fsl.fslview.views').setLevel(logging.WARNING)
        logging.getLogger('props')            .setLevel(logging.WARNING)
        logging.getLogger('pwidgets')         .setLevel(logging.WARNING)
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
        import wx
        app   = wx.App()
        frame = buildGUI(args, fslTool, ctx, fslEnvActive)
        frame.Show()

        wx.CallLater(1, fslDirWarning, frame, fslTool.toolName, fslEnvActive)

        if args.wxinspect:
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        
        app.MainLoop()
        
    elif fslTool.execute is not None:
        fslDirWarning( None, fslTool.toolName, fslEnvActive)
        fslTool.execute(args, ctx)
