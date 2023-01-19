#!/usr/bin/env python
#
# bedpostx.py - Wrappers for bedpostx and its sub-functions
#
# Author: Fidel Alfaro Almagro <fidel.alfaroalmagro@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `BEDPOSTX
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/bedpostx>`.

.. autosummary::
   :nosignatures:

   xfibres_gpu
   split_parts_gpu
   bedpostx_postproc_gpu

"""


import fsl.utils.assertions as asrt
from fsl.utils.deprecated import deprecated
from . import wrapperutils  as wutils


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def xfibres_gpu(data, mask, bvecs, bvals, SubjectDir, NumThisPart,
                TotalNumParts, TotalNumVoxels, **kwargs):
    """Wrapper for the ``xfibres_gpu`` command.

    Compulsory arguments (You MUST set one or more of):
        :arg data:           Data file
        :arg mask:           Mask file
        :arg bvecs:          b vectors file
        :arg bvals:          b values file
        :arg SubjectDir:     Directory of the Subject
        :arg NumThisPart:    Number of the part to process
        :arg TotalNumParts:  Total number of parts to process
        :arg TotalNumVoxels: Total number of voxels for all parts

    Optional arguments (You may optionally specify one or more of):
        :arg verbose:        Switch on diagnostic messages
        :arg logdir:         Log directory (default is logdir)
        :arg forcedir:       Use the actual directory name given - i.e. don't add + to make a new directory
        :arg nfibres:        Maximum number of fibres to fit in each voxel (default 1)
        :arg model:          Which model to use. 1=deconv. with sticks (default). 2=deconv. with sticks and a range of diffusivities. 3=deconv. with zeppelins
        :arg fudge:          ARD fudge factor
        :arg njumps:         Num of jumps to be made by MCMC (default is 5000)
        :arg burnin:         Total num of jumps at start of MCMC to be discarded (default is 0)
        :arg burnin_noard:   Num of burnin jumps before the ard is imposed (default is 0)
        :arg sampleevery:    Num of jumps for each sample (MCMC) (default is 1)
        :arg updateproposalevery: Num of jumps for each update to the proposal density std (MCMC) (default is 40)
        :arg seed:           Seed for pseudo random number generator
        :arg noard:          Turn ARD off on all fibres
        :arg allard:         Turn ARD on on all fibres
        :arg nospat:         Initialise with tensor, not spatially
        :arg nonlinear:      Initialise with nonlinear fitting
        :arg cnonlinear:     Initialise with constrained nonlinear fitting
        :arg rician:         Use Rician noise modelling
        :arg f0:             Add to the model an unattenuated signal compartment
        :arg ardf0:          Use ard on f0
        :arg Rmean:          Set the prior mean for R of model 3 (default:0.13- Must be<0.5)
        :arg Rstd:           Set the prior standard deviation for R of model 3 (default:0.03)

"""

    valmap = {
        'forcedir'   : wutils.SHOW_IF_TRUE,
        'nonlinear'  : wutils.SHOW_IF_TRUE,
        'vebose'     : wutils.SHOW_IF_TRUE,
        'noard'      : wutils.SHOW_IF_TRUE,
        'allard'     : wutils.SHOW_IF_TRUE,
        'nospat'     : wutils.SHOW_IF_TRUE,
        'nonlinear'  : wutils.SHOW_IF_TRUE,
        'cnonlinear' : wutils.SHOW_IF_TRUE,
        'rician'     : wutils.SHOW_IF_TRUE,
        'ardf0'      : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['xfibres_gpu', "--data="+data, "--mask=" + mask, 
           '--bvecs=' + bvecs, '--bvals=' + bvals] 

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
 
    cmd += [SubjectDir, NumThisPart, TotalNumParts, TotalNumVoxels]
    return cmd



@wutils.fileOrImage('Datafile', 'Maskfile')
@wutils.fileOrArray('Bvalsfile', 'Bvecsfile')
@wutils.fslwrapper
def split_parts_gpu(Datafile, Maskfile, Gradfile, Use_grad_file, TotalNumParts,
                    OutputDirectory, Bvalsfile="", Bvecsfile=""):
    """Wrapper for the ``split_parts_gpu`` command."""

    print(Datafile)
    if Bvalsfile and Bvecsfile:
        asrt.assertFileExists(Bvalsfile, Bvecsfile)
    asrt.assertIsNifti(Datafile, Maskfile)

    cmd  = ['split_parts_gpu', Datafile, Maskfile, Bvalsfile, Bvecsfile,
             Gradfile, Use_grad_file, TotalNumParts, OutputDirectory]
    return cmd


@wutils.fileOrImage('data', 'mask',)
@wutils.fileOrArray('bvecs', 'bvals')
@wutils.fslwrapper
def bedpostx_postproc_gpu(data, mask, bvecs, bvals, TotalNumVoxels, SubjectDir, 
                          TotalNumParts, bindir, **kwargs):
    """Wrapper for the ``bedpostx_postproc_gpu`` command.

    Compulsory arguments (You MUST set one or more of):
        :arg data:           Data file
        :arg mask:           Mask file
        :arg bvecs:          b vectors file
        :arg bvals:          b values file
        :arg TotalNumVoxels: Total number of voxels for all parts
        :arg SubjectDir:     Directory of the Subject
        :arg TotalNumParts:  Total number of parts to process
        :arg bindir:         Directory with FSL binaries

    Optional arguments (You may optionally specify one or more of):
        :arg verbose:        Switch on diagnostic messages
        :arg logdir:         Log directory (default is logdir)
        :arg forcedir:       Use the actual directory name given - i.e. don't add + to make a new directory
        :arg nfibres:        Maximum number of fibres to fit in each voxel (default 1)
        :arg model:          Which model to use. 1=deconv. with sticks (default). 2=deconv. with sticks and a range of diffusivities. 3=deconv. with zeppelins
        :arg fudge:          ARD fudge factor
        :arg njumps:         Num of jumps to be made by MCMC (default is 5000)
        :arg burnin:         Total num of jumps at start of MCMC to be discarded (default is 0)
        :arg burnin_noard:   Num of burnin jumps before the ard is imposed (default is 0)
        :arg sampleevery:    Num of jumps for each sample (MCMC) (default is 1)
        :arg updateproposalevery: Num of jumps for each update to the proposal density std (MCMC) (default is 40)
        :arg seed:           Seed for pseudo random number generator
        :arg noard:          Turn ARD off on all fibres
        :arg allard:         Turn ARD on on all fibres
        :arg nospat:         Initialise with tensor, not spatially
        :arg nonlinear:      Initialise with nonlinear fitting
        :arg cnonlinear:     Initialise with constrained nonlinear fitting
        :arg rician:         Use Rician noise modelling
        :arg f0:             Add to the model an unattenuated signal compartment
        :arg ardf0:          Use ard on f0
        :arg Rmean:          Set the prior mean for R of model 3 (default:0.13- Must be<0.5)
        :arg Rstd:           Set the prior standard deviation for R of model 3 (default:0.03)

"""

    valmap = {
        'forcedir'   : wutils.SHOW_IF_TRUE,
        'nonlinear'  : wutils.SHOW_IF_TRUE,
        'vebose'     : wutils.SHOW_IF_TRUE,
        'noard'      : wutils.SHOW_IF_TRUE,
        'allard'     : wutils.SHOW_IF_TRUE,
        'nospat'     : wutils.SHOW_IF_TRUE,
        'nonlinear'  : wutils.SHOW_IF_TRUE,
        'cnonlinear' : wutils.SHOW_IF_TRUE,
        'rician'     : wutils.SHOW_IF_TRUE,
        'ardf0'      : wutils.SHOW_IF_TRUE
    }

    asrt.assertFileExists(data, bvecs, bvals)
    asrt.assertIsNifti(mask)

    cmd = ['bedpostx_postproc_gpu.sh', "--data="+data, "--mask=" + mask, 
           '--bvecs=' + bvecs, '--bvals=' + bvals] 

    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)
 
    cmd += [TotalNumVoxels, TotalNumParts, SubjectDir, bindir]
    return cmd


@wutils.fileOrImage('mask', 'seed')
@wutils.fslwrapper
def probtrackx(samples, mask, seed, stop, **kwargs):
    """Wrapper for the ``probtrackx`` command

    Compulsory arguments (You MUST set one or more of):
        :arg samples    Basename for samples files
        :arg mask       Bet binary mask file in diffusion space
        :arg seed       Seed volume, or voxel, or ascii file with multiple volumes, or freesurfer label file

    Optional arguments (You may optionally specify one or more of):
        :arg verbose    Verbose level, [0-2]
        :arg mode       Use --mode=simple for single seed voxel
        :arg targetmasks   File containing a list of target masks - required for seeds_to_targets classification
        :arg mask2      Second mask in twomask_symm mode.
        :arg waypoints  Waypoint mask or ascii list of waypoint masks - only keep paths going through ALL the masks
        :arg network    Activate network mode - only keep paths going through at least one seed mask (required if multiple seed masks)
        :arg mesh       Freesurfer-type surface descriptor (in ascii format)
        :arg seedref    Reference vol to define seed space in simple mode - diffusion space assumed if absent
        :arg dir        Directory to put the final volumes in - code makes this directory - default='logdir'
        :arg forcedir   Use the actual directory name given - i.e. don't add + to make a new directory
        :arg opd        Output path distribution
        :arg pd         Correct path distribution for the length of the pathways
        :arg os2t       Output seeds to targets
        :arg out        Output file (default='fdt_paths')
        :arg avoid      Reject pathways passing through locations given by this mask
        :arg stop       Stop tracking at locations given by this mask file
        :arg xfm        Transform taking seed space to DTI space (either FLIRT matrix or FNIRT warpfield) - default is identity
        :arg invxfm     Transform taking DTI space to seed space (compulsory when using a warpfield for seeds_to_dti)
        :arg nsamples   Number of samples - default=5000
        :arg nsteps     Number of steps per sample - default=2000
        :arg distthresh Discards samples shorter than this threshold (in mm - default=0)
        :arg cthr       Curvature threshold - default=0.2
        :arg fibthresh  Volume fraction before subsidary fibre orientations are considered - default=0.01
        :arg sampvox    Sample random points within seed voxels
        :arg steplength Steplength in mm - default=0.5
        :arg loopcheck  Perform loopchecks on paths - slower, but allows lower curvature threshold
        :arg usef       Use anisotropy to constrain tracking
        :arg randfib    Default 0. Set to 1 to randomly sample initial fibres (with f > fibthresh). 
                          Set to 2 to sample in proportion fibres (with f>fibthresh) to f. 
                          Set to 3 to sample ALL populations at random (even if f<fibthresh)
        :arg fibst      Force a starting fibre for tracking - default=1, i.e. first fibre orientation. Only works if randfib==0
        :arg modeuler   Use modified euler streamlining
        :arg rseed      Random seed
        :arg s2tastext  Output seed-to-target counts as a text file (useful when seeding from a mesh)


"""

    valmap = {
        'forcedir'  : wutils.SHOW_IF_TRUE,
        'network'   : wutils.SHOW_IF_TRUE,
        'vebose'    : wutils.SHOW_IF_TRUE,
        'opd'       : wutils.SHOW_IF_TRUE,
        'pd'        : wutils.SHOW_IF_TRUE,
        'sampvox'   : wutils.SHOW_IF_TRUE,
        'loopcheck' : wutils.SHOW_IF_TRUE,
        'usef'      : wutils.SHOW_IF_TRUE,
        'modeuler'  : wutils.SHOW_IF_TRUE,
    }

    asrt.assertIsNifti(mask, seed)

    cmd = ['probtrackx',"--samples="+samples,"--mask=" + mask,'--seed=' + seed]

    # Needed for dificult issues with stop parameter
    if stop:
        cmd += ["--stop=" + stop]
        
    cmd += wutils.applyArgStyle('--=', valmap=valmap, **kwargs)

    return cmd