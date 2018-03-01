#!/usr/bin/env python
#
# wrapperutils.py - Functions and decorators used by the FSL wrapper
# functions.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions and decorators used by the FSL wrapper
functions.

.. autosummary::
   :nosignatures:

   applyArgStyle
   required
   fileOrImage
   fileOrArray
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
import fsl.data.image    as fslimage


def _update_wrapper(wrapper, wrapped, *args, **kwargs):
    """Replacement for the built-in ``functools.update_wrapper``. This
    implementation ensures that the wrapper function has an attribute
    called ``__wrapped__``, which refers to the ``wrapped`` function.

    This behaviour is only required in Python versions < 3.4.
    """

    wrapper = functools.update_wrapper(wrapper, wrapped, *args, **kwargs)

    # Python >= 3.4 does things right
    if sys.version_info[0] * 10 + sys.version_info[1] < 3.4:
        wrapper.__wrapped__ = wrapped
    return wrapper


def _unwrap(func):
    """Replacement for the built-in ``inspect.unwrap`` function, which
    is not present in Python versions prior to 3.4.
    """

    # Python >= 3.4 has an inspect.unwrap function
    if sys.version_info[0] * 10 + sys.version_info[1] < 3.4:
        return inspect.unwrap(func)

    # Otherwise we follow the __wrapped__ chain ourselves
    if hasattr(func, '__wrapped__'):
        return _unwrap(func.__wrapped__)

    return func



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


def applyArgStyle(style, argmap=None, valmap=None, **kwargs):
    """Turns the given ``kwargs`` into command line options. This function
    is intended to be used to automatically generate command line options
    from arguments passed into a Python function.

    :arg style:  Controls how the ``kwargs`` are converted into command-line
                 options - must be one of the following:
                  - `'-'`: ``-name val``
                  - `'--'`: ``--name val``
                  - `'-='`: ``-name=val``
                  - `'--='`: ``--name=val``

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

    if style not in ('-', '--', '-=', '--='):
        raise ValueError('Invalid style: {}'.format(style))

    if argmap is None: argmap = {}
    if valmap is None: valmap = {}

    def fmtarg(arg):
        if   style in ('-',  '-='):  arg =  '-{}'.format(arg)
        elif style in ('--', '--='): arg = '--{}'.format(arg)
        return arg

    def fmtval(val):
        if     isinstance(val, collections.Sequence) and \
           not isinstance(val, six.string_types):
            return ' '.join([str(v) for v in val])
        else:
            return str(val)

    args = []

    for k, v in kwargs.items():

        k    = argmap.get(k, k)
        mapv = valmap.get(k, fmtval(v))
        k    = fmtarg(k)

        if (mapv is SHOW_IF_TRUE and     v) or \
           (mapv is HIDE_IF_TRUE and not v):
            args.append(k)

        elif '=' in style:
            args.append('{}={}'.format(k, mapv))
        else:
            args.extend((k, mapv))

    return args


def required(*reqargs):
    """Decorator which makes sure that all specified keyword arguments are
    present before calling the decorated function.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            kwargs = kwargs.copy()
            kwargs.update(argsToKwargs(func, args))
            for reqarg in reqargs:
                assert reqarg in kwargs
            return func(**kwargs)

        wrapper = _update_wrapper(wrapper, func)

        # If this is a bound method, make
        # sure that the instance is set on
        # the wrapper function - this is
        # needed by _FileOrThing decorators.
        if hasattr(func, '__self__'):
            wrapper.__self__ = func.__self__

        return wrapper

    return decorator


def argsToKwargs(func, args):
    """Given a function, and a sequence of positional arguments destined
    for that function, converts the positional arguments into a dict
    of keyword arguments. Used by the :class:`_FileOrThing` class.
    """

    func = _unwrap(func)

    # getargspec is the only way to get the names
    # of positional arguments in Python 2.x.
    if sys.version_info[0] < 3:
        argnames = inspect.getargspec(func).args

    # getargspec is deprecated in python 3.x
    else:

        # getfullargspec is deprecated in
        # python 3.5, but not in python 3.6.
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=DeprecationWarning)
            argnames = inspect.getfullargspec(func).args

    kwargs = collections.OrderedDict()
    for name, val in zip(argnames, args):
        kwargs[name] = val

    return kwargs


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
    tuple, where the first element is the function's actual return value. The
    remainder of the tuple will contain any arguments that were given the
    special ``LOAD`` value. ``None`` is returned for any ``LOAD`` arguments
    corresponded to output files that were not generated by the function.


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


    Because we have decorated the ``concat`` function with :func:`fileToArray`,
    it can be called with either file names, or Numpy arrays::

        # All arguments are passed through
        # unmodified - the output will be
        # saved to a file called atoc.mat
        concat('atob.txt', 'btoc.txt', 'atoc.mat')

        # The output is returned as a numpy
        # array (in a tuple with the concat
        # function's return value)
        atoc = concat('atob.txt', 'btoc.txt', LOAD)[1]

        # The inputs are saved to temporary
        # files, and those file names are
        # passed to the concat function.
        atoc = concat(np.diag([2, 2, 2, 0]), np.diag([3, 3, 3, 3]), LOAD)[1]
    """


    def __init__(self, prepareThing, loadThing, *things):
        """Initialise a ``_FileOrThing`` decorator.

        :arg prepareThing: Function which
        :arg loadThing:    Function which is called for arguments that
                           were set to :data:`LOAD`.

        :arg things:
        """
        self.__prepareThing = prepareThing
        self.__loadThing    = loadThing
        self.__things       = things


    def __call__(self, func):
        """Creates and returns the real decorator function. """

        isFOT   = isinstance(getattr(func, '__self__', None), _FileOrThing)
        wrapper = functools.partial(self.__wrapper, func, isFOT)

        # TODO
        wrapper = _update_wrapper(wrapper, func)
        wrapper.__self__ = self

        return wrapper


    def __wrapper(self, func, isFileOrThing, *args, **kwargs):
        """Function which wraps ``func``, ensuring that any arguments of
        type ``Thing`` are saved to temporary files, and any arguments
        with the value :data:`LOAD` are loaded and returned.

        :arg func:          The func being wrapped.

        :arg isFileOrThing: Set to ``True`` if ``func`` is a wrapper metho
                            of another ``_FileOrThing`` instance. In this case,
                            the output arguments will be flattenedinto a single
                            tuple.
        """

        kwargs = kwargs.copy()
        kwargs.update(argsToKwargs(func, args))

        # Create a tempdir to store any temporary
        # input/output things, but don't change
        # into it, as file paths passed to the
        # function may be relative.
        with tempdir.tempdir(changeto=False) as td:

            kwargs, infiles, outfiles = self.__prepareThings(td, kwargs)

            # Call the function
            result = func(**kwargs)

            # Load the output things that
            outthings = []
            for of in outfiles:
            # were specified as LOAD

                # output file didn't get created
                if not op.exists(of):
                    ot = None

                # load the thing
                else:
                    ot = self.__loadThing(of)

                outthings.append(ot)

            if isFileOrThing:
                things = result[1:]
                result = result[0]
                return tuple([result] + list(things) + outthings)
            else:
                return tuple([result] + outthings)


    def __prepareThings(self, workdir, kwargs):
        """
        """

        kwargs   = dict(kwargs)
        infiles  = []
        outfiles = []

        for tname in self.__things:

            tval = kwargs.get(tname, None)

            if tval is None:
                continue

            tval, infile, outfile = self.__prepareThing(workdir, tname, tval)

            if infile  is not None: infiles .append(infile)
            if outfile is not None: outfiles.append(outfile)

            kwargs[tname] = tval

        return kwargs, infiles, outfiles


def fileOrImage(*imgargs):
    """Decorator which can be used to ensure that any NIfTI images are saved
    to file, and output images can be loaded and returned as ``nibabel``
    image objects.
    """

    def prepareArg(workdir, name, val):

        newval  = val
        infile  = None
        outfile = None

        # This is an input image which has
        # been specified as an in-memory
        # nibabel image. if the image has
        # a backing file, replace the image
        # object with the file name.
        # Otherwise, save the image out to
        # a temporary file, and replace the
        # image with the file name.
        if isinstance(val, nib.nifti1.Nifti1Image):
            imgfile = val.get_filename()

            # in-memory image - we have
            # to save it out to a file
            if imgfile is None:

                hd, imgfile = tempfile.mkstemp(fslimage.defaultExt())

                os.close(hd)
                val.to_filename(imgfile)
                infile = imgfile

            # replace the image with its
            # file name
            newval = imgfile

        # This is an output image, and the
        # caller has requested that it be
        # returned from the function call
        # as an in-memory image.
        elif val == LOAD:
            newval  = op.join(workdir, '{}.nii.gz'.format(name))
            outfile = newval

        return newval, infile, outfile

    def loadImage(path):
        # create an independent in-memory
        # copy of the image file
        img = nib.load(path)
        return nib.nifti1.Nifti1Image(img.get_data(), None, img.header)

    return _FileOrThing(prepareArg, loadImage, *imgargs)


def fileOrArray(*arrargs):
    """Decorator which can be used to ensure that any Numpy arrays are saved
    to text files, and output files can be loaded and returned as Numpy arrays.
    """

    def prepareArg(workdir, name, val):

        newval  = val
        infile  = None
        outfile = None

        # Input has been provided as a numpy
        # array - save it to a file, and
        # replace the argument with the file
        # name
        if isinstance(val, np.ndarray):

            hd, arrfile = tempfile.mkstemp('.txt')

            os.close(hd)

            np.savetxt(arrfile, val, fmt='%0.18f')
            newval = arrfile

        # This is an output, and the caller has
        # requested that it be returned from the
        # function call as an in-memory array.
        elif val == LOAD:
            newval  = op.join(workdir, '{}.txt'.format(name))
            outfile = newval

        return newval, infile, outfile

    return _FileOrThing(prepareArg, np.loadtxt, *arrargs)
