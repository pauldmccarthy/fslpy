#!/usr/bin/env python
#
# ensure.py - Functions which ensure things.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#         Vasilis Karlaftis <vasilis.karlaftis@ndcn.ox.ac.uk>
#
"""This module contains a handful of utility functions which attempt to ensure
that some condition is met.

.. autosummary::
   :nosignatures:

   ensureIsImage
   ensureIsMRSBasis
"""

import pathlib
import nibabel as nib

import fsl.data.image as fslimage


def ensureIsImage(img):
    """Ensures that the given ``img`` is an in-memory ``nibabel`` object.
    """
    if isinstance(img, (str, pathlib.Path)):
        img = fslimage.addExt(img)
        img = nib.load(img)
    return img


def ensureIsMRSBasis(basis):
    """Ensures that the given ``basis`` is an in-memory ``Basis`` object.
    """
    if isinstance(basis, (str, pathlib.Path)):
        from fsl_mrs.utils import mrs_io
        basis = mrs_io.read_basis(basis)
    return basis
