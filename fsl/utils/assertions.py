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


def assertFileExists(*args):
    """Raise an exception if the specified file/folder/s do not exist."""
    for f in args:
        assert op.exists(f), "file/folder does not exist: {0}".format(f)


def assertIsNifti3D(*args):
    """Raise an exception if the specified file/s are not 3D nifti."""
    for f in args:
        assertIsNifti(f)
        d = nib.load(f)
        assert len(d.shape) == 3, \
            "incorrect shape for 3D nifti: {0}:{1}".format(d.shape, f)


def assertIsNifti4D(*args):
    """Raise an exception if the specified file/s are not 4D nifti."""
    for f in args:
        assertIsNifti(f)
        d = nib.load(f)
        assert len(d.shape) == 4, \
            "incorrect shape for 4D nifti: {0}:{1}".format(d.shape, f)


def assertIsNifti(*args):
    """Raise an exception if the specified file/s are not nifti."""
    for f in args:
        assert isinstance(f, nib.nifti1.Nifti1Image) or \
            f.endswith('.nii.gz') or f.endswith('.nii'), \
            "file must be a nifti (.nii or .nii.gz): {0}".format(f)


def assertNiftiShape(shape, *args):
    """Raise an exception if the specified nifti/s are not specified shape."""
    for fname in args:
        d = nib.load(fname)
        assert d.shape == shape, \
            "incorrect shape ({2}) for nifti: {0}:{1}".format(d.shape, fname,
                                                              shape)


def assertIsSurfGifti(*args):
    """Raise an exception if the specified file/s are not surface gifti."""
    for fname in args:
        assert fname.endswith('.surf.gii'), \
            "file must be a surface gifti (surf.gii): {0}".format(fname)


def assertIsFuncGifti(*args):
    """Raise an exception if the specified file/s are not functional gifti."""
    for fname in args:
        assert fname.endswith('.func.gii'), \
            "file must be a functional gifti (func.gii): {0}".format(fname)

def assertIsMelodicDir(path):
    """Raise an exception if the specified path is not a melodic directory.

    :arg path:     Path to melodic directory
    :type path:    string
    """
    assert op.exists(path), "melodic dir does not exist: {0}".format(path)
    assert path.endswith('.ica'), \
        "melodic directory must end in *.ica: {0}".format(path)
    assert op.exists(op.join(path, 'melodic_IC.nii.gz')), \
        "melodic directy must contain a file called melodic_IC.nii.gz"
    assert op.exists(op.join(path, 'melodic_mix')), \
        "melodic directy must contain a file called melodic_mix"
    assert op.exists(op.join(path, 'melodic_FTmix')), \
        "melodic directy must contain a file called melodic_FTmix"
