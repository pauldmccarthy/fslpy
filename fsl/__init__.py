#!/usr/bin/env python
#
# __init__.py - Front end to fslpy. The entry point is main(), defined
# at the bottom.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`fsl` package contains front ends to various FSL tools,
including 'FSLEyes', the Python based image viewer.

This file contains the function :func:`main`, the application entry
point. When invoked with the name of a tool, the :mod:`fsl.tools` package
is searched for a module which has that name. All valid tool modules must
also provide the following module level attributes:

 - ``FSL_TOOLNAME``  - Mandatory. String providing the name of the tool.

 - ``FSL_HELPPAGE``  - Optional. A URL to a web page providing
                       help/documentation.

 - ``FSL_PARSEARGS`` - Optional. A function which is given a list of
                       command line arguments specific to the tool. The
                       function should parse the arguments and return,
                       for example, an :mod:`argparse` namespace object.

 - ``FSL_CONTEXT``   - Optional. A function which is passed the output of
                       the ``FSL_PARSEARGS`` function. It should perform
                       any necessary initialisation, and may optionally
                       return a value which will be passed to the
                       functions described below.
              
 - ``FSL_INTERFACE`` - Mandatory for GUI applications. A function which
                       accepts three parameters - a GUI parent object,
                       the value returned by the ``FSL_PARSEARGS``
                       function, and the value returned by the
                       ``FSL_CONTEXT`` function. Creates a :mod:`wx` GUI,
                       and returns the top level GUI object.

 - ``FSL_EXECUTE``   - Mandatory for non-GUI applications. A function
                       which accepts two parameters - the value returned
                       by the ``FSL_PARSEARGS`` function, and the value
                       returned by the ``FSL_CONTEXT`` function. Does
                       whatever the tool is supposed to do.

 - ``FSL_ACTIONS``   - Optional. Only relevant to GUI applications. A
                       list of (name, function) tuples, which will be
                       added as GUI menu items for the user to execute. 
                       An action function must accept two parameters - 
                       a parent GUI object, and the value returned by the
                       ``FSL_CONTEXT`` function.
"""


import logging
import warnings

import os
import os.path as op
import sys
import glob
import argparse
import importlib
import subprocess


# make numpy/matplotlib quiet
warnings.filterwarnings('ignore', module='matplotlib')
warnings.filterwarnings('ignore', module='mpl_toolkits')
warnings.filterwarnings('ignore', module='numpy')


# My own custom logging level for tracing memory related events
logging.MEMORY = 15
def logmemory(self, message, *args, **kwargs):
    if self.isEnabledFor(logging.MEMORY):
        self._log(logging.MEMORY, message, args, **kwargs)
        
logging.Logger.memory = logmemory
logging.addLevelName(logging.MEMORY, 'MEMORY')


# There's a bug in OpenGL.GL.shaders (which has been fixed in
# the latest version) - it calls logging.basicConfig(), and
# thus screws up our own logging. We overcome this by configuring
# the root logger before OpenGL.GL.shaders is imported (which
# occurs when fsl.fsleyes.gl.slicecanvas.SliceCanvas is imported).

logFormatter = logging.Formatter('%(levelname)8.8s '
                                 '%(filename)20.20s '
                                 '%(lineno)4d: '
                                 '%(funcName)-15.15s - '
                                 '%(message)s')
logHandler  = logging.StreamHandler()
logHandler.setFormatter(logFormatter)


# We want the root logger
log = logging.getLogger()


log.addHandler(logHandler)


import fsl.tools          as tools
import fsl.utils.settings as fslsettings


def getFSLToolNames():
    """Returns the name of every tool in the :mod:`fsl.tools` package.
    """

    toolFiles = glob.glob(op.join(op.dirname(tools.__file__), '*py'))
    allTools  = []
    
    for toolFile in toolFiles:

        toolName = op.splitext(op.basename(toolFile))[0]

        if toolName != '__init__':
            allTools.append(toolName)

    return allTools


def loadFSLTool(moduleName):
    """Inspects the given module to see if it looks like a valid
    FSL tool. If it is not, a TypeError is raised. If it is,
    a container object is created and returned, containing
    all of the elements of the tool.
    """

    module = importlib.import_module('fsl.tools.{}'.format(moduleName))

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
    """Creates a command line :class:`argparse.ArgumentParser` which will
    process general arguments for fsl.py (this script) and, arguments for
    all FSL tools which have defined their own command line arguments.
    Returns an object containing values for all of the arguments that were
    passed in.
    """

    epilog = 'Type fslpy help <tool> for program-specific help. ' \
             'Available programs:\n  {}'.format('\n  '.join(allTools))

    parser = argparse.ArgumentParser(
        prog='fslpy',
        description='Run a FSL program',
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument(
        '-v', '--verbose', action='count',
        help='Verbose output (can be used up to 3 times)')
    
    parser.add_argument(
        '-n', '--noisy', metavar='MODULE', action='append',
        help='Make the specified module noisy')

    parser.add_argument(
        '-m', '--memory', action='store_true',
        help='Output memory events (implied if -v is set)')
    
    parser.add_argument(
        '-w', '--wxinspect', action='store_true',
        help='Run wx inspection tool')
    parser.add_argument('tool', help='FSL program to run')

    # find the index of the first positional
    # argument, i.e. the tool name
    i = -1
    while True:

        i = i + 1
            
        if argv[i].startswith('-'):
            continue
            
        if i > 0 and argv[i - 1] in ('-n', '--noisy'):
            continue
        break
        
    firstPos = i
    
    # Separate the top level arguments
    # from the tool arguments, and parse
    # the top level args
    fslArgv   = argv[:firstPos + 1]
    toolArgv  = argv[ firstPos + 1:]

    namespace = parser.parse_args(fslArgv)

    if namespace.noisy is None:
        namespace.noisy = []

    # if the specified tool is 'help', it should be followed by
    # one more argument, the name of the tool to print help for
    if namespace.tool == 'help':
        
        # no tool name supplied
        if len(toolArgv) == 0:
            parser.print_help()
            sys.exit(1)

        # unknown tool name supplied
        if toolArgv[0] not in allTools:
            print '\nUnknown FSL tool: {}\n'.format(toolArgv[0])
            parser.print_help()
            sys.exit(1)

        fslTool = loadFSLTool(toolArgv[0])

        # no tool specific argument parser
        if fslTool.parseArgs is None:
            print 'No help for {}'.format(toolArgv[0])
            
        # Otherwise, get help from the tool. We assume that
        # all the argument parser for every  tool will interpret
        # '-h' as '--help', and will print some help
        else:
            fslTool.parseArgs(['-h'])
        sys.exit(0)

    # Unknown tool name supplied
    elif namespace.tool not in allTools:
        print '\nUnknown FSL tool: {}\n'.format(namespace.tool)
        parser.print_help()
        sys.exit(1)

    # Configure any logging verbosity 
    # settings specified by the user
    if namespace.verbose is None:
        if namespace.memory:
            class MemFilter(object):
                def filter(self, record):
                    if   record.name in namespace.noisy:   return 1
                    elif record.levelno == logging.MEMORY: return 1
                    else:                                  return 0

            log.setLevel(logging.MEMORY)
            log.handlers[0].addFilter(MemFilter())
            log.memory('Added filter for MEMORY messages')
            logging.getLogger('props')   .setLevel(logging.WARNING)
            logging.getLogger('pwidgets').setLevel(logging.WARNING)            
        
    if namespace.verbose == 1:
        log.setLevel(logging.DEBUG)

        # make some noisy things quiet
        logging.getLogger('fsl.fsleyes.gl')   .setLevel(logging.MEMORY)
        logging.getLogger('fsl.fsleyes.views').setLevel(logging.MEMORY)
        logging.getLogger('props')            .setLevel(logging.WARNING)
        logging.getLogger('pwidgets')         .setLevel(logging.WARNING)
    elif namespace.verbose == 2:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.WARNING)
        logging.getLogger('pwidgets').setLevel(logging.WARNING)
    elif namespace.verbose == 3:
        log.setLevel(logging.DEBUG)
        logging.getLogger('props')   .setLevel(logging.DEBUG)
        logging.getLogger('pwidgets').setLevel(logging.DEBUG)

    for mod in namespace.noisy:
        logging.getLogger(mod).setLevel(logging.DEBUG)

    # The trace module monkey-patches some
    # things if its logging level has been
    # set to DEBUG, so we import it now so
    # it can set itself up.
    import fsl.utils.trace

    fslTool = loadFSLTool(namespace.tool)

    if fslTool.parseArgs is not None: toolArgs = fslTool.parseArgs(toolArgv)
    else:                             toolArgs = None
    
    return fslTool, namespace, toolArgs


def fslDirWarning(frame, toolName, fslEnvActive):
    """If ``fslEnvActive`` is False, displays a warning that the ``FSLDIR``
    environment variable is not set. The warning is displayed either on
    stdout, or via a GUI dialog (if ``frame`` is not ``None``).
    """

    if fslEnvActive: return

    warnmsg = 'The FSLDIR environment variable is not set - '\
              '{} may not behave correctly.'.format(toolName)


    # Check fslpy settings before
    # prompting the user
    fsldir = fslsettings.read('fsldir')

    if fsldir is not None:
        os.environ['FSLDIR'] = fsldir
        return

    if frame is not None and fsldir is None:
        import wx
        from fsl.utils.fsldirdlg import FSLDirDialog

        dlg = FSLDirDialog(frame, toolName)

        if dlg.ShowModal() == wx.ID_OK:
            fsldir = dlg.GetFSLDir()
            log.debug('Setting $FSLDIR to {} (specified '
                      'by user)'.format(fsldir))
            
            os.environ['FSLDIR'] = fsldir
            fslsettings.write('fsldir', fsldir)
    else:
        log.warn(warnmsg)
        

def buildGUI(args, fslTool, toolCtx, fslEnvActive):
    """Builds a :mod:`wx` GUI for the tool."""

    import wx
    import fsl.utils.webpage as webpage

    frame = fslTool.interface(None, args, toolCtx)

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
        actions.append((wx.ID_ANY, name, lambda ev, f=func: f(frame, toolCtx)))

    actions.append((
        wx.ID_EXIT,
        'Exit',
        lambda *ev: frame.Close()))

    for wxId, name, func in actions:
        menuItem = fslMenu.Append(wxId, name)
        frame.Bind(wx.EVT_MENU, func, menuItem)

    return frame


def runTool(toolName, args, **kwargs):
    """Runs the tool with the specified name, with the specified arguments,
    in a separate process. Returns the process exit code.
    """

    args = [toolName] + args
    args = [sys.executable, '-c', 'import fsl; fsl.main()'] + args

    log.debug('Executing {}'.format(' '.join(args)))

    return subprocess.call(args, **kwargs)


def main(args=None):
    """Entry point.

    Parses command line arguments, loads the appropriate tool module, builds
    and displays a GUI (if the tool has one), or executes the tool.
    """

    # Search the environment for FSLDIR 
    fsldir       = os.environ.get('FSLDIR', None)
    fslEnvActive = fsldir is not None

    if args is None:
        args = sys.argv[1:]

    allTools                = getFSLToolNames()
    fslTool, args, toolArgs = parseArgs(args, allTools)

    if fslTool.interface is not None:
        import wx
        app   = wx.App()

        # Context creation may assume that a wx.App has been created
        if fslTool.context is not None: ctx = fslTool.context(toolArgs)
        else:                           ctx = None
        
        frame = buildGUI(toolArgs, fslTool, ctx, fslEnvActive)
        frame.Show()

        wx.CallLater(1, fslDirWarning, frame, fslTool.toolName, fslEnvActive)

        if args.wxinspect:
            import wx.lib.inspection
            wx.lib.inspection.InspectionTool().Show()
        
        app.MainLoop()
        
    elif fslTool.execute is not None:
        
        if fslTool.context is not None: ctx = fslTool.context(toolArgs)
        else:                           ctx = None
        
        fslDirWarning( None, fslTool.toolName, fslEnvActive)
        fslTool.execute(toolArgs, ctx)
