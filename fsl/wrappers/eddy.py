#!/usr/bin/env python
#
# eddy.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


def eddy_cuda(imain, mask, index, acqp, bvecs, bvals, out, very_verbose=False,
              niter=None, fwhm=None, s2v_niter=None, mporder=None, nvoxhp=None,
              slspec=None, b0_only=False, topup=None, field=None,
              field_mat=None, debug=None, s2v_fwhm=None, interp=None,
              dont_mask_output=False, s2v_interp=None, ref_scan_no=None,
              data_is_shelled=False, estimate_move_by_susceptibility=False,
              mbs_niter=None, mbs_lambda=None, mbs_ksp=None, s2v_lambda=None,
              cnr_maps=False, residuals=False):
    """Correct eddy current-induced distortions and subject movements."""
    asrt.assertFileExists(imain, mask, index, acqp, bvecs, bvals)
    asrt.assertIsNifti(imain, mask)

    assert not (topup and field), "topup and field arguments are incompatible"

    out = img.splitext(out)[0]

    opts = " --imain={0} --mask={1} --index={2} --bvals={3} " \
           "--bvecs={4} --acqp={5} --out={6}".format(imain, mask, index, bvals,
                                                     bvecs, acqp, out)

    cmd = op.join(os.getenv('DHCP_EDDY_PATH', ''), 'eddy_cuda')
    # cmd = 'eddy_cuda'
    cmd = cmd + opts

    if very_verbose:
        cmd += " --very_verbose"
    if estimate_move_by_susceptibility:
        cmd += " --estimate_move_by_susceptibility"
    if data_is_shelled:
        cmd += " --data_is_shelled"
    if mbs_niter is not None:
        cmd += " --mbs_niter={0}".format(mbs_niter)
    if mbs_lambda is not None:
        cmd += " --mbs_lambda={0}".format(mbs_lambda)
    if mbs_ksp is not None:
        cmd += " --mbs_ksp={0}".format(mbs_ksp)
    if niter is not None:
        cmd += " --niter={0}".format(niter)
    if fwhm is not None:
        cmd += " --fwhm={0}".format(fwhm)
    if s2v_fwhm is not None:
        cmd += " --s2v_fwhm={0}".format(s2v_fwhm)
    if s2v_niter is not None:
        cmd += " --s2v_niter={0}".format(s2v_niter)
    if s2v_interp is not None:
        cmd += " --s2v_interp={0}".format(s2v_interp)
    if interp is not None:
        cmd += " --interp={0}".format(interp)
    if mporder is not None:
        cmd += " --mporder={0}".format(mporder)
    if nvoxhp is not None:
        cmd += " --nvoxhp={0}".format(nvoxhp)
    if slspec is not None:
        cmd += " --slspec={0}".format(slspec)
    if topup is not None:
        cmd += " --topup={0}".format(topup)
    if field is not None:
        field = img.splitext(field)[0]
        cmd += " --field={0}".format(field)
    if b0_only:
        cmd += " --b0_only"
    if field_mat is not None:
        cmd += " --field_mat={0}".format(field_mat)
    if debug is not None:
        cmd += " --debug={0}".format(debug)
    if dont_mask_output:
        cmd += " --dont_mask_output"
    if ref_scan_no is not None:
        cmd += " --ref_scan_no={0}".format(ref_scan_no)
    if s2v_lambda is not None:
        cmd += " --s2v_lambda={0}".format(s2v_lambda)
    if cnr_maps:
        cmd += " --cnr_maps"
    if residuals:
        cmd += " --residuals"

    shops.run(cmd)




def topup(imain, datain, config=None, fout=None, iout=None, out=None,
          verbose=False, subsamp=None, logout=None):
    """Estimate and correct susceptibility induced distortions."""
    asrt.assertFileExists(imain, datain)
    asrt.assertIsNifti(imain)

    cmd = "topup --imain={0} --datain={1}".format(imain, datain)

    if config is not None:
        cmd += " --config={0}".format(config)
    if fout is not None:
        cmd += " --fout={0}".format(fout)
    if iout is not None:
        cmd += " --iout={0}".format(iout)
    if out is not None:
        cmd += " --out={0}".format(out)
    if subsamp is not None:
        cmd += " --subsamp={0}".format(subsamp)
    if logout is not None:
        cmd += " --logout={0}".format(logout)
    if verbose:
        cmd += " -v"

    shops.run(cmd)
