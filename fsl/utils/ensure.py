#!/usr/bin/env python
#
# ensure.py - Functions which ensure things.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a handful of utility functions which attempt to ensure
that some condition is met.

.. autosummary::
   :nosignatures:

   ensureIsImage
"""


import nibabel as nib

import fsl.data.image as fslimage


def ensureIsImage(img):
    """Ensures that the given ``img`` is an in-memory ``nibabel`` object.
    """
    if isinstance(img, str):
        img = fslimage.addExt(img)
        img = nib.load(img)
    return img
