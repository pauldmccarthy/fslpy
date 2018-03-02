#!/usr/bin/env python
#
# flirt.py - Wrappers for FLIRT commands.
#
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


import fsl.utils.run        as run
import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.required('src', 'ref')
@wutils.fileOrImage('src', 'ref', 'out', 'wmseg', 'fieldmap', 'fieldmapmask')
@wutils.fileOrArray('init', 'omat', 'wmcoords', 'wmnorms')
def flirt(src, ref, **kwargs):
    """Wrapper around the ``flirt`` command. """

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


@wutils.fileOrImage('src', 'ref', 'out')
@wutils.fileOrArray('mat')
def applyxfm(src, ref, mat, out, interp='spline'):
    """Convenience function which runs ``flirt -applyxfm ...``."""
    return flirt(src,
                 ref,
                 out=out,
                 applyxfm=True,
                 init=mat,
                 interp=interp)


@wutils.fileOrArray
def invxfm(inmat, omat):
    """Use ``convert_xfm`` to invert an affine."""
    asrt.assertFileExists(inmat)

    cmd = 'convert_xfm -omat {} -inverse {}'.format(omat, inmat)
    return run.runfsl(cmd)


@wutils.fileOrArray('inmat1', 'inmat2', 'outmat')
def concatxfm(inmat1, inmat2, outmat):
    """Use ``convert_xfm`` to concatenate two affines."""

    asrt.assertFileExists(inmat1, inmat2)

    cmd = ['convert_xfm',
           '-omat',
           outmat,
           '-concat',
           inmat2,
           inmat1]

    return run.runfsl(cmd)


@wutils.fileOrImage('infile', 'out', 'reffile')
@wutils.fileOrArary('init')
def mcflirt(infile, **kwargs):
    """Wrapper around the ``mcflirt`` command."""

    asrt.assertIsNifti(infile)

    cmd  = ['mcflirt', '-in', infile]
    cmd += wutils.applyArgStyle('-', **kwargs)

    return run.runfsl(cmd)