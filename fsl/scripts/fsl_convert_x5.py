#!/usr/bin/env python
#
# fsl_convert_x5.py - Convert between FSL and X5 transformation files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This script can be used to convert between FSL and X5 linear and non-linear
transformation file formats.
"""


import os.path as       op
import                  sys
import                  shutil
import                  logging
import                  argparse
from collections import OrderedDict

import fsl.data.image      as fslimage
import fsl.transform.flirt as flirt
import fsl.transform.fnirt as fnirt
import fsl.transform.x5    as x5


log = logging.getLogger(__name__)


def parseArgs(args):
    """Create an argument parser and parse the given ``args``.

    :arg args: Sequence of commane line arguments.
    :return:   An ``argparse.Namespace`` object containing parsed arguments.
    """

    helps = {
        'input'         : 'Input file',
        'output'        : 'Output file',
        'source'        : 'Source image',
        'reference'     : 'Reference image',
        'input_format'  : 'Input format - if not provided, the input format '
                          'is automatically inferred from the input file '
                          'name.',
        'output_format' : 'Output format - if not provided, the output format '
                          'is automatically inferred from the output file '
                          'name.',
    }

    parser     = argparse.ArgumentParser('fsl_convert_x5')
    subparsers = parser.add_subparsers(dest='ctype')
    flirt      = subparsers.add_parser('flirt')
    fnirt      = subparsers.add_parser('fnirt')

    flirt.add_argument('input',                  help=helps['input'])
    flirt.add_argument('output',                 help=helps['output'])
    flirt.add_argument('-s',  '--source',        help=helps['source'])
    flirt.add_argument('-r',  '--reference',     help=helps['reference'])
    flirt.add_argument('-if', '--input_format',  help=helps['input_format'],
                       choices=('x5', 'mat'))
    flirt.add_argument('-of', '--output_format', help=helps['output_format'],
                       choices=('x5', 'mat'))

    fnirt  .add_argument('input',                  help=helps['input'])
    fnirt  .add_argument('output',                 help=helps['output'])
    fnirt  .add_argument('-s',  '--source',        help=helps['source'])
    fnirt  .add_argument('-r',  '--reference',     help=helps['reference'])
    fnirt  .add_argument('-if', '--input_format',  help=helps['input_format'],
                         choices=('x5', 'nii'))
    fnirt  .add_argument('-of', '--output_format', help=helps['output_format'],
                         choices=('x5', 'nii'))

    args = parser.parse_args(args)

    if args.ctype is None:
        parser.print_help()
        sys.exit(0)

    # If input/output formats were not
    # specified, infer them from the
    # file names
    def getfmt(arg, fname, exist):
        ext = op.splitext(fname)[1]
        if ext in ('.mat', '.x5'):
            return ext[1:]

        fname = fslimage.addExt(fname, mustExist=exist)

        if fslimage.looksLikeImage(fname):
            return 'nii'
        parser.error('Could not infer format from '
                     'filename: {}'.format(args.input))

    if args.input_format  is None:
        args.input_format  = getfmt('input',  args.input, True)
    if args.output_format is None:
        args.output_format = getfmt('output', args.output, False)

    # The source and reference arguments are
    # required if the input is a FLIRT matrix
    # or a FNIRT displacement/coefficient field.
    if args.input_format in ('mat', 'nii') and \
       (args.source is None or args.reference is None):
        parser.error('You must specify a source and reference '
                     'when the input is not an X5 file!')

    return args


def flirtToX5(args):
    """Convert a linear FLIRT transformation matrix to an X5 transformation
    file.
    """
    src   = fslimage.Image(args.source,    loadData=False)
    ref   = fslimage.Image(args.reference, loadData=False)
    xform = flirt.readFlirt(args.input)
    xform = flirt.fromFlirt(xform, src, ref, 'world', 'world')
    x5.writeLinearX5(args.output, xform, src, ref)


def X5ToFlirt(args):
    """Convert a linear X5 transformation file to a FLIRT matrix. """
    xform, src, ref = x5.readLinearX5(args.input)
    xform           = flirt.toFlirt(xform, src, ref, 'world', 'world')
    flirt.writeFlirt(xform, args.output)


def fnirtToX5(args):
    """Convert a non-linear FNIRT transformation into an X5 transformation
    file.
    """
    src   = fslimage.Image(args.source,    loadData=False)
    ref   = fslimage.Image(args.reference, loadData=False)
    field = fnirt.readFnirt(args.input, src=src, ref=ref)
    field = fnirt.fromFnirt(field, 'world', 'world')
    x5.writeNonLinearX5(args.output, field)


def X5ToFnirt(args):
    """Convert a non-linear X5 transformation file to a FNIRT-style
    transformation file.
    """
    field = x5.readNonLinearX5(args.input)
    field = fnirt.toFnirt(field)
    field.save(args.output)


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
