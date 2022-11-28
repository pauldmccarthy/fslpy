#!/usr/bin/env python
#
# first.py - Wrapper functions for the FSL FIRST commands.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains wrapper functions for the FSL
`FIRST <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST/>`_ commands,
for subcortical segmentation.
"""


from . import wrapperutils  as wutils


@wutils.fileOrImage('input')
@wutils.fslwrapper
def first(input, outputName, inputModel, flirtMatrix, **kwargs):
    """Wrapper function for the FSL ``first`` command. """

    valmap = {
        'v'                   : wutils.SHOW_IF_TRUE,
        'verbose'             : wutils.SHOW_IF_TRUE,
        'intref'              : wutils.SHOW_IF_TRUE,
        'multiImageInput'     : wutils.SHOW_IF_TRUE,
        'binarySurfaceOutput' : wutils.SHOW_IF_TRUE,
        'loadBvars'           : wutils.SHOW_IF_TRUE,
        'shcond'              : wutils.SHOW_IF_TRUE
    }

    cmd  = ['first',
            f'--in={input}',
            f'--outputName={outputName}',
            f'--inputModel={inputModel}',
            f'--flirtMatrix={flirtMatrix}']
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input', 'strucweight')
@wutils.fslwrapper
def first_flirt(input, output, **kwargs):
    """Wrapper function for the FSL ``first_flirt`` command. """
    valmap = {
        'b'        : wutils.SHOW_IF_TRUE,
        'd'        : wutils.SHOW_IF_TRUE,
        'inweight' : wutils.SHOW_IF_TRUE,
        'cort'     : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['first_flirt', input, output]
    cmd += wutils.applyArgStyle('-', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input')
@wutils.fslwrapper
def run_first(input,
              input_to_mni,
              n_modes,
              output_basename,
              model_name,
              **kwargs):
    """Wrapper for the FSL ``run_first`` command. """

    valmap = {
        'v'              : wutils.SHOW_IF_TRUE,
        'multipleImages' : wutils.SHOW_IF_TRUE
    }

    cmd  = ['run_first',
            '-i', input,
            '-t', input_to_mni,
            '-n', str(n_modes),
            '-o', output_basename,
            '-m', model_name]
    cmd += wutils.applyArgStyle('-', valmap=valmap, **kwargs)

    return cmd


@wutils.fileOrImage('input', outprefix='output')
@wutils.fslwrapper
def run_first_all(input, output, **kwargs):
    """Wrapper for the FSL ``run_first_all`` command. Use
    ``three=True`` to apply the ``-3`` argument.
    """

    argmap = {
        'three' : '3'
    }

    valmap = {
        'b' : wutils.SHOW_IF_TRUE,
        '3' : wutils.SHOW_IF_TRUE,
        'd' : wutils.SHOW_IF_TRUE,
        'v' : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['run_first_all', '-i', input, '-o', output]
    cmd += wutils.applyArgStyle('-', argmap=argmap, valmap=valmap,
                                **kwargs)

    return cmd


@wutils.fileOrImage('input', outprefix='output')
@wutils.fslwrapper
def first_utils(input, output, **kwargs):
    """Wrapper for the FSL ``first_utils`` command. """
    valmap = {
        'v'                  : wutils.SHOW_IF_TRUE,
        'verbose'            : wutils.SHOW_IF_TRUE,
        'debug'              : wutils.SHOW_IF_TRUE,
        'overlap'            : wutils.SHOW_IF_TRUE,
        'useScale'           : wutils.SHOW_IF_TRUE,
        'vertezxAnalysis'    : wutils.SHOW_IF_TRUE,
        'singleBoundaryCorr' : wutils.SHOW_IF_TRUE,
        'usePCAFilter'       : wutils.SHOW_IF_TRUE,
        'usebvars'           : wutils.SHOW_IF_TRUE,
        'doMVGLM'            : wutils.SHOW_IF_TRUE,
        'useReconMNI'        : wutils.SHOW_IF_TRUE,
        'useReconNative'     : wutils.SHOW_IF_TRUE,
        'useRigidAlign'      : wutils.SHOW_IF_TRUE,
        'useNorm'            : wutils.SHOW_IF_TRUE,
        'surfaceVAout'       : wutils.SHOW_IF_TRUE,
        'reconMeshFromBvars' : wutils.SHOW_IF_TRUE,
        'readBvars'          : wutils.SHOW_IF_TRUE,
        'concatBvars'        : wutils.SHOW_IF_TRUE,
        'meshToVol'          : wutils.SHOW_IF_TRUE,
        'centreOrigin'       : wutils.SHOW_IF_TRUE
    }

    cmd  = ['first_utils', '--in', input, '--out', output]
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd


@wutils.fslwrapper
def concat_bvars(output, *inputs):
    """Wrapper for the FSL ``concat_bvars`` command. """
    return ['concat_bvars', output] + list(inputs)
