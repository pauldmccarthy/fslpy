#!/usr/bin/env python
#
# melodic.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import fsl.utils.run        as run
import fsl.utils.assertions as asrt


def melodic(input, outdir, dim=None, tr=None, mmthresh=None, report=True,
            prefix=None, nomask=False, updatemask=False, nobet=False,
            mask=None):
    """Multivariate Exploratory Linear Optimised ICA."""
    asrt.assertIsNifti(input)

    cmd = "melodic -i {0} -v --Oall --outdir={1}".format(input, outdir)

    if mmthresh:
        cmd += " --mmthresh={0}".format(mmthresh)
    if dim:
        cmd += " -d -{0}".format(dim)
    if report:
        cmd += " --report"
    if tr:
        cmd += " --tr={0}".format(tr)
    if nomask:
        cmd += " --nomask"
    if updatemask:
        cmd += " --update_mask"
    if nobet:
        cmd += " --nobet"
    if prefix:
        cmd = prefix + " " + cmd
    if mask is not None:
        cmd += " --mask={0}".format(mask)
    return run.runfsl(cmd)


def fsl_regfilt(infile, outfile, mix, ics):
    """Data de-noising by regression.

    Data de-noising by regressing out part of a design matrix
    using simple OLS regression on 4D images
    """
    asrt.assertIsNifti(infile, outfile)

    icstr = '"'
    for i in range(0, len(ics) - 1):
        icstr = icstr + '{0},'.format(ics[i] + 1)
    icstr = icstr + '{0}"'.format(ics[-1] + 1)

    cmd = "fsl_regfilt -i {0} -o {1} -d {2} -f {3}".format(infile, outfile,
                                                           mix, icstr)
    return run.runfsl(cmd)
