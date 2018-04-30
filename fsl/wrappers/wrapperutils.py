#!/usr/bin/env python
#
# wrapperutils.py - Functions and decorators used by the FSL wrapper
# functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions and decorators used by the FSL wrapper
functions.


The :func:`cmdwrapper` and :func:`fslwrapper` functions are conenience
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
files, and then the file names passed into the wrapper function. For exmaple::


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


import os.path as op
import            os
import            sys
import            inspect
import            tempfile
import            warnings
import            functools
import            collections

import            six
import nibabel as nib
import numpy   as np

import fsl.utils.tempdir as tempdir
import fsl.utils.run     as run
import fsl.data.image    as fslimage


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
        submit = kwargs.pop('submit', None)
        cmd = func(*args, **kwargs)
        return run.run(cmd, err=True, submit=submit)
    return _update_wrapper(wrapper, func)


def fslwrapper(func):
    """This decorator can be used on functions which generate a FSL command
    line. It will pass the return value of the function to the
    :func:`fsl.utils.run.runfsl` function in a standardised manner.
    """
    def wrapper(*args, **kwargs):
        submit = kwargs.pop('submit', None)
        cmd = func(*args, **kwargs)
        return run.runfsl(cmd, err=True, submit=submit)
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


def applyArgStyle(style, valsep=None, argmap=None, valmap=None, **kwargs):
    """Turns the given ``kwargs`` into command line options. This function
    is intended to be used to automatically generate command line options
    from arguments passed into a Python function.

    The ``style`` and ``valsep`` arguments control how key-value pairs
    are converted into command-line options:


    =========  ==========  ===========================
    ``style``  ``valsep``  Result
    =========  ==========  ===========================
    ``'-'``    ' '         ``-name val1 val2 val3``
    ``'-'``    '"'         ``-name "val1 val2 val3"``
    ``'-'``    ','         ``-name val1,val2,val3``
    ``'--'``   ' '         ``--name val1 val2 val3``
    ``'--'``   '"'         ``--name "val1 val2 val3"``
    ``'--'``   ','         ``--name val1,val2,val3``
    ``'-='``   ' '         Not supported
    ``'-='``   '"'         ``-name="val1 val2 val3"``
    ``'-='``   ','         ``-name=val1,val2,val3``
    ``'--='``  ' '         Not supported
    ``'--='``  '"'         ``--name="val1 val2 val3"``
    ``'--='``  ','         ``--name=val1,val2,val3``
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
        if   style in ('-',  '-='):  arg =  '-{}'.format(arg)
        elif style in ('--', '--='): arg = '--{}'.format(arg)
        return arg

    # always returns a sequence
    def fmtval(val):
        if     isinstance(val, collections.Sequence) and \
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
    **as long as** they do not manipulate the return value.
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


    def __init__(self, func, prepIn, prepOut, load, *things):
        """Initialise a ``_FileOrThing`` decorator.

        :arg func:    The function to be decorated.

        :arg prepIn:  Function which returns a file name to be used in
                      place of an input argument.

        :arg prepOut: Function which generates a file name to use for
                      arguments that were set to :data:`LOAD`.

        :arg load:    Function which is called to load items for arguments
                      that were set to :data:`LOAD`. Must accept a file path
                      as its sole argument.

        :arg things:  Names of all arguments which will be handled by
                      this ``_FileOrThing`` decorator. If not provided,
                      *all* arguments passed to the function will be
                      handled.

        The ``prepIn`` and ``prepOut`` functions must accept the following
        positional arguments:

          - A directory in which all temporary input/output files should be
            stored

          - The name of the keyword argument to be processed

          - The argument value that was passed in
        """
        self.__func    = func
        self.__prepIn  = prepIn
        self.__prepOut = prepOut
        self.__load    = load
        self.__things  = things


    def __call__(self, *args, **kwargs):
        """Function which calls ``func``, ensuring that any arguments of
        type ``Thing`` are saved to temporary files, and any arguments
        with the value :data:`LOAD` are loaded and returned.

        All other arguments are passed through to ``func``.
        """

        func     = self.__func
        argnames = namedPositionals(func, args)

        # Create a tempdir to store any temporary
        # input/output things, but don't change
        # into it, as file paths passed to the
        # function may be relative.
        with tempdir.tempdir(changeto=False) as td:

            # Replace any things with file names.
            # Also get a list of LOAD outputs
            args, kwargs, outfiles = self.__prepareArgs(
                td, argnames, args, kwargs)

            # Call the function
            result = func(*args, **kwargs)

            # make a _Reults object to store
            # the output. If we are decorating
            # another _FileOrThing, the
            # results will get merged together
            # into a single _Results dict.
            if not isinstance(result, _FileOrThing._Results):
                result = _FileOrThing._Results(result)

            # Load the LOADed outputs
            for oname, ofile in outfiles.items():

                if not op.exists(ofile): oval = None
                else:                    oval = self.__load(ofile)

                result[oname] = oval

            return result


    def __prepareArgs(self, workdir, argnames, args, kwargs):
        """Prepares all input and output arguments to be passed to the
        decorated function. Any arguments with a value of :data:`LOAD` are
        passed to the ``prepOut`` function specified at :meth:`__init__`.
        All other arguments are passed through the ``prepIn`` function.

        :arg workdir: Directory in which all temporary files should be stored.

        :arg args:    Positional arguments to be passed to the decorated
                      function.

        :arg kwargs:  Keyword arguments to be passed to the decorated function.

        :returns:     A tuple containing:

                        - An updated copy of ``args``.

                        - An updated copy of ``kwargs``.

                        - A dictionary of ``{ name : filename }`` mappings,
                          for all arguments with a value of ``LOAD``.
        """

        outfiles = dict()

        allargs  = {k : v for k, v in zip(argnames, args)}
        allargs.update(kwargs)

        if len(self.__things) > 0: things = self.__things
        else:                      things = allargs.keys()

        for name in things:

            val = allargs.get(name, None)

            if val is None:
                continue

            if val is LOAD:

                outfile = self.__prepOut(workdir, name, val)

                if outfile is not None:
                    allargs[ name] = outfile
                    outfiles[name] = outfile
            else:

                infile = self.__prepIn(workdir, name, val)

                if infile is not None:
                    allargs[name] = infile

        args   = [allargs.pop(k) for k in argnames]
        kwargs = allargs

        return args, kwargs, outfiles


def fileOrImage(*imgargs):
    """Decorator which can be used to ensure that any NIfTI images are saved
    to file, and output images can be loaded and returned as ``nibabel``
    image objects.
    """

    def prepIn(workdir, name, val):

        infile = None

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
        # create an independent in-memory
        # copy of the image file
        img = nib.load(path)
        return nib.nifti1.Nifti1Image(img.get_data(), None, img.header)

    def decorator(func):
        fot = _FileOrThing(func, prepIn, prepOut, load, *imgargs)

        def wrapper(*args, **kwargs):
            return fot(*args, **kwargs)

        return _update_wrapper(wrapper, func)

    return decorator


def fileOrArray(*arrargs):
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

    load = np.loadtxt

    def decorator(func):
        fot = _FileOrThing(func, prepIn, prepOut, load, *arrargs)

        def wrapper(*args, **kwargs):
            return fot(*args, **kwargs)

        return _update_wrapper(wrapper, func)

    return decorator
