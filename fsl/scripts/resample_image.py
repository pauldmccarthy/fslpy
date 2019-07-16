#!/usr/bin/env python
#
# resample_image.py - Script to resample an image
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the ``resample_image`` script, for resampling
a NIfTI image.
"""


import textwrap as tw
import             sys
import             argparse

import numpy    as np

import fsl.utils.parse_data     as parse_data
import fsl.utils.image.resample as resample
import fsl.data.image           as fslimage


def intlist(val):
    """Turn a string of comma-separated ints into a list of ints. """
    return [int(v) for v in val.split(',')]


def floatlist(val):
    """Turn a string of comma-separated floats into a list of floats. """
    return [float(v) for v in val.split(',')]


def sanitiseList(parser, vals, img, arg):
    """Make sure that ``vals`` has the same number of elements as ``img`` has
    dimensions. Used to sanitise the ``--shape`` and ``--dim`` options.
    """

    if vals is None:
        return vals

    nvals = len(vals)

    if nvals < 3:
        parser.error('At least three values are '
                     'required for {}'.format(arg))

    if nvals > img.ndim:
        parser.error('Input only has {} dimensions - too many values '
                     'specified for {}'.format(img.ndim, arg))

    if nvals < img.ndim:
        vals = list(vals) + list(img.shape[nvals:])

    return vals


ARGS = {
    'input'     : ('input',),
    'output'    : ('output',),
    'shape'     : ('-s',  '--shape'),
    'dim'       : ('-d',  '--dim'),
    'reference' : ('-r',  '--reference'),
    'interp'    : ('-i',  '--interp'),
    'origin'    : ('-o',  '--origin'),
    'dtype'     : ('-dt', '--dtype'),
    'smooth'    : ('-n',  '--nosmooth')}


OPTS = {
    'input'     : dict(type=parse_data.Image),
    'output'    : dict(type=parse_data.ImageOut),
    'reference' : dict(type=parse_data.Image, metavar='IMAGE'),
    'shape'     : dict(type=intlist,   metavar=('X,Y,Z,...')),
    'dim'       : dict(type=floatlist, metavar=('X,Y,Z,...')),
    'interp'    : dict(choices=('nearest', 'linear', 'cubic'),
                       default='linear'),
    'origin'    : dict(choices=('centre', 'corner'), default='centre'),
    'dtype'     : dict(choices=('char', 'short', 'int', 'float', 'double')),
    'smooth'    : dict(dest='smooth', action='store_false')}


HELPS = {
    'input'     : 'Input image',
    'output'    : 'Output image',
    'shape'     : 'Output shape',
    'dim'       : 'Output voxel dimensions',
    'reference' : 'Resample input to the space of this reference image'
                  '(overrides --origin)',
    'interp'    : 'Interpolation (default: linear)',
    'origin'    : 'Resampling origin (default: centre)',
    'dtype'     : 'Data type (default: data type of input image)',
    'smooth'    : 'Do not smooth image when downsampling'}


DESC = tw.dedent("""
Resample an image to different dimensions.
""").strip()


DEST_DESC = tw.dedent("""
Specify the resampling destination space using one of the following
options. Note that the --reference option will cause the field-of-view
of the input image to be changed to that of the reference image.
""").strip()


USAGE = 'resample_image (--shape|--dim|--reference) [options] input output'


INTERPS = {'nearest' : 0,
           'linear'  : 1,
           'cubic'   : 3}
DTYPES  = {'char'    : np.uint8,
           'short'   : np.int16,
           'int'     : np.int32,
           'float'   : np.float32,
           'double'  : np.float64}


def parseArgs(argv):
    """Parses command-line arguments.

    :arg argv: Sequence of command-line arguments
    :returns:  An ``argparse.Namespace`` object containing parsed arguments.
    """

    parser = argparse.ArgumentParser(prog='resample_image',
                                     usage=USAGE,
                                     description=DESC)
    dest   = parser.add_argument_group('Resampling destination', DEST_DESC)
    dest   = dest.add_mutually_exclusive_group(required=True)

    for a in ('input', 'output', 'interp', 'origin',
              'dtype', 'smooth'):
        parser.add_argument(*ARGS[a], help=HELPS[a], **OPTS[a])

    for a in ('shape', 'dim', 'reference'):
        dest.add_argument(*ARGS[a], help=HELPS[a], **OPTS[a])

    if len(argv) == 0:
        parser.print_help()
        sys.exit(0)

    args        = parser.parse_args(argv)
    args.interp = INTERPS[   args.interp]
    args.dtype  = DTYPES.get(args.dtype, args.input.dtype)
    args.shape  = sanitiseList(parser, args.shape, args.input, 'shape')
    args.dim    = sanitiseList(parser, args.dim,   args.input, 'dim')

    if (args.reference is not None) and \
       (args.input.ndim     > 3)    and \
       (args.reference.ndim > 3):
        print('Reference and image are both >3D - only '
              'resampling along the spatial dimensions.')

    return args


def main(argv=None):
    """Entry point for ``resample_image``. Parses arguments, resamples the
    input image, and saves it to the specified output file.

    :arg argv: Sequence of command-line arguments. If not provided, taken
               from ``sys.argv``.
    """

    if argv is None:
        argv = sys.argv[1:]

    args      = parseArgs(argv)
    reskwargs = {
        'dtype'  : args.dtype,
        'order'  : args.interp,
        'smooth' : args.smooth,
        'origin' : args.origin}

    # One of these is guaranteed to be set
    if args.shape is not None:
        func    = resample.resample
        resargs = (args.input, args.shape)

    elif args.dim is not None:
        func    = resample.resampleToPixdims
        resargs = (args.input, args.dim)

    elif args.reference is not None:
        func    = resample.resampleToReference
        resargs = (args.input, args.reference)

    resampled, xform = func(*resargs, **reskwargs)

    if args.reference is None:
        hdr = args.input.header
    else:
        hdr   = args.reference.header
        xform = None

    resampled = fslimage.Image(resampled, xform=xform, header=hdr)

    # Adjust the pixdims of the
    # higher dimensions if they
    # have been resampled
    if len(resampled.shape) > 3:

        oldPixdim = args.input.pixdim[3:]
        oldShape  = args.input.shape[ 3:]
        newShape  = resampled .shape[ 3:]

        for i, (p, o, n) in enumerate(zip(oldPixdim, oldShape, newShape), 4):
            resampled.header['pixdim'][i] = p * o / n

    resampled.save(args.output)

    return 0


if __name__ == '__main__':
    sys.exit(main())
