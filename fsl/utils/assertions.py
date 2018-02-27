#!/usr/bin/env python
#
# Miscellaneous assertion functions.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk
#         Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a handful of miscellaneous assertion routines.
"""


import os.path as op
import nibabel as nib

import fsl.data.melodicanalysis as fslma


def assertFileExists(*args):
    """Raise an exception if the specified file/folder/s do not exist."""
    for f in args:
        assert op.exists(f), 'file/folder does not exist: {}'.format(f)


def assertIsNifti3D(*args):
    """Raise an exception if the specified file/s are not 3D nifti."""
    for f in args:
        assertIsNifti(f)
        d = nib.load(f)
        assert len(d.shape) == 3, \
            'incorrect shape for 3D nifti: {}:{}'.format(d.shape, f)


def assertIsNifti4D(*args):
    """Raise an exception if the specified file/s are not 4D nifti."""
    for f in args:
        assertIsNifti(f)
        d = nib.load(f)
        assert len(d.shape) == 4, \
            'incorrect shape for 4D nifti: {}:{}'.format(d.shape, f)


def assertIsNifti(*args):
    """Raise an exception if the specified file/s are not nifti."""
    for f in args:
        assert isinstance(f, nib.nifti1.Nifti1Image) or \
            f.endswith('.nii.gz') or f.endswith('.nii'), \
            'file must be a nifti (.nii or .nii.gz): {}'.format(f)


def assertNiftiShape(shape, *args):
    """Raise an exception if the specified nifti/s are not specified shape."""
    for fname in args:
        d = nib.load(fname)
        assert d.shape == shape, \
            'incorrect shape ({}) for nifti: {}:{}'.format(
                shape, d.shape, fname)


def assertIsSurfGifti(*args):
    """Raise an exception if the specified file/s are not surface gifti."""
    for fname in args:
        assert fname.endswith('.surf.gii'), \
            'file must be a surface gifti (surf.gii): {}'.format(fname)


def assertIsFuncGifti(*args):
    """Raise an exception if the specified file/s are not functional gifti."""
    for fname in args:
        assert fname.endswith('.func.gii'), \
            'file must be a functional gifti (func.gii): {}'.format(fname)


def assertIsMelodicDir(path):
    """Raise an exception if the specified path is not a melodic directory.

    :arg path:  Path to melodic directory
    """
    assert fslma.isMelodicDir(path), 'not a melodic directory: {}'.format(path)
