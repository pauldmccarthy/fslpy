#!/usr/bin/env python
#
# fsl_apply_x5.py - Apply an X5 transformation to an image.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The ``fsl_apply_x5`` script can be used to apply an X5 transformation file
to resample an image.
"""


import functools as ft
import              sys
import              argparse

import fsl.transform.x5         as x5
import fsl.transform.nonlinear  as nonlinear
import fsl.utils.parse_data     as parse_data
import fsl.utils.image.resample as resample
import fsl.data.image           as fslimage


def parseArgs(args):
    """Parses command-line arguments.

    :arg args: Sequence of command-line arguments. If ``None``, ``sys.argv``
               is used
    :returns:  An ``argparse.Namespace`` object containing parsed arguments
    """

    parser = argparse.ArgumentParser('fsl_apply_x5')
    flags  = {
        'input'  : ('input',),
        'xform'  : ('xform',),
        'output' : ('output',),
        'interp' : ('-i', '--interp'),
        'ref'    : ('-r', '--ref'),
    }

    helps  = {
        'input'  : 'Input image',
        'xform'  : 'X5 transformation file',
        'output' : 'Output image',
        'interp' : 'Interpolation (default: linear)',
        'ref'    : 'Alternate reference image (default: '
                   'reference specified in X5 file)',
    }
    opts = {
        'input'  : dict(help=helps['input'],
                        type=parse_data.Image),
        'xform'  : dict(help=helps['xform']),
        'output' : dict(help=helps['output'],
                        type=parse_data.ImageOut),
        'interp' : dict(help=helps['interp'],
                        choices=('nearest', 'linear', 'cubic'),
                        default='linear'),
        'ref'    : dict(help=helps['ref'],
                        type=ft.partial(parse_data.Image, loadData=False)),
    }

    parser.add_argument(*flags['input'],  **opts['input'])
    parser.add_argument(*flags['xform'],  **opts['xform'])
    parser.add_argument(*flags['output'], **opts['output'])
    parser.add_argument(*flags['interp'], **opts['interp'])
    parser.add_argument(*flags['ref'],    **opts['ref'])

    if len(args) == 0:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args(args)

    if   args.interp == 'nearest': args.interp = 0
    elif args.interp == 'linear':  args.interp = 1
    elif args.interp == 'cubic':   args.interp = 3

    return args


def applyLinear(args):
    """Applies a linear X5 transformation file to the input.

    :arg args: ``argparse.Namespace`` object
    :returns:  The transformed input as an :class:`.Image` object
    """

    input           = args.input
    xform, src, ref = x5.readLinearX5(args.xform)

    if args.ref is not None:
        ref = args.ref

    res, xform = resample.resampleToReference(input,
                                              ref,
                                              matrix=xform,
                                              order=args.interp)

    return fslimage.Image(res, xform=xform, header=ref.header)


def applyNonlinear(args):
    """Applies a non-linear X5 transformation file to the input.

    :arg args: ``argparse.Namespace`` object
    :returns:  The transformed input as an :class:`.Image` object
    """

    field = x5.readNonLinearX5(args.xform)

    if args.ref is None: ref = field.ref
    else:                ref = args.ref

    result = nonlinear.applyDeformation(args.input,
                                        field,
                                        ref=ref,
                                        order=args.interp,
                                        mode='constant')

    return fslimage.Image(result, header=ref.header)


def main(args=None):
    """Entry point. Parse command-line arguments, then calls
    :func:`applyLinear` or :func:`applyNonlinear` depending on the x5 file
    type.
    """

    if args is None:
        args = sys.argv[1:]

    print()
    print('Warning: this version of fsl_apply_x5 is a development release.\n'
          'Interface, behaviour, and input/output formats of future versions\n'
          'may differ substantially from this version.')
    print()

    args = parseArgs(args)

    if x5.inferType(args.xform) == 'linear':
        result = applyLinear(args)
    else:
        result = applyNonlinear(args)

    result.save(args.output)


if __name__ == '__main__':
    sys.exit(main())
