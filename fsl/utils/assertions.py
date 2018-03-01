#!/usr/bin/env python
#
# Miscellaneous assertion functions.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk
#         Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a handful of miscellaneous assertion routines.

.. autosummary::
   :nosignatures:

    assertFileExists
    assertIsNifti3D
    assertIsNifti4D
    assertIsNifti
    assertNiftiShape
    assertIsSurfGifti
    assertIsFuncGifti
    assertIsMelodicDir


The :func:`disabled` context manager can be used to temporarily disable
assertion checks.
"""


import os.path as op
import            contextlib
import nibabel as nib

import fsl.utils.ensure         as ensure
import fsl.data.melodicanalysis as fslma


_DISABLE_ASSERTIONS = False
"""
"""


@contextlib.contextmanager
def disabled():
    """Context manager which allows assertion checks to be temporarily
    disabled.
    """
    global _DISABLE_ASSERTIONS

    oldval              = _DISABLE_ASSERTIONS
    _DISABLE_ASSERTIONS = True

    try:
        yield
    finally:
        _DISABLE_ASSERTIONS = oldval


def _canDisable(func):
    """Decorator used on assertion functions,  allowing them to be disabled
    via the :func:`disabled` context manager.
    """
    def wrapper(*args, **kwargs):
        if not _DISABLE_ASSERTIONS:
            return func(*args, **kwargs)
    return wrapper


@_canDisable
def assertFileExists(*args):
    """Raise an exception if the specified file/folder/s do not exist."""
    for f in args:
        assert op.exists(f), 'file/folder does not exist: {}'.format(f)


@_canDisable
def assertIsNifti3D(*args):
    """Raise an exception if the specified file/s are not 3D nifti."""
    for f in args:
        assertIsNifti(f)
        d = ensure.ensureIsImage(f)
        assert len(d.shape) == 3, \
            'incorrect shape for 3D nifti: {}:{}'.format(d.shape, f)


@_canDisable
def assertIsNifti4D(*args):
    """Raise an exception if the specified file/s are not 4D nifti."""
    for f in args:
        assertIsNifti(f)
        d = ensure.ensureIsImage(f)
        assert len(d.shape) == 4, \
            'incorrect shape for 4D nifti: {}:{}'.format(d.shape, f)


@_canDisable
def assertIsNifti(*args):
    """Raise an exception if the specified file/s are not nifti."""
    for f in args:
        f = ensure.ensureIsImage(f)

        # Nifti2Image derives from Nifti1Image,
        # so we only need to test the latter.
        assert isinstance(f, nib.nifti1.Nifti1Image), \
            'file must be a nifti (.nii or .nii.gz): {}'.format(f)


@_canDisable
def assertNiftiShape(shape, *args):
    """Raise an exception if the specified nifti/s are not specified shape."""
    for fname in args:
        d = ensure.ensureIsImage(fname)
        assert tuple(d.shape) == tuple(shape), \
            'incorrect shape ({}) for nifti: {}:{}'.format(
                shape, d.shape, fname)


@_canDisable
def assertIsSurfGifti(*args):
    """Raise an exception if the specified file/s are not surface gifti."""
    for fname in args:
        assert fname.endswith('.surf.gii'), \
            'file must be a surface gifti (surf.gii): {}'.format(fname)


@_canDisable
def assertIsFuncGifti(*args):
    """Raise an exception if the specified file/s are not functional gifti."""
    for fname in args:
        assert fname.endswith('.func.gii'), \
            'file must be a functional gifti (func.gii): {}'.format(fname)


@_canDisable
def assertIsMelodicDir(path):
    """Raise an exception if the specified path is not a melodic directory.

    :arg path:  Path to melodic directory
    """
    assert fslma.isMelodicDir(path), 'not a melodic directory: {}'.format(path)
