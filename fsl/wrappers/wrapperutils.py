#!/usr/bin/env python
#
# wrapperutils.py - Functions and decorators used by the FSL wrapper
# functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Martin Craig <martin.craig@eng.ox.ac.uk>
#
"""This module contains functions and decorators used by the FSL wrapper
functions.


The :func:`cmdwrapper` and :func:`fslwrapper` functions are convenience
decorators which allow you to write your wrapper function such that it simply
generates the command-line needed to respectively run a standard shell
command or a FSL command. For example::


    @fslwrapper
    def fslreorient2std(input, output):
        return ['fslreorient2std', input, output]


When this ``fslreorient2std`` function is called, the ``fslwrapper`` decorator
will take care of invoking the command in a standardised way.


The :func:`applyArgStyle` function can be used to automatically convert
keyword arguments into command-line arguments, based on a set of standard
patterns. For example::


    @fslwrapper
    def flirt(src, ref, **kwargs):
        cmd  = ['flirt', '-in', src, '-ref', ref]
        return cmd + applyArgStyle('-=', **kwargs)


The :func:`fileOrImage` and :func:`fileOrArray` functions can be used to
decorate a wrapper function such that in-memory ``nibabel`` images or Numpy
arrays can be passed in as arguments - they will be automatically saved out to
files, and then the file names passed into the wrapper function. For example::


    @fileOrImage('src', 'ref')
    @fslwrapper
    def flirt(src, ref, **kwargs):
        cmd  = ['flirt', '-in', src, '-ref', ref]
        return cmd + applyArgStyle('-=', **kwargs)


Now this ``flirt`` function can be called either with file names, or
``nibabel`` images.


.. note:: Because the :func:`fileOrImage` and :func:`fileOrArray` decorators
          manipulate the return value of the decorated function, they should
          be applied *after* any other decorators. Furthermore, if you need to
          apply both a ``fileOrImage`` and ``fileOrArray`` decorator to a
          function, they should be grouped together, e.g.::

              @fileOrImage('a', 'b')
              @fileOrArray('c', 'd')
              @fslwrapper
              def func(**kwargs):
                  ...


Command outputs can also be loaded back into memory by using the special
:data:`LOAD` value when calling a wrapper function. For example::


    @fileOrImage('src', 'ref', 'out')
    @fslwrapper
    def flirt(src, ref, **kwargs):
        cmd  = ['flirt', '-in', src, '-ref', ref]
        return cmd + applyArgStyle('-=', **kwargs)


If we set the ``out`` argument to ``LOAD``, the output image will be loaded
and returned::

    src     = nib.load('src.nii')
    ref     = nib.load('ref.nii')
    aligned = flirt(src, ref, out=LOAD)['out']
"""


import itertools       as it
import os.path         as op
import collections.abc as abc
import                    os
import                    re
import                    sys
import                    glob
import                    random
import                    string
import                    fnmatch
import                    inspect
import                    logging
import                    tempfile
import                    warnings
import                    functools


import            six
import nibabel as nib
import numpy   as np

import fsl.utils.run     as run
import fsl.utils.path    as fslpath
import fsl.utils.tempdir as tempdir
import fsl.data.image    as fslimage


log = logging.getLogger(__name__)


def _update_wrapper(wrapper, wrapped, *args, **kwargs):
    """Replacement for the built-in ``functools.update_wrapper``. This
    implementation ensures that the wrapper function has an attribute
    called ``__wrapped__``, which refers to the ``wrapped`` function.

    This custom function is only needed in Python versions < 3.4.
    """

    wrapper = functools.update_wrapper(wrapper, wrapped, *args, **kwargs)

    # Python >= 3.4 does things right
    if (sys.version_info[0] * 10 + sys.version_info[1]) < 34:
        wrapper.__wrapped__ = wrapped
    return wrapper


def _unwrap(func):
    """Replacement for the built-in ``inspect.unwrap`` function, which
    is not present in Python versions prior to 3.4.
    """

    # Python >= 3.4 has an inspect.unwrap function
    if (sys.version_info[0] * 10 + sys.version_info[1]) >= 34:
        return inspect.unwrap(func)

    # Otherwise we follow the __wrapped__ chain ourselves
    if hasattr(func, '__wrapped__'):
        return _unwrap(func.__wrapped__)

    return func


def cmdwrapper(func):
    """This decorator can be used on functions which generate a command line.
    It will pass the return value of the function to the
    :func:`fsl.utils.run.run` function in a standardised manner.
    """
    def wrapper(*args, **kwargs):
        stdout = kwargs.pop('stdout', True)
        stderr = kwargs.pop('stderr', True)
        exitcode = kwargs.pop('exitcode', False)
        submit = kwargs.pop('submit', None)
        log    = kwargs.pop('log',    {'tee' : True})
        cmd    = func(*args, **kwargs)
        return run.run(cmd,
                       stderr=stderr,
                       log=log,
                       submit=submit,
                       stdout=stdout,
                       exitcode=exitcode)
    return _update_wrapper(wrapper, func)


def fslwrapper(func):
    """This decorator can be used on functions which generate a FSL command
    line. It will pass the return value of the function to the
    :func:`fsl.utils.run.runfsl` function in a standardised manner.
    """
    def wrapper(*args, **kwargs):
        stdout = kwargs.pop('stdout', True)
        stderr = kwargs.pop('stderr', True)
        exitcode = kwargs.pop('exitcode', False)
        submit = kwargs.pop('submit', None)
        log    = kwargs.pop('log',    {'tee' : True})
        cmd    = func(*args, **kwargs)
        return run.runfsl(cmd,
                          stderr=stderr,
                          log=log,
                          submit=submit,
                          stdout=stdout,
                          exitcode=exitcode)
    return _update_wrapper(wrapper, func)


SHOW_IF_TRUE = object()
"""Constant to be used in the ``valmap`` passed to the :func:`applyArgStyle`
function.

When a ``SHOW_IF_TRUE`` argument is ``True``, it is added to the generated
command line arguments.
"""


HIDE_IF_TRUE = object()
"""Constant to be used in the ``valmap`` passed to the :func:`applyArgStyle`
function.

When a ``HIDE_IF_TRUE`` argument is ``True``, it is suppressed from the
generated command line arguments.
"""


def applyArgStyle(style,
                  valsep=None,
                  argmap=None,
                  valmap=None,
                  singlechar_args=False,
                  **kwargs):
    """Turns the given ``kwargs`` into command line options. This function
    is intended to be used to automatically generate command line options
    from arguments passed into a Python function.

    The ``style`` and ``valsep`` arguments control how key-value pairs
    are converted into command-line options:


    =========  ==========  ===========================
    ``style``  ``valsep``  Result
    =========  ==========  ===========================
    ``'-'``    ``' '``     ``-name val1 val2 val3``
    ``'-'``    ``'"'``     ``-name "val1 val2 val3"``
    ``'-'``    ``','``     ``-name val1,val2,val3``
    ``'--'``   ``' '``     ``--name val1 val2 val3``
    ``'--'``   ``'"'``     ``--name "val1 val2 val3"``
    ``'--'``   ``','``     ``--name val1,val2,val3``
    ``'-='``   ``' '``     Not supported
    ``'-='``   ``'"'``     ``-name="val1 val2 val3"``
    ``'-='``   ``','``     ``-name=val1,val2,val3``
    ``'--='``  ``' '``     Not supported
    ``'--='``  ``'"'``     ``--name="val1 val2 val3"``
    ``'--='``  ``','``     ``--name=val1,val2,val3``
    =========  ==========  ===========================


    :arg style:  Controls how the ``kwargs`` are converted into command-line
                 options - must be one of ``'-'``, ``'--'``, ``'-='``, or
                 ``'--='``.

    :arg valsep: Controls how the values passed to command-line options
                 which expect multiple arguments are delimited - must be
                 one of ``' '``, ``','`` or ``'"'``. Defaults to ``' '``
                 if ``'=' not in style``, ``','`` otherwise.

    :arg argmap: Dictionary of ``{kwarg-name : cli-name}`` mappings. This can
                 be used if you want to use different argument names in your
                 Python function for the command-line options.

    :arg valmap: Dictionary of ``{cli-name : value}`` mappings. This can be
                 used to define specific semantics for some command-line
                 options. Acceptable values for ``value`` are as follows

                  - :data:`SHOW_IF_TRUE` - if the argument is present, and
                    ``True`` in ``kwargs``, the command line option
                    will be added (without any arguments).

                  - :data:`HIDE_IF_TRUE` - if the argument is present, and
                    ``False`` in ``kwargs``, the command line option
                    will be added (without any arguments).

                  - Any other constant value. If the argument is present
                    in ``kwargs``, its command-line option will be
                    added, with the constant value as its argument.

                 The argument for any options not specified in the ``valmap``
                 will be converted into strings.

    :arg singlechar_args: If True, single character arguments always take a
                          single hyphen prefix (e.g. -h) regardless of the
                          style.

    :arg kwargs: Arguments to be converted into command-line options.

    :returns:    A list containing the generated command-line options.
    """

    if valsep is None:
        if '=' in style: valsep = ','
        else:            valsep = ' '

    if style not in ('-', '--', '-=', '--='):
        raise ValueError('Invalid style: {}'.format(style))
    if valsep not in (' ', ',', '"'):
        raise ValueError('Invalid valsep: {}'.format(valsep))

    # we don't handle the case where '=' in
    # style, and valsep == ' ', because no
    # sane CLI app would do this. Right?
    if '=' in style and valsep == ' ':
        raise ValueError('Incompatible style and valsep: s={} v={}'.format(
            style, valsep))

    if argmap is None: argmap = {}
    if valmap is None: valmap = {}

    def fmtarg(arg):
        if   style in ('-',  '-=') or (singlechar_args and len(arg) == 1):
            arg =  '-{}'.format(arg)
        elif style in ('--', '--='):
            arg = '--{}'.format(arg)
        return arg

    # always returns a sequence
    def fmtval(val):
        if     isinstance(val, abc.Sequence) and \
           not isinstance(val, six.string_types):

            val = [str(v) for v in val]
            if   valsep == ' ': return val
            elif valsep == '"': return [' '   .join(val)]
            else:               return [valsep.join(val)]
        else:
            return [str(val)]

    # val is assumed to be a sequence
    def fmtargval(arg, val):
        # if '=' in style, val will
        # always be a single string
        if '=' in style: return ['{}={}'.format(arg, val[0])]
        else:            return [arg] + val

    args = []

    for k, v in kwargs.items():

        if v is None: continue

        k    = argmap.get(k, k)
        mapv = valmap.get(k, fmtval(v))
        k    = fmtarg(k)

        if mapv in (SHOW_IF_TRUE, HIDE_IF_TRUE):
            if (mapv is SHOW_IF_TRUE and     v) or \
               (mapv is HIDE_IF_TRUE and not v):
                args.append(k)
        else:
            args.extend(fmtargval(k, mapv))

    return args


def namedPositionals(func, args):
    """Given a function, and a sequence of positional arguments destined
    for that function, identifies the name for each positional argument.
    Variable positional arguments are given an automatic name.

    :arg func: Function which will accept ``args`` as positionals.
    :arg args: Tuple of positional arguments to be passed to ``func``.
    """

    # Current implementation will
    # result in naming collisions
    # for something like this:
    #
    # def func(args0, *args):
    #     ...
    # because of automatic vararg
    # naming. But who would write
    # a function like that anyway?

    # Remove any decorators
    # from the function
    func = _unwrap(func)

    # getargspec is the only way to
    # get the names of positional
    # arguments in Python 2.x.
    if sys.version_info[0] < 3:
        spec     = inspect.getargspec(func)
        argnames = spec.args
        varargs  = spec.varargs

    # But getargspec is deprecated
    # in python 3.x
    else:

        # getfullargspec is deprecated in
        # python 3.5, but not in python 3.6.
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            spec     = inspect.getfullargspec(func)
            argnames = spec.args
            varargs  = spec.varargs

    # we only care about the arguments
    # that are being passed in
    argnames = argnames[:len(args)]

    # make up names for varargs
    nvarargs = len(args) - len(argnames)
    if varargs is not None and nvarargs > 0:
        argnames += ['{}{}'.format(varargs, i) for i in range(nvarargs)]

    return argnames


LOAD = object()
"""Constant used by the :class:`_FileOrThing` class to indicate that an output
file should be loaded into memory and returned as a Python object.
"""


class _FileOrThing(object):
    """Decorator which ensures that certain arguments which are passed into the
    decorated function are always passed as file names. Both positional and
    keyword arguments can be specified.


    The ``_FileOrThing`` class is not intended to be used directly - see the
    :func:`fileOrImage` and :func:`fileOrArray` decorator functions for more
    details.


    These decorators are intended for functions which wrap a command-line tool,
    i.e. where some inputs/outputs need to be specified as file names.


    **Inputs**


    Any arguments which are not of type ``Thing`` are passed through to the
    decorated function unmodified.  Arguments which are of type ``Thing`` are
    saved to a temporary file, and the name of that file is passed to the
    function.


    **Outputs**


    If an argument is given the special :data:`LOAD` value, it is assumed
    to be an output argument. In this case, it is replaced with a temporary
    file name then, after the function has completed, that file is loaded
    into memory, and the value returned (along with the function's output,
    and any other arguments with a value of ``LOAD``).


    **Return value**


    Functions decorated with a ``_FileOrThing`` decorator will always return a
    ``dict``-like object, where the function's actual return value is
    accessible via an attribute called `output`. All output arguments with a
    value of ``LOAD`` will be present as dictionary entries, with the keyword
    argument names used as keys. Any ``LOAD``ed output arguments which were not
    generated by the function will not be present in the dictionary.


    **Example**


    As an example of using the ``fileOrArray`` decorator on a function
    which concatenates two files containing affine transformations, and
    saves the output to a file::

        # if atob, btoc, or output are passed
        # in as arrays, they are converted to
        # file names.
        @fileOrArray('atob', 'btoc', 'output')
        def concat(atob, btoc, output=None):

            # inputs are guaranteed to be files
            atob = np.loadtxt(atob)
            btoc = np.loadtxt(atoc)

            atoc = np.dot(btoc, atob)

            if output is not None:
                np.savetxt(output, atoc)

            return 'Done'


    Because we have decorated the ``concat`` function with :func:`fileToArray`,
    it can be called with either file names, or Numpy arrays::


        # All arguments are passed through
        # unmodified - the output will be
        # saved to a file called atoc.mat.
        concat('atob.txt', 'btoc.txt', 'atoc.mat')

        # The function's return value
        # is accessed via an attribute called
        # "output" on the dict
        assert concat('atob.txt', 'btoc.txt', 'atoc.mat').output == 'Done'

        # Outputs to be loaded into memory
        # are returned in a dictionary,
        # with argument names as keys.
        atoc = concat('atob.txt', 'btoc.txt', LOAD)['atoc']

        # In-memory inputs are saved to
        # temporary files, and those file
        # names are passed to the concat
        # function.
        atoc = concat(np.diag([2, 2, 2, 0]),
                      np.diag([3, 3, 3, 3]), LOAD)['atoc']


    **Using with other decorators**


    ``_FileOrThing`` decorators can be chained with other ``_FileOrThing``
    decorators, and other decorators.  When multiple ``_FileOrThing``
    decorators are used on a single function, the outputs from each decorator
    are merged together into a single dict-like object.


    ``_FileOrThing`` decorators can be used with any other decorators
    **as long as** they do not manipulate the return value, and as long as
    the ``_FileOrThing`` decorators are adjacent to each other.
    """


    class _Results(dict):
        """A custom ``dict`` type used to return outputs from a function
        decorated with ``_FileOrThing``. All outputs are stored as dictionary
        items, with the argument name as key, and the output object (the
        "thing") as value.

        The decorated function's actual return value is accessible via the
        :meth:`output` property.
        """
        def __init__(self, output):
            self.__output = output

        @property
        def output(self):
            """Access the return value of the decorated function. """
            return self.__output


    def __init__(self,
                 func,
                 prepIn,
                 prepOut,
                 load,
                 removeExt,
                 *args,
                 **kwargs):
        """Initialise a ``_FileOrThing`` decorator.

        :arg func:      The function to be decorated.

        :arg prepIn:    Function which returns a file name to be used in
                        place of an input argument.

        :arg prepOut:   Function which generates a file name to use for
                        arguments that were set to :data:`LOAD`.

        :arg load:      Function which is called to load items for arguments
                        that were set to :data:`LOAD`. Must accept a file path
                        as its sole argument.

        :arg removeExt: Function which can remove a file extension from a file
                        path.

        :arg outprefix: Must be passed as a keyword argument. The name of a
                        positional or keyword argument to the function, which
                        specifies an output file name prefix.  All other
                        arguments with names that begin with this prefix may
                        be interpreted as things to ``LOAD``.

        All other positional arguments are interpreted as the names of the
        arguments to the function which will be handled by this
        ``_FileOrThing`` decorator. If not provided, *all* arguments passed to
        the function will be handled.


        The ``prepIn`` and ``prepOut`` functions must accept the following
        positional arguments:

          - A directory in which all temporary input/output files should be
            stored

          - The name of the keyword argument to be processed

          - The argument value that was passed in
        """
        self.__func      = func
        self.__prepIn    = prepIn
        self.__prepOut   = prepOut
        self.__load      = load
        self.__removeExt = removeExt
        self.__things    = args
        self.__outprefix = kwargs.get('outprefix', None)


    def __call__(self, *args, **kwargs):
        """Function which calls ``func``, ensuring that any arguments of
        type ``Thing`` are saved to temporary files, and any arguments
        with the value :data:`LOAD` are loaded and returned.

        All other arguments are passed through to ``func``.
        """

        func     = self.__func
        argnames = namedPositionals(func, args)

        # If this _FileOrThing is being called
        # by another _FileOrThing don't create
        # another working directory. We do this
        # sneakily, by setting an attribute on
        # the wrapped function which stores the
        # current working directory.
        wrapped     = _unwrap(func)
        fot_workdir = getattr(wrapped, '_fot_workdir', None)
        parent      = fot_workdir is None

        # Create a tempdir to store any temporary
        # input/output things, but don't change
        # into it, as file paths passed to the
        # function may be relative.
        with tempdir.tempdir(changeto=False, override=fot_workdir) as td:

            log.debug('Redirecting LOADed outputs to %s', td)

            # Replace any things with file names.
            # Also get a list of LOAD outputs
            args = self.__prepareArgs(parent, td, argnames, args, kwargs)
            args, kwargs, outprefix, outfiles, prefixes = args

            # The prefix/patterns may be
            # overridden by a parent FoT
            outprefix = getattr(wrapped, '_fot_outprefix', outprefix)
            prefixes  = getattr(wrapped, '_fot_prefixes',  prefixes)

            # if there are any other FileOrThings
            # in the decorator chain, get them to
            # use our working directory, and
            # prefixes, instead of creating their
            # own.
            if parent:
                setattr(wrapped, '_fot_workdir',   td)
                setattr(wrapped, '_fot_outprefix', outprefix)
                setattr(wrapped, '_fot_prefixes',  prefixes)

            # Call the function
            try:
                result = func(*args, **kwargs)

            finally:
                # if we're the top-level FileOrThing
                # decorator, remove the attributes we
                # added above.
                if parent:
                    delattr(wrapped, '_fot_workdir')
                    delattr(wrapped, '_fot_outprefix')
                    delattr(wrapped, '_fot_prefixes')

            return self.__generateResult(
                td, result, outprefix, outfiles, prefixes)


    def __prepareArgs(self, parent, workdir, argnames, args, kwargs):
        """Prepares all input and output arguments to be passed to the
        decorated function. Any arguments with a value of :data:`LOAD` are
        passed to the ``prepOut`` function specified at :meth:`__init__`.
        All other arguments are passed through the ``prepIn`` function.

        :arg parent:  ``True`` if this ``_FileOrThing`` is the first in a
                      chain of ``_FileOrThing`` decorators.

        :arg workdir: Directory in which all temporary files should be stored.

        :arg args:    Positional arguments to be passed to the decorated
                      function.

        :arg kwargs:  Keyword arguments to be passed to the decorated function.

        :returns:     A tuple containing:

                        - An updated copy of ``args``.

                        - An updated copy of ``kwargs``.

                        - The output file prefix that was actually passed in
                          (it is subsequently modified so that prefixed outputs
                          are redirected to a temporary location). All prefixed
                          outputs that are not ``LOAD``ed should be moved into
                          this directory. ``None`` if there is no output
                          prefix.

                        - A dictionary of ``{ name : filename }`` mappings,
                          for all arguments with a value of ``LOAD``.

                        - A dictionary   ``{ filepat : replstr }`` paths, for
                          all output-prefix arguments with a value of ``LOAD``.
        """

        # These containers keep track
        # of output files which are to
        # be loaded into memory
        outfiles      = dict()
        prefixedFiles = dict()

        allargs  = {k : v for k, v in zip(argnames, args)}
        allargs.update(kwargs)

        # Has an output prefix been specified?
        prefix     = allargs.get(self.__outprefix, None)
        realPrefix = None

        # Prefixed outputs are only
        # managed by the parent
        # _FileOrthing in a chain of
        # FoT decorators.
        if not parent:
            prefix = None

        # If so, replace it with a new output
        # prefix which will redirect all output
        # to the temp dir.
        #
        # Importantly, here we assume that the
        # underlying function (and hence the
        # underlying command-line tool) will
        # accept an output prefix which contains
        # a directory path.
        if prefix is not None:

            # If prefix is set to LOAD,
            # all generated output files
            # should be loaded - we use a
            # randomly generated prefix,
            # and add it to prefixedFiles,
            # so that every file which
            # starts with it will be
            # loaded.
            if prefix is LOAD:
                prefix                = random.sample(string.ascii_letters, 10)
                prefix                = ''.join(prefix)
                prefixedFiles[prefix] = self.__outprefix

            realPrefix                = prefix
            fakePrefix                = op.join(workdir, prefix)
            allargs[self.__outprefix] = fakePrefix

            log.debug('Replacing output prefix: %s -> %s',
                      realPrefix, fakePrefix)

            # If the prefix specifies a
            # directory, make sure it
            # exists (remember that we're
            # in a temporary directory)
            pdir = op.dirname(fakePrefix)
            if pdir != '' and not op.exists(pdir):
                os.makedirs(pdir)

        if len(self.__things) > 0: things = self.__things
        else:                      things = allargs.keys()

        for name, val in list(allargs.items()):

            # don't process the
            # outprefix argument
            if name == self.__outprefix:
                continue

            # is this argument referring
            # to a prefixed output?
            isprefixed = (prefix is not None and
                          name.startswith(prefix))

            if not (isprefixed or name in things):
                continue

            # Prefixed output files may only
            # be given a value of LOAD
            if isprefixed and val is not LOAD:
                raise ValueError('Cannot specify name of prefixed file - the '
                                 'name is defined by the output prefix: '
                                 '{}'.format(name))

            if val is LOAD:

                # this argument refers to an output
                # that is generated from the output
                # prefix argument, and doesn't map
                # directly to an argument of the
                # function. So we don't pass it
                # through.
                if isprefixed:
                    prefixedFiles[name] = name
                    allargs.pop(name)

                # regular output-file argument
                else:
                    outfile = self.__prepOut(workdir, name, val)
                    outfiles[name] = outfile
                    allargs[ name] = outfile

            # Assumed to be an input file
            else:
                # sequences may be
                # accepted for inputs
                if isinstance(val, (list, tuple)):
                    infile = list(val)
                    for i, v in enumerate(val):
                        v = self.__prepIn(workdir, name, v)
                        if v is not None:
                            infile[i] = v

                else:
                    infile = self.__prepIn(workdir, name, val)

                if infile is not None:
                    allargs[name] = infile

        if realPrefix is not None and len(prefixedFiles) == 0:
            allargs[self.__outprefix] = realPrefix

        args   = [allargs.pop(k) for k in argnames]
        kwargs = allargs

        return args, kwargs, realPrefix, outfiles, prefixedFiles


    def __generateResult(
            self, workdir, result, outprefix, outfiles, prefixes):
        """Loads function outputs and returns a :class:`_Results` object.

        Called by :meth:`__call__` after the decorated function has been
        called. Figures out what files should be loaded, and loads them into
        a ``_Results`` object.

        :arg workdir:   Directory which contains the function outputs.
        :arg result:    Function return value.
        :arg outprefix: Original output prefix that was passed into the
                        function (or ``None`` if one wasn't passed)
        :arg outfiles:  Dictionary containing output files to be loaded (see
                        :meth:`__prepareArgs`).
        :arg prefixes:  Dictionary containing output-prefix patterns to be
                        loaded (see :meth:`__prepareArgs`).

        :returns:       A ``_Results`` object containing all loaded outputs.
        """

        # make a _Results object to store
        # the output. If we are decorating
        # another _FileOrThing, the
        # results will get merged together
        # into a single _Results dict.
        if not isinstance(result, _FileOrThing._Results):
            result = _FileOrThing._Results(result)

        # Load the LOADed outputs
        for oname, ofile in outfiles.items():

            log.debug('Loading output %s: %s', oname, ofile)

            if op.exists(ofile): oval = self.__load(ofile)
            else:                oval = None

            result[oname] = oval

        # No output prefix - we're done
        if outprefix is None or len(prefixes) == 0:
            return result

        # Load or move output-prefixed files.
        # Find all files with a name that
        # matches the prefix that was passed
        # in (recursing into matching sub-
        # directories too).
        allPrefixed = glob.glob(op.join(workdir, '{}*'.format(outprefix)))
        allPrefixed = [fslpath.allFiles(f) if op.isdir(f) else [f]
                       for f in allPrefixed]

        for prefixed in it.chain(*allPrefixed):
            fullpath = prefixed
            prefixed = op.relpath(prefixed, workdir)
            for prefPat, prefName in prefixes.items():
                if not fnmatch.fnmatch(prefixed, '{}*'.format(prefPat)):
                    continue

                log.debug('Loading prefixed output %s [%s]: %s',
                          prefPat, prefName, prefixed)

                # if the load function returns
                # None, this file is probably
                # not of the correct type.
                fval = self.__load(fullpath)
                if fval is not None:
                    noext = self.__removeExt(prefixed)
                    prefPat  = prefPat.replace('\\', '\\\\')
                    noext = re.sub('^' + prefPat, prefName, noext)
                    # If there is already an item in result with the
                    # name (stripped of prefix), then instead store
                    # the result with the full prefixed name
                    if noext not in result:
                        result[noext] = fval
                    else:
                        withext = re.sub('^' + prefPat, prefName, prefixed)
                        result[withext] = fval
                    break

        return result


def fileOrImage(*args, **kwargs):
    """Decorator which can be used to ensure that any NIfTI images are saved
    to file, and output images can be loaded and returned as ``nibabel``
    image objects or :class:`.Image` objects.
    """

    # keep track of the input argument
    # types on each call, so we know
    # whether to return a fsl.Image or
    # a nibabel image
    intypes = []

    def prepIn(workdir, name, val):

        infile = None

        if isinstance(val, fslimage.Image):
            intypes.append(fslimage.Image)

        elif isinstance(val, nib.nifti1.Nifti1Image):
            intypes.append(nib.nifti1.Nifti1Image)

        if isinstance(val, fslimage.Image):
            val = val.nibImage

        if isinstance(val, nib.nifti1.Nifti1Image):
            infile = val.get_filename()

            # in-memory image - we have
            # to save it out to a file
            if infile is None:
                hd, infile = tempfile.mkstemp(fslimage.defaultExt())
                os.close(hd)
                val.to_filename(infile)

        return infile

    def prepOut(workdir, name, val):
        return op.join(workdir, '{}.nii.gz'.format(name))

    def load(path):

        if not fslimage.looksLikeImage(path):
            return None

        # create an independent in-memory
        # copy of the image file
        img = nib.load(path, mmap=False)

        # if any arguments were fsl images,
        # that takes precedence.
        if fslimage.Image in intypes:
            return fslimage.Image(img.get_data(), header=img.header)
        # but if all inputs were file names,
        # nibabel takes precedence
        elif nib.nifti1.Nifti1Image in intypes or len(intypes) == 0:
            return nib.nifti1.Nifti1Image(img.get_data(), None, img.header)

        # this function should not be called
        # under any other circumstances
        else:
            raise RuntimeError('Cannot handle type: {}'.format(intypes))

    def decorator(func):
        fot = _FileOrThing(func,
                           prepIn,
                           prepOut,
                           load,
                           fslimage.removeExt,
                           *args,
                           **kwargs)

        def wrapper(*args, **kwargs):
            result = fot(*args, **kwargs)
            intypes[:] = []
            return result

        return _update_wrapper(wrapper, func)

    return decorator


def fileOrArray(*args, **kwargs):
    """Decorator which can be used to ensure that any Numpy arrays are saved
    to text files, and output files can be loaded and returned as Numpy arrays.
    """

    def prepIn(workdir, name, val):

        infile = None

        if isinstance(val, np.ndarray):
            hd, infile = tempfile.mkstemp('.txt')
            os.close(hd)
            np.savetxt(infile, val, fmt='%0.18f')

        return infile

    def prepOut(workdir, name, val):
        return op.join(workdir, '{}.txt'.format(name))

    def load(path):
        try:              return np.loadtxt(path)
        except Exception: return None

    def decorator(func):
        fot = _FileOrThing(func,
                           prepIn,
                           prepOut,
                           load,
                           fslpath.removeExt,
                           *args,
                           **kwargs)

        def wrapper(*args, **kwargs):
            return fot(*args, **kwargs)

        return _update_wrapper(wrapper, func)

    return decorator


def fileOrText(*args, **kwargs):
    """Decorator which can be used to ensure that any text output (e.g. log
    file) are saved to text files, and output files can be loaded and returned
    as strings.
    """

    def prepIn(workdir, name, val):

        infile = None

        if isinstance(val, six.string_types):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt') as f:
                f.write(val)
                infile = f.name
        return infile

    def prepOut(workdir, name, val):
        return op.join(workdir, '{}.txt'.format(name))

    def load(path):
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception: return None

    def decorator(func):
        fot = _FileOrThing(func,
                           prepIn,
                           prepOut,
                           load,
                           fslpath.removeExt,
                           *args,
                           **kwargs)

        def wrapper(*args, **kwargs):
            return fot(*args, **kwargs)

        return _update_wrapper(wrapper, func)

    return decorator
