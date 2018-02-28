#!/usr/bin/env python
#
# misc.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.utils.run        as run
import fsl.utils.assertions as asrt


def fslreorient2std(input, output):
    """reorient to match the approx. orientation of the standard (MNI152)."""

    asrt.assertIsNifti(input, output)
    asrt.assertFileExists(input)

    cmd = 'fslreorient2std {0} {1}'.format(input, output)
    return run.runfsl(cmd)


def fslroi(input, output, xmin=None, xsize=None, ymin=None, ysize=None,
           zmin=None, zsize=None, tmin=None, tsize=None):
    """Extract region of interest (ROI) from an image."""
    assert ((tmin is not None and tsize is not None) or
            (xmin is not None and xsize is not None and
            ymin is not None and ysize is not None and
            zmin is not None and zsize is not None)), \
        "either time min/size or x/y/z min/size must be provided"

    cmd = "fslroi {0} {1}".format(input, output)

    if xmin is not None:
        cmd += " {0} {1} {2} {3} {4} {5}".format(xmin, xsize, ymin, ysize,
                                                 zmin, zsize)
    if tmin is not None:
        cmd += " {0} {1}".format(tmin, tsize)

    return run.runfsl(cmd)


def slicer(input, input2=None, label=None, lut=None, intensity=None,
           edgethreshold=None, x=None, y=None, z=None):

    cmd = "slicer {0}".format(input)

    if input2 is not None:
        cmd += " {0}".format(input2)
    if label is not None:
        cmd += " -L {0}".format(label)
    if lut is not None:
        cmd += " -l {0}".format(lut)
    if intensity is not None:
        cmd += " -i {0} {1}".format(intensity[0], intensity[1])
    if edgethreshold is not None:
        cmd += " -e {0}".format(edgethreshold)
    if x is not None:
        cmd += " -x {0} {1}".format(x[0], x[1])
    if y is not None:
        cmd += " -y {0} {1}".format(y[0], y[1])
    if z is not None:
        cmd += " -z {0} {1}".format(z[0], z[1])

    return run.runfsl(cmd)


def cluster(infile, thresh, oindex=None, no_table=False):
    """
    Form clusters, report information about clusters and/or perform
    cluster-based inference.
    """
    cmd = "cluster --in={0} --thresh={1}".format(infile, thresh)

    if oindex is not None:
        cmd += " -o {0}".format(oindex)

    if no_table:
        cmd += " --no_table"

    return run.runfsl(cmd)
