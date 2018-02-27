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


import os.path as op

import            six
import nibabel as nib

import fsl.utils.path as fslpath
import fsl.data.image as fslimage


ALLOWED_EXTENSIONS = ['.mgz', '.mgh']
"""List of file extensions interpreted as MGH image files.
"""


EXTENSION_DESCRIPTIONS = ['Compressed MGH image', 'MGH image']
"""A description for each of the :attr:`ALLOWED_EXTENSIONS`."""


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
            filename = op.abspath(image)
            name     = op.basename(filename)
            image    = nib.load(image)
        else:
            name     = 'MGH image'
            filename = None

        data   = image.get_data()
        affine = image.affine

        fslimage.Image.__init__(self,
                                data,
                                xform=affine,
                                name=name,
                                dataSource=filename)

        if filename is not None:
            self.setMeta('mghImageFile', filename)


    def save(self, filename=None):
        """Overrides :meth:`.Image.save`.  If a ``filename`` is not provided,
        converts the original (MGH) file name into a NIFTI filename, before
        passing it to the :meth:`.Image.save` method.
        """
        if filename is None:
            filename = self.dataSource

        filename = fslpath.removeExt(filename, ALLOWED_EXTENSIONS)

        return fslimage.Image.save(self, filename)


    @property
    def mghImageFile(self):
        """If this ``MGHImage`` was loaded from a file, returns the file
        name. Otherwise returns ``None``.
        """
        return self.getMeta('mghImageFile', None)
