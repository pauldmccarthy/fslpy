#!/usr/bin/env python
#
# wrapperutils.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            inspect
import            tempfile
import            warnings
import            functools
import            collections

import            six
import nibabel as nib

import fsl.utils.tempdir as tempdir
import fsl.data.image    as fslimage


class _BooleanFlag(object):
    def __init__(self, show):
        self.show = show
    def __eq__(self, other):
        return type(other) == type(self) and self.show == other.show


SHOW_IF_TRUE = _BooleanFlag(True)
HIDE_IF_TRUE = _BooleanFlag(False)


def applyArgStyle(style, argmap=None, valmap=None, **kwargs):

    def fmtarg(arg, style):
        if   style in ('-',  '-='):  arg =  '-{}'.format(arg)
        elif style in ('--', '--='): arg = '--{}'.format(arg)
        return arg

    def fmtval(val, style=None):
        if     isinstance(val, collections.Sequence) and \
           not isinstance(val, six.string_types):
            return ' '.join([str(v) for v in val])
        else:
            return str(val)

    if style not in ('-', '--', '-=', '--='):
        raise ValueError('Invalid style: {}'.format(style))

    args = []

    for k, v in kwargs.items():

        k    = argmap.get(k, k)
        mapv = valmap.get(k, fmtval(v, style))
        k    = fmtarg(k, style)

        if mapv in (SHOW_IF_TRUE, HIDE_IF_TRUE):
            if v == mapv.show:
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
        def wrapper(**kwargs):
            for reqarg in reqargs:
                assert reqarg in kwargs
            return func(**kwargs)
        return wrapper
    return decorator


def argsToKwargs(func, args):
    """Given a function, and a sequence of positional arguments destined
    for that function, converts the positional arguments into a dict
    of keyword arguments. Used by the :class:`_FileOrImage` class.
    """
    # getfullargspec is the only way to get the names
    # of positional arguments in Python 2.x. It is
    # deprecated in python 3.5, but not in python 3.6.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        spec = inspect.getfullargspec(func)

    kwargs = collections.OrderedDict()
    for name, val in zip(spec.args, args):
        kwargs[name] = val

    return kwargs


RETURN = object()
"""
"""


class _FileOrImage(object):
    """

    Inputs:
      - In-memory nibabel images loaded from a file. The image is replaced with
        its file name.

      - In-memory nibabel images. The image is saved to a temporary file, and
        replaced with the temporary file's name. The file is deleted after the
        function has returned.

    Outputs:
      - File name:  The file name is passed straight through to the function.
      - ``RETURN``: A temporary file name is passed to the function. After the
        function has completed, the image is loaded into memory and the
        temporary file is deleted. The image is returned from the function
        call.
    """


    def __init__(self, *imgargs):
        """
        """
        self.__imgargs = imgargs


    def __call__(self, func):
        """
        """
        return functools.partial(self.__wrapper, func)


    def __wrapper(self, func, *args, **kwargs):
        """
        """

        kwargs.update(argsToKwargs(func, args))

        # Create a tempdir to store any temporary
        # input/output images, but don't change
        # into it, as file paths passed to the
        # function may be relative.
        with tempdir.tempdir(changeto=False) as td:

            kwargs, infiles, outfiles = self.__prepareArgs(td, kwargs)

            # Call the function
            result  = func(**kwargs)

            # Load the output images that
            # were specified as RETURN
            outimgs = []
            for of in outfiles:

                # output file didn't get created
                if not op.exists(of):
                    oi = None

                # load the file, and create
                # an in-memory copy (the file
                # is going to get deleted)
                else:
                    oi = nib.load(of)
                    oi = nib.nifti1.Nifti1Image(oi.get_data(), None, oi.header)

                outimgs.append(oi)

            return tuple([result] + outimgs)


    def __prepareArgs(self, workdir, kwargs):
        """
        """

        kwargs   = dict(kwargs)
        infiles  = []
        outfiles = []

        for imgarg in self.__imgargs:

            img = kwargs.get(imgarg, None)

            # Not specified, nothing to do
            if img is None:
                continue

            # This is an input image which has
            # been specified as an in-memory
            # nibabel image. if the image has
            # a backing file, replace the image
            # object with the file name.
            # Otherwise, save the image out to
            # a temporary file, and replace the
            # image with the file name.
            if isinstance(img, nib.nifti1.Nifti1Image):
                imgfile = img.get_filename()

                # in-memory image - we have
                # to save it out to a file
                if imgfile is None:

                    hd, imgfile = tempfile.mkstemp(fslimage.defaultExt())

                    os.close(hd)
                    img.to_filename(imgfile)
                    infiles.append(imgfile)

                # replace the image with its
                # file name
                kwargs[img] = imgfile

            # This is an output image, and the
            # caller has requested that it be
            # returned from the function call
            # as an in-memory image.
            if img == RETURN:
                kwargs[imgarg] = '{}.nii.gz'.format(imgarg)
                outfiles.append(imgarg)

        return kwargs, infiles, outfiles


fileOrImage = _FileOrImage
