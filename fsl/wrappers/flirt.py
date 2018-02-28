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


def flirt(src, ref, out=None, omat=None, dof=None, cost=None, wmseg=None,
          init=None, schedule=None, echospacing=None, pedir=None,
          fieldmap=None, fieldmapmask=None, bbrslope=None, bbrtype=None,
          interp=None, refweight=None, applyisoxfm=None, usesqform=False,
          nosearch=False, verbose=0):
    """FLIRT (FMRIB's Linear Image Registration Tool)."""
    asrt.assertIsNifti(src, ref)
    asrt.assertFileExists(src, ref)

    cmd = "flirt -in {0} -ref {1}".format(src, ref)

    if out is not None:
        asrt.assertIsNifti(out)
        cmd += " -out {0}".format(out)
    if omat is not None:
        cmd += " -omat {0}".format(omat)
    if dof is not None:
        cmd += " -dof {0}".format(dof)
    if cost is not None:
        cmd += " -cost {0}".format(cost)
    if wmseg is not None:
        asrt.assertIsNifti(wmseg)
        cmd += " -wmseg {0}".format(wmseg)
    if init is not None:
        cmd += " -init {0}".format(init)
    if schedule is not None:
        cmd += " -schedule {0}".format(schedule)
    if echospacing is not None:
        cmd += " -echospacing {0}".format(echospacing)
    if pedir is not None:
        cmd += " -pedir {0}".format(pedir)
    if fieldmap is not None:
        cmd += " -fieldmap {0}".format(fieldmap)
    if fieldmapmask is not None:
        cmd += " -fieldmapmask {0}".format(fieldmapmask)
    if bbrslope is not None:
        cmd += " -bbrslope {0}".format(bbrslope)
    if bbrtype is not None:
        cmd += " -bbrtype {0}".format(bbrtype)
    if interp is not None:
        cmd += " -interp {0}".format(interp)
    if refweight is not None:
        asrt.assertIsNifti(refweight)
        cmd += " -refweight {0}".format(refweight)
    if applyisoxfm is not None:
        cmd += " -applyisoxfm {0}".format(applyisoxfm)
    if verbose is not None:
        cmd += " -verbose {0}".format(verbose)
    if usesqform:
        cmd += " -usesqform"
    if nosearch:
        cmd += " -nosearch"

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


def concatxfm(inmat1, inmat2, outmat):
    """Tool to concatenate two FSL transformation matrices."""
    asrt.assertFileExists(inmat1, inmat2)

    cmd = "convert_xfm -omat {0} -concat {1} {2}"
    return run.runfsl(cmd.format(outmat, inmat2, inmat1))


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
