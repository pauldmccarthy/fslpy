#!/usr/bin/env python
#
# flirt.py - Wrappers for FLIRT commands.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides wrapper functions for the FSL `FLIRT
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT>`_ tool, and other related
tools.

.. autosummary::
   :nosignatures:

   flirt
   applyxfm
   invxfm
   concatxfm
   mcflirt
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fileOrImage('src', 'ref', 'out', 'wmseg', 'fieldmap', 'fieldmapmask')
@wutils.fileOrArray('init', 'omat', 'wmcoords', 'wmnorms')
@wutils.fslwrapper
def flirt(src, ref, **kwargs):
    """Wrapper for the ``flirt`` command.

    The ``twod`` argument may be used in place of the ``2D`` command line
    option.
    """

    asrt.assertIsNifti(src, ref)

    argmap = {
        'twod' : '2D'
    }

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
    }

    cmd  = ['flirt', '-in', src, '-ref', ref]
    cmd += wutils.applyArgStyle('-', argmap=argmap, valmap=valmap, **kwargs)

    return cmd


def applyxfm(src, ref, mat, out, interp='spline', **kwargs):
    """Convenience function which runs ``flirt -applyxfm ...``."""
    return flirt(src,
                 ref,
                 out=out,
                 applyxfm=True,
                 init=mat,
                 interp=interp,
                 **kwargs)


@wutils.fileOrArray()
@wutils.fslwrapper
def invxfm(inmat, omat):
    """Use ``convert_xfm`` to invert an affine."""
    asrt.assertFileExists(inmat)
    return ['convert_xfm', '-omat', omat, '-inverse', inmat]


@wutils.fileOrArray('inmat1', 'inmat2', 'outmat')
@wutils.fslwrapper
def concatxfm(inmat1, inmat2, outmat):
    """Use ``convert_xfm`` to concatenate two affines."""

    asrt.assertFileExists(inmat1, inmat2)

    cmd = ['convert_xfm',
           '-omat',
           outmat,
           '-concat',
           inmat2,
           inmat1]

    return cmd


@wutils.fileOrImage('infile', 'out', 'reffile', outprefix='out')
@wutils.fileOrArray('init', outprefix='out')
@wutils.fslwrapper
def mcflirt(infile, **kwargs):
    """Wrapper for the ``mcflirt`` command."""

    asrt.assertIsNifti(infile)

    argmap = {
        'twod' : '2d',
    }

    valmap = {
        '2d'      : wutils.SHOW_IF_TRUE,
        'gdt'     : wutils.SHOW_IF_TRUE,
        'meanvol' : wutils.SHOW_IF_TRUE,
        'stats'   : wutils.SHOW_IF_TRUE,
        'mats'    : wutils.SHOW_IF_TRUE,
        'plots'   : wutils.SHOW_IF_TRUE,
        'report'  : wutils.SHOW_IF_TRUE,
    }

    cmd  = ['mcflirt', '-in', infile]
    cmd += wutils.applyArgStyle('-', argmap=argmap, valmap=valmap, **kwargs)

    return cmd
