#!/usr/bin/env python
#
# fnirt.py - FNIRT wrapper functions.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `FNIRT
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FNIRT/>`_ tool, used for performing
non-linear registration of 3D images.

.. autosummary::
   :nosignatures:

   fnirt
   applywarp
   invwarp
   convertwarp
"""


import os.path as op
import            glob


import fsl.utils.run        as run
import fsl.utils.assertions as asrt


def fnirt(src, ref, aff=None, imprefm=None, impinm=None, applyrefmask=None,
          applyinmask=None, subsamp=None, miter=None, infwhm=None,
          reffwhm=None, lmbda=None, estint=None, warpres=None, ssqlambda=None,
          regmod=None, intmod=None, intorder=None, biasres=None,
          biaslambda=None, refderiv=None, cout=None, intout=None, refout=None,
          iout=None, interp=None, inwarp=None, minmet=None, verbose=False,
          intin=None, jout=None):
    """Do nonlinear image registration."""
    cmd = 'fnirt --in={0} --ref={1}'.format(src, ref)

    if aff is not None:
        cmd += " --aff={0}".format(aff)
    if imprefm is not None:
        cmd += " --imprefm={0}".format(imprefm)
    if impinm is not None:
        cmd += " --impinm={0}".format(impinm)
    if applyrefmask is not None:
        cmd += " --applyrefmask={0}".format(applyrefmask)
    if applyinmask is not None:
        cmd += " --applyinmask={0}".format(applyinmask)
    if subsamp is not None:
        cmd += " --subsamp={0}".format(subsamp)
    if miter is not None:
        cmd += " --miter={0}".format(miter)
    if infwhm is not None:
        cmd += " --infwhm={0}".format(infwhm)
    if reffwhm is not None:
        cmd += " --reffwhm={0}".format(reffwhm)
    if lmbda is not None:
        cmd += " --lambda={0}".format(lmbda)
    if estint is not None:
        cmd += " --estint={0}".format(estint)
    if warpres is not None:
        cmd += " --warpres={0}".format(warpres)
    if ssqlambda is not None:
        cmd += " --ssqlambda={0}".format(ssqlambda)
    if regmod is not None:
        cmd += " --regmod={0}".format(regmod)
    if intmod is not None:
        cmd += " --intmod={0}".format(intmod)
    if intorder is not None:
        cmd += " --intorder={0}".format(intorder)
    if biasres is not None:
        cmd += " --biasres={0}".format(biasres)
    if biaslambda is not None:
        cmd += " --biaslambda={0}".format(biaslambda)
    if refderiv is not None:
        cmd += " --refderiv={0}".format(refderiv)
    if cout is not None:
        cmd += " --cout={0}".format(cout)
    if intout is not None:
        cmd += " --intout={0}".format(intout)
    if refout is not None:
        cmd += " --refout={0}".format(refout)
    if iout is not None:
        cmd += " --iout={0}".format(iout)
    if interp is not None:
        cmd += " --interp={0}".format(interp)
    if inwarp is not None:
        cmd += " --inwarp={0}".format(inwarp)
    if minmet is not None:
        cmd += " --minmet={0}".format(minmet)
    if intin is not None:
        cmd += " --intin={0}".format(intin)
    if jout is not None:
        cmd += " --jout={0}".format(jout)
    if verbose:
        cmd += " --verbose"

    return run.runfsl(cmd)


def applywarp(src, ref, out, warp=None, premat=None, prematdir=None,
              postmat=None, postmatdir=None, interp="spline",
              paddingsize=None, abs=False, rel=False):
    """Tool for applying FSL warps.

    The ``prematdir`` and ``postmatdir`` arguments can be used when warping a
    4D image. You can specify a directory containing multiple affines, named
    ``MAT_????`` (as output by e.g. ``mcflirt``). Each file will be applied to
    one volume (in order) of the image.
    """
    assert (warp or premat or postmat or prematdir or postmatdir), \
        "either a warp or mat (premat, postmat or prematdir) must be supplied"
    assert not (premat and prematdir), \
        "cannot use premat and prematdir arguments together"
    assert not (postmat and postmatdir), \
        "cannot use postmat and postmatdir arguments together"

    def catmats(matdir, out):
        """Concatenate FSL trasformations files into a single file."""
        mats = sorted(glob.glob(op.join(matdir, "MAT_????")))
        with open(out, 'w') as outfile:
            for fname in mats:
                with open(fname) as infile:
                    outfile.write(infile.read())

    cmd = "--in={0} --ref={1} --out={2} --interp={3}".format(src, ref, out,
                                                             interp)
    cmd = "applywarp " + cmd

    if prematdir:
        premat = op.join(prematdir, 'allmats.txt')
        catmats(prematdir, premat)
    if postmatdir:
        postmat = op.join(postmatdir, 'allmats.txt')
        catmats(postmatdir, postmat)
    if warp:
        cmd += " --warp={0}".format(warp)
    if premat:
        cmd += " --premat={0}".format(premat)
    if postmat:
        cmd += " --postmat={0}".format(postmat)
    if paddingsize:
        cmd += " --paddingsize={0}".format(paddingsize)
    if abs:
        cmd += " --abs"
    if rel:
        cmd += " --rel"

    return run.runfsl(cmd)


def invwarp(inwarp, ref, outwarp):
    """Tool for inverting FSL warps."""

    asrt.assertFileExists(inwarp, ref)
    asrt.assertIsNifti(inwarp, ref, outwarp)

    cmd  = 'invwarp'
    cmd += ' --warp={}'.format(inwarp)
    cmd += ' --out={}'.format(outwarp)
    cmd += ' --ref={}'.format(ref)

    return run.runfsl(cmd)


def convertwarp(out, ref, warp1=None, warp2=None, premat=None, midmat=None,
                postmat=None, shiftmap=None, shiftdir=None, absout=False,
                abs=False, rel=False, relout=False):
    """Tool for converting FSL warps."""

    assert (warp1 or warp2 or premat or midmat or postmat), \
        "either a warp (warp1 or warp2) or mat (premat, midmat, or " + \
        "postmat) must be supplied"

    cmd = "convertwarp --ref={0} --out={1}".format(ref, out)
    if warp1:
        cmd = cmd + " --warp1={0}".format(warp1)
    if warp2:
        cmd = cmd + " --warp2={0}".format(warp2)
    if premat:
        cmd = cmd + " --premat={0}".format(premat)
    if midmat:
        cmd = cmd + " --midmat={0}".format(midmat)
    if postmat:
        cmd = cmd + " --postmat={0}".format(postmat)
    if shiftmap:
        cmd = cmd + " --shiftmap={0}".format(shiftmap)
    if shiftdir:
        cmd = cmd + " --shiftdir={0}".format(shiftdir)
    if absout:
        cmd = cmd + " --absout"
    if relout:
        cmd = cmd + " --relout"
    if abs:
        cmd = cmd + " --abs"
    if rel:
        cmd = cmd + " --rel"

    return run.runfsl(cmd)
