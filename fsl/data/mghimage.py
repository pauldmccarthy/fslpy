#!/usr/bin/env python
#
# mghimage.py - The MGHImage class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MGHImage` class, which can be used to load
Freesurfer ``mgh``/``mgz`` image files.

.. autosummary::
   :nosignatures:

   looksLikeMGHImage
"""


import six

import nibabel as nib

import fsl.data.image as fslimage


class MGHImage(fslimage.Image):
    """The ``MGHImage`` class is a NIFTI :class:`Image` which has been converted
    from a Freesurfer ``.mgh`` file.

    .. see:: https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/MghFormat

    .. see:: http://nipy.org/nibabel/reference/nibabel.freesurfer.html
    """

    def __init__(self, image, *args, **kwargs):
        """Create a ``MGHImage``.

        :arg image: Name of MGH file, or a
                    ``nibabel.freesurfer.mghformat.MGHImage`` instance.

        All other arguments are passed through to :meth:`Image.__init__`
        """

        if isinstance(image, six.string_types):
            filename = image
            image    = nib.load(image)
        else:
            filename = None

        data   = image.get_data()
        affine = image.affine

        fslimage.Image.__init__(self, data, xform=affine)

        if filename is not None:
            self.setMeta('mghImageFile', filename)


    @property
    def mghImageFile(self):
        """If this ``MGHImage`` was loaded from a file, returns the file
        name. Otherwise returns ``None``.
        """
        return self.getMeta('mghImageFile', None)



ALLOWED_EXTENSIONS = ['.mgz', '.mgh']
"""List of file extensions interpreted as MGH image files.
"""


EXTENSION_DESCRIPTIONS = ['Compressed MGH image', 'MGH image']
"""A description for each of the :attr:`ALLOWED_EXTENSIONS`."""


def looksLikeMGHImage(filename):
    """Returns ``True`` if the given file looks like a MGH image, ``False``
    otherwise.
    """
    return fslimage.looksLikeImage(filename, ALLOWED_EXTENSIONS)
