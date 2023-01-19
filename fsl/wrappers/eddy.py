#!/usr/bin/env python
#
# eddy.py - Wrappers for topup and eddy.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Martin Craig <martin.craig@eng.ox.a.uk>
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk>
#
"""This module provides wrapper functions for the FSL `TOPUP
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/topup>`_ and `EDDY
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/eddy>`_ tools, for field map
estimation and eddy-current distortion correction.

.. autosummary::
   :nosignatures:

   eddy_cuda
   topup
   applytopup
"""


import fsl.utils.assertions as asrt
from fsl.utils.deprecated import deprecated
from . import wrapperutils  as wutils


@wutils.fileOrImage('imain', 'mask', 'field')
@wutils.fileOrArray('index', 'acqp', 'bvecs', 'bvals', 'field_mat')
@wutils.fslwrapper
def eddy(imain, mask, index, acqp, bvecs, bvals, out, **kwargs):
    """Wrapper for the ``eddy`` command."""

    valmap = {
        'fep'                             : wutils.SHOW_IF_TRUE,
        'initrand'                        : wutils.SHOW_IF_TRUE,
        'repol'                           : wutils.SHOW_IF_TRUE,
        'ol_pos'                          : wutils.SHOW_IF_TRUE,
        'ol_sqr'                          : wutils.SHOW_IF_TRUE,
        'dont_sep_offs_move'              : wutils.SHOW_IF_TRUE,
        'dont_peas'                       : wutils.SHOW_IF_TRUE,
        'data_is_shelled'                 : wutils.SHOW_IF_TRUE,
        'b0_only'                         : wutils.SHOW_IF_TRUE,
        'dont_mask_output'                : wutils.SHOW_IF_TRUE,
        'cnr_maps'                        : wutils.SHOW_IF_TRUE,
        'residuals'                       : wutils.SHOW_IF_TRUE,
        'estimate_move_by_susceptibility' : wutils.SHOW_IF_TRUE,
        'verbose'                         : wutils.SHOW_IF_TRUE,
        'very_verbose'                    : wutils.SHOW_IF_TRUE,
        'sep_offs_move'                   : wutils.SHOW_IF_TRUE,
        'rms'                             : wutils.SHOW_IF_TRUE,
    }

    asrt.assertFileExists(imain, mask, index, acqp, bvecs, bvals)
    asrt.assertIsNifti(imain, mask)

    kwargs.update({'imain' : imain,
                   'mask'  : mask,
                   'index' : index,
                   'acqp'  : acqp,
                   'bvecs' : bvecs,
                   'bvals' : bvals,
                   'out'   : out})

    cmd = ['eddy'] + wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
    return cmd


@deprecated("3.10", "4.0", "eddy_cuda has been deprecated in favour of eddy, which will call the appropriate GPU or CPU version of eddy automatically.")
def eddy_cuda(*args, **kwargs):
    eddy(*args, **kwargs)


@wutils.fileOrImage('imain', 'fout', 'iout', outprefix='out')
@wutils.fileOrArray('datain', outprefix='out')
@wutils.fslwrapper
def topup(imain, datain, **kwargs):
    """Wrapper for the ``topup`` command.

Compulsory arguments (You MUST set one or more of):
    :arg imain:    name of 4D file with images
    :arg datain:   name of text file with PE directions/times

Optional arguments (You may optionally specify one or more of):
    :arg out:         Base-name of output files (spline coefficients (Hz) and movement parameters)
    :arg fout:        Name of image file with field (Hz)
    :arg iout:        Name of 4D image file with unwarped images
    :arg jacout:      Name of 4D image file with jacobian of the warp
    :arg logout:      Name of log-file
    :arg warpres:     (approximate) resolution (in mm) of warp basis for the different sub-sampling levels, default 10
    :arg subsamp:     sub-sampling scheme, default 1
    :arg fwhm:        FWHM (in mm) of gaussian smoothing kernel, default 8
    :arg config:      Name of config file specifying command line arguments
    :arg miter:       Max # of non-linear iterations, default 5
    :arg lambda:      Weight of regularisation, default depending on :arg ssqlambda and :arg regmod switches. See user documetation.
    :arg ssqlambda:   If set (=1), lambda is weighted by current ssq, default 1
    :arg regmod:      Model for regularisation of warp-field [membrane_energy bending_energy], default bending_energy
    :arg estmov:      Estimate movements if set, default 1 (true)
    :arg minmet:      Minimisation method 0=Levenberg-Marquardt, 1=Scaled Conjugate Gradient, default 0 (LM)
    :arg splineorder: Order of spline, 2->Qadratic spline, 3->Cubic spline. Default=3
    :arg numprec:     Precision for representing Hessian, double or float. Default double
    :arg interp:      Image interpolation model, linear or spline. Default spline
    :arg scale:       If set (=1), the images are individually scaled to a common mean, default 0 (false)
    :arg regrid:      If set (=1), the calculations are done in a different grid, default 1 (true)
    :arg nthr:        Number of threads to use (cannot be greater than numbers of hardware cores), default 1
    :arg h:           display help info
    :arg v:           Print diagonostic information while running

    """

    valmap = {
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    asrt.assertIsNifti(imain)

    cmd  = ['topup', '--imain={}'.format(imain), '--datain={}'.format(datain)]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd

@wutils.fileOrImage('imain', outprefix='out')
@wutils.fileOrArray('datain')
@wutils.fslwrapper
def applytopup(imain, datain, index, topup, out, **kwargs):
    """Wrapper for the ``applytopup`` command.

Compulsory arguments (You MUST set one or more of):
    :arg imain:    comma separated list of names of input image (to be corrected)
    :arg datain:   name of text file with PE directions/times
    :arg inindex:  comma separated list of indicies into --datain of the input image (to be corrected)
    :arg topup:    name of field/movements (from topup)
    :arg out:      basename for output (warped) image

Optional arguments (You may optionally specify one or more of):
    :arg method:    Use jacobian modulation (jac) or least-squares resampling (lsr), default=lsr.
    :arg interp:    interpolation method {trilinear,spline}, default=spline
    :arg datatype:  Force output data type [char short int float double].
    :arg verbose:   switch on diagnostic messages
    :arg help:      display this message

    """

    valmap = {
        'verbose' : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(datain)
    for fn in imain.split(','):
        asrt.assertIsNifti(fn)

    cmd  = [
        'applytopup', '--imain={}'.format(imain),
        '--inindex={}'.format(index),
        '--datain={}'.format(datain),
        '--topup={}'.format(topup), 
        '--out={}'.format(out)
    ]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd
