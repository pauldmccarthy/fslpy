#!/usr/bin/env python
#
# __init__.py - FSL tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains front-ends to all of the ``fslpy`` tools.

The following tools are available:

.. autosummary::
   ~fsl.tools.fsleyes
   ~fsl.tools.render
   ~fsl.tools.bet
   ~fsl.tools.feat
   ~fsl.tools.flirt

A ``fslpy`` tool is a python module which is contained within this package.
A tool may be a command line application, or a GUI application.


In order to be recognised by ``fslpy`` (see ``__init__.py`` in the :mod:`fsl`
package) a tool module must provide the following module level attributes:

================= =============================================================
``FSL_TOOLNAME``  Mandatory. String providing the name of the tool.

``FSL_HELPPAGE``  Optional. A URL to a web page providing help/documentation.

``FSL_PARSEARGS`` Optional. A function which is given a list of command line
                  arguments specific to the tool. The function should parse
                  the arguments and return, for example, an :mod:`argparse`
                  namespace object.

``FSL_CONTEXT``   Optional. A function which is passed the output of the
                  ``FSL_PARSEARGS`` function. It should perform any necessary
                  initialisation, and may optionally return a value which will
                  be passed to the functions described below.

``FSL_INTERFACE`` Mandatory for GUI applications. A function which accepts
                  three parameters - a GUI parent object, the value returned
                  by the ``FSL_PARSEARGS`` function, and the value returned by
                  the ``FSL_CONTEXT`` function. Creates a :mod:`wx` GUI, and
                  returns the top level GUI object.

``FSL_EXECUTE``   Mandatory for non-GUI applications. A function which accepts
                  two parameters - the value returned by the ``FSL_PARSEARGS``
                  function, and the value returned by the ``FSL_CONTEXT``
                  function. Does whatever the tool is supposed to do.

``FSL_ACTIONS``   Optional. Only relevant to GUI applications. A list of (name,
                  function) tuples, which will be added as GUI menu items for
                  the user to execute.  An action function must accept two
                  parameters - a parent GUI object, and the value returned by
                  the ``FSL_CONTEXT`` function.
================= =============================================================


The :func:`fsl.main` function does (the equivalent of) the following when
asked to run a ``fslpy`` tool:

1.  Imports the appropriate ``fsl.tools`` module::

        import fsl.tools.mytool as mytool

2.  Calls the ``FSL_PARSEARGS`` function::

        parsedArgs = mytool.FSL_PARSEARGS(cmdLineArgs)

3.  Calls the ``FSL_CONTEXT`` function, giving it the value returned by
    ``FSL_PARSEARGS``::

        context = mytool.FSL_CONTEXT(parsedArgs)

4.

 a. If the tool is a command line application, calls the ``FSL_EXECUTE``
    function, passing it the arguments and the context::

        mytool.FSL_EXECUTE(parsedArgs, context)

 b. Otherwise, a :mod:`wx` GUI is created::

        app = wx.App()
        frame = mytool.FSL_INTERFACE(None, parsedArgs, context)
        frame.Show()
        app.MainLoop()
"""
