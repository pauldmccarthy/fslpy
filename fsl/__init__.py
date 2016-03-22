#!/usr/bin/env python
#
# __init__.py - Front end to fslpy. The entry point is main(), defined
# at the bottom.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`fsl` package contains front ends to various FSL tools, including
*FSLeyes*, the Python based image viewer.  The following top-level functions
are provided:

.. autosummary::
   :nosignatures:

   main
   runTool


The conventional way to run ``fslpy`` is as follows::

    import fsl

    # If no arguments are provided, the 
    # main() function will use sys.argv
    fsl.main()

    # Or, you can pass in arguments
    # programmatically
    fsl.main(['fsleyes', 'MNI152_T1_1mm.nii.gz', '--cmap', 'hot'])

    # You can ask for top level help
    fsl.main(['help'])

    # Or you can ask for help on a specific tool
    fsl.main(['help', 'render'])


.. note:: When the ``fsl`` package is imported, it configures a new
          ``logging`` level for tracking memory usage. The log level is
          attached to the ``logging`` module as ``logging.MEMORY``, and
          an associated log function is attached as ``logging.memory``.


.. note:: The ``fslpy`` version number (currently |version|) is set in a
          single place - the :mod:`fsl.version` module.
"""


from __future__ import print_function

import logging
import pkgutil
import warnings

import os
import sys
import time
import argparse
import importlib
import threading
import subprocess

import fsl.tools          as tools
import fsl.utils.settings as fslsettings
import fsl.utils.platform as fslplatform

import fsl.version


__version__ = fsl.version.__version__
"""The current ``fslpy`` version number. This information is stored in the
:mod:`fsl.version` module.
"""


def main(args=None):
    """``fslpy`` entry point.

    Parses command line arguments, loads the appropriate tool module, builds
    and displays a GUI (if the tool has one), and/or executes the tool.

    :arg args: Command line arguments. If not provided, ``sys.argv`` is used.
    """

    if args is None:
        args = sys.argv[1:]

    # Get a list of all available tools, 
    # and parse the top-level arguments
    allTools                     = _getFSLToolNames()
    fslTool, namespace, toolArgv = _parseTopLevelArgs(args, allTools)

    # GUI or command-line tool?
    if fslTool.interface is not None: _runGUITool(fslTool, namespace, toolArgv)
    else:                             _runCLITool(fslTool, namespace, toolArgv)


def _runGUITool(fslTool, topLevelArgs, toolArgv):
    """Runs the given ``FSLTool``, which is assumed to be a GUI tool.

    :arg fslTool:      The ``FSLTool`` to run - see the :func:`_loadFSLTool`
                       function.

    :arg topLevelArgs: An ``argparse.Namespace`` object containing parsed
                       top-level arguments.

    :arg toolArgv:     Unparsed tool-specific command line arguments.
    """
    import wx

    # Create the wx.App object befor fslTool.init,
    # in case it does GUI stuff. Also create a dummy
    # frame - if we don't create a dummy frame, the
    # wx.MainLoop call below will just return
    # immediately.
    #
    # The buildGUI function below will kill the dummy
    # frame when it has created the real interface.
    app        = wx.App()
    dummyFrame = wx.Frame(None)

    # Call the tool's init
    # function if there is one
    if fslTool.init is not None: initVal = fslTool.init()
    else:                        initVal = None

    # We are going do all processing on the
    # wx.MainLoop, so the GUI can be shown
    # as soon as possible, and because it is 
    # difficult to force immediate GUI
    # refreshes when not running on the main
    # loop - this is important for, e.g.
    # FSLEyes, which displays status updates
    # to the user while it is loading overlays
    # and setting up the interface.
    # 
    # To make this work, this buildGUI
    # function is called on a separate thread
    # (so it is executed after wx.MainLoop
    # has been called), but it schedules its
    # work to be done on the wx.MainLoop.
    def buildGUI():
        def realBuild():

            # Parse the tool-specific
            # command line arguments
            toolNamespace = _parseToolArgs(fslTool, toolArgv)

            # Call the tool context function
            if fslTool.context is not None:
                ctx = fslTool.context(toolNamespace, initVal)
            else:
                ctx = None

            # Build the GUI
            frame = _buildGUI(toolNamespace, fslTool, ctx)
            frame.Show()

            # See comment about the
            # dummy frame below
            dummyFrame.Destroy()

        # Sleep a bit so the main thread (on
        # which wx.MainLoop is running) can
        # start.
        time.sleep(0.01)

        if not topLevelArgs.skipfslcheck:
            wx.CallAfter(_fslDirWarning,
                         None,
                         fslTool.toolName,
                         'FSLDIR' in os.environ)
            
        wx.CallAfter(realBuild)

    threading.Thread(target=buildGUI).start()
    app.MainLoop()


def _runCLITool(fslTool, topLevelArgs, toolArgv):
    """Runs the given ``FSLTool``, which is assumed to be a command-line (i.e.
    non-GUI) tool.

    :arg fslTool:      The ``FSLTool`` to run - see the :func:`_loadFSLTool`
                       function.

    :arg topLevelArgs: An ``argparse.Namespace`` object containing parsed
                       top-level arguments. 

    :arg toolArgv:     Unparsed tool-specific command line arguments.     
    """

    if fslTool.execute is None:
        return

    # Call the tool's init
    # function if there is one
    if fslTool.init is not None: initVal = fslTool.init()
    else:                        initVal = None

    # Parse the tool-specific
    # command line arguments
    namespace = _parseToolArgs(fslTool, toolArgv) 

    initVal = None
    ctx     = None
    
    if fslTool.init    is not None: initVal = fslTool.init()
    if fslTool.context is not None: ctx     = fslTool.context(namespace,
                                                              initVal)

    if not topLevelArgs.skipfslcheck:
        _fslDirWarning(None, fslTool.toolName, 'FSLDIR' in os.environ)
        
    fslTool.execute(namespace, ctx)


def runTool(toolName, args, **kwargs):
    """Runs the tool with the specified name, with the specified arguments,
    in a separate process. Returns the process exit code.

    :arg toolName: Name of the FSL tool to run.

    :arg args:     Arguments to pass to the FSL tool.

    :arg kwargs:   Passed through to the ``subprocess.call`` function.
    """

    args = [toolName] + args

    if log.getEffectiveLevel() == logging.DEBUG:
        args = ['-vvv'] + args

    # If we are running from a compiled fsleyes
    # executable, we need to prepend command line
    # arguments with 'cmd' - see the wrapper script
    # created by:
    #
    # https://git.fmrib.ox.ac.uk/paulmc/fslpy_build/\
    #     blob/master/build_osx_app.sh
    if getattr(sys, 'frozen', False):
        args = [sys.executable, 'cmd'] + args

    # Otherwise we are running
    # through a python interpreter
    else:
        args = [sys.executable, '-c', 'import fsl; fsl.main()'] + args

    log.debug('Executing {}'.format(' '.join(args)))
    
    return subprocess.call(args, **kwargs)


def _getFSLToolNames():
    """Returns the name of every tool in the :mod:`fsl.tools` package. """

    # Under linux/Pyinstaller 3.1, iter_modules
    # doesn't seem to work, even if i include
    # the source code in the frozen app directory.
    # So i'm hard coding the names of the tool
    # modules.
    # 
    # A workaround would be to manually glob the
    # fsl/tools/ directory which, if I continue
    # to add the source code to the frozen app
    # directory, should work for both frozen and
    # unfrozen apps.
    if getattr(sys, 'frozen', False):
        allTools = ['fsleyes', 'render']
    else:
        allTools = [mod for _, mod, _ in pkgutil.iter_modules(tools.__path__)]

    return allTools


def _loadFSLTool(moduleName):
    """Inspects the given module to see if it looks like a valid FSL tool.
    If it is not, a :exc:`TypeError` is raised. If it is, a container
    object, a ``FSLTool`` is created and returned, containing all of the
    elements of the tool.

    The returned ``FSLTool`` instance contains the following attributes:

        ============== ========================================
        ``module``     The tool module.
        ``moduleName`` The tool module name.
        ``toolName``   The tool name.
        ``helpPage``   The tool help page URL.
        ``init``       An initialisation function.
        ``parseArgs``  A function to parse tool arguments.
        ``context``    A function to generate the tool context.
        ``interface``  A function to create the tool interface.
        ``execute``    A function to run the tool.
        ``actions``    A list of tool actions.
        ============== ========================================

    See the :mod:`fsl.tools` documentation for more details.
    """

    module = importlib.import_module('fsl.tools.{}'.format(moduleName))

    # Each FSL tool module may specify several things
    toolName  = getattr(module, 'FSL_TOOLNAME',  None)
    helpPage  = getattr(module, 'FSL_HELPPAGE',  None)
    init      = getattr(module, 'FSL_INIT',      None)
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
    fsltool.init       = init
    fsltool.parseArgs  = parseArgs
    fsltool.context    = context
    fsltool.interface  = interface
    fsltool.execute    = execute
    fsltool.actions    = actions

    return fsltool


def _parseTopLevelArgs(argv, allTools):
    """Parses top-level command line arguments. This involves parsing arguments
    which are shared across all tools.  Also identifies the tool to be invoked
    and configures logging verbosity. Returns a tuple containing the
    following:
    
      - The ``FSLTool`` instance (see :func:`_loadFSLTool`).
    
      - The :class:`argparse.Namespace` instance containing parsed arguments.
    
      - All remaining unparsed command line arguments (to be passed to the
        :func:`_parseToolArgs` function).
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
        '-V', '--version', action='store_true',
        help='Print the current fslpy version and exit')

    parser.add_argument(
        '-s', '--skipfslcheck', action='store_true',
        help='Skip $FSLDIR check/warning')
    
    parser.add_argument(
        '-n', '--noisy', metavar='MODULE', action='append',
        help='Make the specified module noisy')

    parser.add_argument(
        '-m', '--memory', action='store_true',
        help='Output memory events (implied if -v is set)')
    
    parser.add_argument('tool', help='FSL program to run', nargs='?')

    # No arguments at all? 
    # I'm not a mind-reader
    if len(argv) == 0:
        parser.print_help()
        sys.exit(1)

    # find the index of the first positional
    # argument, i.e. the tool name
    i = -1
    while True:

        i = i + 1

        if i >= len(argv):
            break
            
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

    # Version number
    if namespace.version:
        print('fslpy version: {}'.format(__version__))
        sys.exit(0)

    if namespace.noisy is None:
        namespace.noisy = []

    # if the specified tool is 'help', it should be followed by
    # one more argument, the name of the tool to print help for.
    # 
    # FSLeyes prints basic usage when passed '-h'/'--help';
    # to get all options, we need to pass '-fh'/'--fullhelp'.
    if namespace.tool in ('help', 'fullhelp'):
        
        # no tool name supplied
        if len(toolArgv) == 0:
            parser.print_help()
            sys.exit(1)

        # unknown tool name supplied
        if toolArgv[0] not in allTools:
            print('\nUnknown FSL tool: {}\n'.format(toolArgv[0]))
            parser.print_help()
            sys.exit(1)

        # Only fsleyes/render support full help
        if namespace.tool == 'fullhelp' and \
           toolArgv[0] not in ('fsleyes', 'render'):
            print('\n{} does not support fullhelp\n'.format(toolArgv[0]))
            parser.print_help()
            sys.exit(1) 

        fslTool = _loadFSLTool(toolArgv[0])

        # no tool specific argument parser
        if fslTool.parseArgs is None:
            print('No help for {}'.format(toolArgv[0]))
            
        # Otherwise, get help from the tool. We assume that
        # all the argument parser for every tool will interpret
        # '--help' (and fsleyes will interpret '--fullhelp'),
        # and will print some help.
        else:
            fslTool.parseArgs(['--{}'.format(namespace.tool)])
        sys.exit(0)

    # Unknown tool name supplied
    elif namespace.tool not in allTools:
        print('\nUnknown FSL tool: {}\n'.format(namespace.tool))
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
    traceLogger = logging.getLogger('fsl.utils.trace')
    if traceLogger.getEffectiveLevel() <= logging.DEBUG:
        import fsl.utils.trace

    fslTool = _loadFSLTool(namespace.tool)

    return fslTool, namespace, toolArgv


def _parseToolArgs(tool, argv):
    """Parses tool-specific command-line arguments. Returns the result of
    calling the ``FSL_PARSEARGS`` attribute of the given tool, or ``None``
    if the tool does not have the function.

    :arg tool:      The ``FSLTool`` to be invoked.
    :arg argv:      Command line arguments to be parsed.
    """

    if tool.parseArgs is not None: toolNamespace = tool.parseArgs(argv)
    else:                          toolNamespace = None
    
    return toolNamespace


def _fslDirWarning(parent, toolName, fslEnvActive):
    """If ``fslEnvActive`` is False, displays a warning that the ``$FSLDIR``
    environment variable is not set. The warning is displayed either on
    stdout, or via a GUI dialog (if ``wx`` is available).

    :arg parent:       A ``wx`` parent for the :class:`.FSLDirDialog`, if it
                       is displayed.
    
    :arg toolName:     Name of the tool that is being executed.

    :arg fslEnvActive: Set to ``True`` if ``$FSLDIR`` is set, ``False``
                       otherwise.
    """

    if fslEnvActive: return

    haveGui = False
    try:
        import wx
        if wx.GetApp() is not None:
            haveGui = True
    except:
        pass

    warnmsg = 'The FSLDIR environment variable is not set - '\
              '{} may not behave correctly.'.format(toolName)

    # Check fslpy settings before
    # prompting the user
    fsldir = fslsettings.read('fsldir')

    if fsldir is not None:
        os.environ['FSLDIR']        = fsldir
        fslplatform.platform.fsldir = fsldir
        return

    if haveGui:
        import wx
        from fsl.utils.dialog import FSLDirDialog

        def warn():
            dlg = FSLDirDialog(parent, toolName)

            if dlg.ShowModal() == wx.ID_OK:
                fsldir = dlg.GetFSLDir()
                log.debug('Setting $FSLDIR to {} (specified '
                          'by user)'.format(fsldir))

                fslplatform.platform.fsldir   = fsldir
                os.environ[         'FSLDIR'] = fsldir
                fslsettings.write(  'fsldir',   fsldir)

        wx.CallLater(500, warn)

    else:
        log.warn(warnmsg)
        

def _buildGUI(args, fslTool, toolCtx):
    """Builds a :mod:`wx` GUI for the tool.

    :arg fslTool:      The ``FSLTool`` instance (see :func:`_loadFSLTool`).

    :arg toolCtx:      The tool context, as returned by the 
                       ``FSLTool.context`` function.
    """

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

    def help(ev):
        if fslTool.helpPage is not None:
            webpage.openPage(fslTool.helpPage)
        else:
            webpage.openLocalHelp(fslTool.toolName)

    actions.append((
        wx.ID_HELP,
        '{} Help'.format(fslTool.toolName),
        help))

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


#################################
# My own custom logging level for
# tracing memory related events
#################################

logging.MEMORY = 15
def _logmemory(self, message, *args, **kwargs):
    """Log function for my custom ``logging.MEMORY`` logging level. """
    if self.isEnabledFor(logging.MEMORY):
        self._log(logging.MEMORY, message, args, **kwargs)
        
logging.Logger.memory = _logmemory
logging.addLevelName(logging.MEMORY, 'MEMORY')



#########################
# Fix some logging quirks
#########################


# make numpy/matplotlib quiet
warnings.filterwarnings('ignore', module='matplotlib')
warnings.filterwarnings('ignore', module='mpl_toolkits')
warnings.filterwarnings('ignore', module='numpy')


# There's a bug in OpenGL.GL.shaders (PyOpenGL 3.1.0. - it's been
# fixed in the development version) - it calls logging.basicConfig(),
# and thus screws up our own logging. We overcome this by configuring
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
