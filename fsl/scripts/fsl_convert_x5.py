#!/usr/bin/env python
#
# fsl_convert_x5.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


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

    flirt.add_argument('input')
    flirt.add_argument('output')
    flirt.add_argument('-s', '--source')
    flirt.add_argument('-r', '--reference')
    flirt.add_argument('-if', '--input_format',  choices=('x5', 'mat'))
    flirt.add_argument('-of', '--output_format', choices=('x5', 'mat'))

    args = parser.parse_args(args)

    def getfmt(fname):
        ext = op.splitext(fname)[1]
        if ext not in ('.x5', '.mat'):
            raise argparse.ArgumentError('Could not infer format from '
                                         'filename: {}'.format(args.input))
        return ext[1:]

    if args.ctype == 'flirt':
        if args.input_format  is None: args.input_format  = getfmt(args.input)
        if args.output_format is None: args.output_format = getfmt(args.output)

    return args


def flirtToX5(args):
    src   = fslimage.Image(args.source)
    ref   = fslimage.Image(args.reference)
    xform = transform.readFlirt(args.input)
    transform.writeFlirtX5(args.output, xform, src, ref)


def X5ToFlirt(args):
    xform, src, ref = transform.readFlirtX5(args.input)
    xform           = transform.toFlirt(xform, src, ref, 'world', 'world')
    transform.writeFlirt(xform, args.output)


def main(args=None):

    if args is None:
        args = sys.argv[1:]

    args   = parseArgs(args)
    ctype  = args.ctype

    if ctype == 'flirt':
        infmt  = args.input_format
        outfmt = args.output_format

        if   (infmt, outfmt) == ('x5', 'mat'): X5ToFlirt(args)
        elif (infmt, outfmt) == ('mat', 'x5'): flirtToX5(args)
        else: shutil.copy(args.input, args.output)


if __name__ == '__main__':
    sys.exit(main())
