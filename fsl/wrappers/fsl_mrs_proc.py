#!/usr/bin/env python
# fsl_mrs_proc.py - Wrappers for fsl_mrs_proc command line tool.
#
# Author: Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#
#
"""This module provides wrapper functions for fsl_mrs_proc and its subcommands.

.. autosummary::
   :nosignatures:

   coilcombine
   average
   align
   align_diff
   ecc
   remove
   model
   tshift
   truncate
   apodize
   fshift
   unlike
   phase
   fixed_phase
   subtract
   add
   conj
   mrsi_align
   mrsi_lipid
"""

import fsl.utils.assertions as asrt
from . import wrapperutils as wutils


@wutils.fileOrImage('file', 'filename', 'reference')
@wutils.fslwrapper
def coilcombine(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc coilcombine`` command.
    The following arguments are currently supported:
    file, output, reference, no_prewhiten, covariance, noise,
    overwrite, r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'no_prewhiten'  : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc coilcombine',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def average(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc average`` command.
    The following arguments are currently supported:
    file, output, dim, overwrite, r/generateReports, allreports,
    filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc average',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'reference')
@wutils.fslwrapper
def align(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc align`` command.
    The following arguments are currently supported:
    file, output, dim, ppm, reference, window, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc align',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def align_diff(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc align-diff`` command.
    The following arguments are currently supported:
    file, output, dim, dim_diff, ppm, diff_type, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc align-diff',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'reference')
@wutils.fslwrapper
def ecc(file, reference, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc ecc`` command.
    The following arguments are currently supported:
    file, reference, output, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file, reference)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc ecc',
           '--file', file,
           '--reference', reference,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def remove(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc remove`` command.
    The following arguments are currently supported:
    file, output, ppm, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc remove',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def model(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc model`` command.
    The following arguments are currently supported:
    file, output, ppm, components, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc model',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def tshift(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc tshift`` command.
    The following arguments are currently supported:
    file, output, tshiftStart, tshiftEnd, samples, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc tshift',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def truncate(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc truncate`` command.
    The following arguments are currently supported:
    file, output, points, pos, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc truncate',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def apodize(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc apodize`` command.
    The following arguments are currently supported:
    file, output, filter, amount, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc apodize',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def fshift(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc fshift`` command.
    The following arguments are currently supported:
    file, output, shiftppm, shifthz, shiftRef, ppm, target, use_avg,
    overwrite, r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'shiftRef'      : wutils.SHOW_IF_TRUE,
        'use_avg'       : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc fshift',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def unlike(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc unlike`` command.
    The following arguments are currently supported:
    file, output, sd, iter, ppm, outputbad, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'outputbad'     : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc unlike',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def phase(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc phase`` command.
    The following arguments are currently supported:
    file, output, ppm, hlsvd, use_avg, overwrite,
    r/generateReports, allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'hlsvd'         : wutils.SHOW_IF_TRUE,
        'use_avg'       : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc phase',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def fixed_phase(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc fixed_phase`` command.
    The following arguments are currently supported:
    file, output, p0, p1, p1_type, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc Xfixed_phase',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'reference')
@wutils.fslwrapper
def subtract(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc subtract`` command.
    The following arguments are currently supported:
    file, output, reference, dim, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc subtract',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'reference')
@wutils.fslwrapper
def add(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc add`` command.
    The following arguments are currently supported:
    file, output, reference, dim, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc add',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename')
@wutils.fslwrapper
def conj(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc conj`` command.
    The following arguments are currently supported:
    file, output, overwrite, r/generateReports, allreports,
    filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc conj',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'mask')
@wutils.fslwrapper
def mrsi_align(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc mrsi-align`` command.
    The following arguments are currently supported:
    file, output, mask, freq_align, zpad, phase-correct, ppm,
    save_params, overwrite, r/generateReports, allreports,
    filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'freq_align' : 'freq-align',
        'save_params': 'save-params',
        'r': 'generateReports',
    }
    
    valmap = {
        'freq-align'    : wutils.SHOW_IF_TRUE,
        'phase-correct' : wutils.SHOW_IF_TRUE,
        'save-params'   : wutils.SHOW_IF_TRUE,
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc mrsi-align',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('file', 'filename', 'mask')
@wutils.fslwrapper
def mrsi_lipid(file, output, **kwargs):
    """Wrapper for the ``fsl_mrs_proc mrsi-lipid`` command.
    The following arguments are currently supported:
    file, output, mask, beta, overwrite, r/generateReports,
    allreports, filename, verbose.
    """

    asrt.assertIsNiftiMRS(file)

    argmap = {
        'r': 'generateReports',
    }
    
    valmap = {
        'overwrite'     : wutils.SHOW_IF_TRUE,
        'allreports'    : wutils.SHOW_IF_TRUE,
        'verbose'       : wutils.SHOW_IF_TRUE,
    }

    cmd = ['fsl_mrs_proc mrsi-lipid',
           '--file', file,
           '--output', output,
    ]

    cmd += wutils.applyArgStyle('--', argmap=argmap, valmap=valmap, **kwargs)

    return cmd
