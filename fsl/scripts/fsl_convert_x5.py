#!/usr/bin/env python
#
# fsl_convert_x5.py - Convert between FSL and X5 transformation files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This script can be used to convert between FSL and X5 linear and non-linear
transformation file formats.
"""


import os.path as op
import            sys
import            shutil
import            logging
import            argparse

import fsl.data.image as fslimage
import fsl.transform  as transform


log = logging.getLogger(__name__)


def parseArgs(args):

    parser     = argparse.ArgumentParser('fsl_convert_x5')
    subparsers = parser.add_subparsers(dest='ctype')
    flirt      = subparsers.add_parser('flirt')
    fnirt      = subparsers.add_parser('fnirt')


    flirt.add_argument('input')
    flirt.add_argument('output')
    flirt.add_argument('-s',  '--source')
    flirt.add_argument('-r',  '--reference')
    flirt.add_argument('-if', '--input_format',  choices=('x5', 'mat'))
    flirt.add_argument('-of', '--output_format', choices=('x5', 'mat'))

    intype  = fnirt.add_mutually_exclusive_group()
    outtype = fnirt.add_mutually_exclusive_group()

    fnirt  .add_argument('input')
    fnirt  .add_argument('output')
    fnirt  .add_argument('-s',  '--source')
    fnirt  .add_argument('-r',  '--reference')
    fnirt  .add_argument('-if', '--input_format',  choices=('x5', 'nii'))
    fnirt  .add_argument('-of', '--output_format', choices=('x5', 'nii'))
    intype .add_argument('-ai', '--absin',  action='store_const', const='absolute', dest='inDispType')
    intype .add_argument('-ri', '--relin',  action='store_const', const='relative', dest='inDispType')
    outtype.add_argument('-ao', '--absout', action='store_const', const='absolute', dest='outDispType')
    outtype.add_argument('-ro', '--relout', action='store_const', const='relative', dest='outDispType')

    args = parser.parse_args(args)

    if args.ctype is None:
        parser.print_help()
        sys.exit(0)

    def getfmt(arg, fname):
        ext = op.splitext(fname)[1]
        if ext in ('.mat', '.x5'):
            return ext[1:]
        if fslimage.looksLikeImage(fslimage.fixExt(fname)):
            return 'nii'
        parser.error('Could not infer format from '
                     'filename: {}'.format(args.input))

    if args.input_format  is None: args.input_format  = getfmt('input',  args.input)
    if args.output_format is None: args.output_format = getfmt('output', args.output)

    return args


def flirtToX5(args):
    src   = fslimage.Image(args.source,    loadData=False)
    ref   = fslimage.Image(args.reference, loadData=False)
    xform = transform.readFlirt(args.input)
    xform = transform.fromFlirt(xform, src, ref, 'world', 'world')
    transform.writeLinearX5(args.output, xform, src, ref)


def X5ToFlirt(args):
    """Convert a linear X5 transformation file to a FLIRT matrix. """
    xform, src, ref = transform.readLinearX5(args.input)
    xform           = transform.toFlirt(xform, src, ref, 'world', 'world')
    transform.writeFlirt(xform, args.output)


def fnirtToX5(args):
    """Convert a non-linear FNIRT transformation into an X5 transformation
    file.
    """
    src   = fslimage.Image(args.source,    loadData=False)
    ref   = fslimage.Image(args.reference, loadData=False)
    field = transform.readFnirt(args.input,
                                src=src,
                                ref=ref,
                                dispType=args.inDispType)
    field = transform.fromFnirt(field, 'world', 'world')
    transform.writeNonLinearX5(args.output, field)


def X5ToFnirt(args):
    """Convert a non-linear X5 transformation file to a FNIRT-style
    transformation file.
    """
    field = transform.readNonLinearX5(args.input)
    field = transform.toFnirt(field, 'world', 'world')
    transform.writeFnirt(field, args.output)


def doFlirt(args):
    """Converts a linear FIRT transformation file to or from the X5 format. """
    infmt  = args.input_format
    outfmt = args.output_format

    if   (infmt, outfmt) == ('x5', 'mat'): X5ToFlirt(args)
    elif (infmt, outfmt) == ('mat', 'x5'): flirtToX5(args)
    else: shutil.copy(args.input, args.output)


def doFnirt(args):
    """Converts a non-linear FNIRT transformation file to or from the X5
    format.
    """
    infmt  = args.input_format
    outfmt = args.output_format

    if   (infmt, outfmt) == ('x5', 'nii'): X5ToFnirt(args)
    elif (infmt, outfmt) == ('nii', 'x5'): fnirtToX5(args)
    else: shutil.copy(args.input, args.output)


def main(args=None):
    """Entry point. Calls :func:`doFlirt` or :func:`doFnirt` depending on
    the sub-command specified in the arguments.

    :arg args: Sequence of command-line arguments. If not provided,
               ``sys.argv`` is used.
    """

    if args is None:
        args = sys.argv[1:]

    args = parseArgs(args)

    if   args.ctype == 'flirt': doFlirt(args)
    elif args.ctype == 'fnirt': doFnirt(args)

    return 0


if __name__ == '__main__':
    sys.exit(main())
