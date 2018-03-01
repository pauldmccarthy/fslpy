#!/usr/bin/env python
#
# flirt.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""

.. autosummary::
   :nosignatures:

   flirt
   invxfm
   applyxfm
   concatxfm
   mcflirt
"""


import fsl.utils.run        as run
import fsl.utils.assertions as asrt
import fsl.data.image       as fslimage
from . import wrapperutils  as wutils


@wutils.required('src', 'ref')
@wutils.fileOrImage('src', 'ref', 'out', 'wmseg', 'fieldmap', 'fieldmapmask')
@wutils.fileOrArray('init', 'omat', 'wmcoords', 'wmnorms')
def flirt(src, ref, **kwargs):
    """FLIRT (FMRIB's Linear Image Registration Tool)."""

    asrt.assertIsNifti(src, ref)

    valmap = {
        'usesqform'    : wutils.SHOW_IF_TRUE,
        'displayinit'  : wutils.SHOW_IF_TRUE,
        'noresample'   : wutils.SHOW_IF_TRUE,
        'forcescaling' : wutils.SHOW_IF_TRUE,
        'applyxfm'     : wutils.SHOW_IF_TRUE,
        'nosearch'     : wutils.SHOW_IF_TRUE,
        'noclamp'      : wutils.SHOW_IF_TRUE,
        'noresampblur' : wutils.SHOW_IF_TRUE,
        '2D'           : wutils.SHOW_IF_TRUE,
        'v'            : wutils.SHOW_IF_TRUE,
        'version'      : wutils.SHOW_IF_TRUE,
        'help'         : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['flirt', '-in', src, '-ref', ref]
    cmd += wutils.applyArgStyle('-', valmap=valmap, **kwargs)

    return run.runfsl(cmd)


def invxfm(inmat, omat):
    """Tool for inverting FSL transformation matrices."""
    asrt.assertFileExists(inmat)

    cmd = "convert_xfm -omat {0} -inverse {1}".format(omat, inmat)
    return run.runfsl(cmd)


def applyxfm(src, ref, mat, out, interp='spline'):
    """Tool for applying FSL transformation matrices."""
    asrt.assertFileExists(src, ref)
    asrt.assertIsNifti(src, ref)

    cmd = "flirt -init {0} -in {1} -ref {2} -applyxfm -out {3} -interp {4}"
    return run.runfsl(cmd.format(mat, src, ref, out, interp))

@wutils.required(   'inmat1', 'inmat2', 'outmat')
@wutils.fileOrArray('inmat1', 'inmat2', 'outmat')
def concatxfm(inmat1, inmat2, outmat):
    """Tool to concatenate two FSL transformation matrices."""

    print('inmat1', inmat1)
    print('inmat2', inmat2)
    print('outmat', outmat)

    asrt.assertFileExists(inmat1, inmat2)

    cmd = ['convert_xfm',
           '-omat',
           outmat,
           '-concat',
           inmat2,
           inmat1]

    return run.runfsl(cmd)


def mcflirt(infile, outfile, reffile=None, spline_final=True, plots=True,
            mats=True, refvol=None):
    """Rigid-body motion correction using mcflirt."""

    outfile = fslimage.removeExt(outfile)
    cmd = "mcflirt -in {0} -out {1} -rmsrel -rmsabs".format(infile, outfile)

    if reffile is not None:
        cmd += " -reffile {0}".format(reffile)
    if refvol is not None:
        cmd += " -refvol {0}".format(refvol)
    if spline_final:
        cmd += " -spline_final"
    if plots:
        cmd += " -plots"
    if mats:
        cmd += " -mats"

    return run.runfsl(cmd)
