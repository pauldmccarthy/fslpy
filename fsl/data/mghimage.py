#!/usr/bin/env python
#
# mghimage.py - The MGHImage class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MGHImage` class, which can be used to load
Freesurfer ``mgh``/``mgz`` image files.
"""


import os.path as op
import            pathlib

import numpy   as np
import nibabel as nib

import fsl.utils.path       as fslpath
import fsl.transform.affine as affine
import fsl.data.image       as fslimage


ALLOWED_EXTENSIONS = ['.mgz', '.mgh']
"""List of file extensions interpreted as MGH image files.
"""


EXTENSION_DESCRIPTIONS = ['Compressed MGH image', 'MGH image']
"""A description for each of the :attr:`ALLOWED_EXTENSIONS`."""


class MGHImage(fslimage.Image):
    """The ``MGHImage`` class is a NIFTI :class:`Image` which has been converted
    from a Freesurfer ``.mgh`` file.

    See:
     - https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/MghFormat
     - http://nipy.org/nibabel/reference/nibabel.freesurfer.html
    """

    def __init__(self, image, **kwargs):
        """Create a ``MGHImage``.

        :arg image: Name of MGH file, or a
                    ``nibabel.freesurfer.mghformat.MGHImage`` instance.

        All other arguments are passed through to :meth:`Image.__init__`
        """

        if isinstance(image, (str, pathlib.Path)):
            filename = op.abspath(image)
            name     = op.basename(filename)
            image    = nib.load(image)
        else:
            name     = 'MGH image'
            filename = None

        data     = np.asanyarray(image.dataobj)
        xform    = image.affine
        pixdim   = image.header.get_zooms()
        vox2surf = image.header.get_vox2ras_tkr()

        # the image may have an affine which
        # transforms the data into some space
        # with a scaling that is different to
        # the pixdims. So we create a header
        # object with both the affine and the
        # pixdims, so they are both preserved.
        #
        # Note that we have to set the zooms
        # after the s/qform, otherwise nibabel
        # will clobber them with zooms gleaned
        # fron the affine.
        header = nib.nifti1.Nifti1Header()
        header.set_data_shape(data.shape)
        header.set_sform(xform)
        header.set_qform(xform)
        header.set_zooms(pixdim)

        fslimage.Image.__init__(self,
                                data,
                                header=header,
                                name=name,
                                dataSource=filename,
                                **kwargs)

        if filename is not None:
            self.setMeta('mghImageFile', filename)

        self.__voxToSurfMat   = vox2surf
        self.__surfToVoxMat   = affine.invert(vox2surf)
        self.__surfToWorldMat = affine.concat(xform, self.__surfToVoxMat)
        self.__worldToSurfMat = affine.invert(self.__surfToWorldMat)


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


    @property
    def voxToSurfMat(self):
        """Returns an affine which can be used to transform voxel
        coordinates into the surface coordinate system for this image.

        See: http://www.grahamwideman.com/gw/brain/fs/coords/fscoords.htm
        See: https://surfer.nmr.mgh.harvard.edu/fswiki/CoordinateSystems
        """
        return self.__voxToSurfMat


    @property
    def surfToVoxMat(self):
        """Returns an affine which can be used to transform surface
        coordinates into the voxel coordinate system for this image.
        """
        return self.__surfToVoxMat


    @property
    def surfToWorldMat(self):
        """Returns an affine which can be used to transform surface
        coordinates into the world coordinate system for this image.
        """
        return self.__surfToWorldMat


    @property
    def worldToSurfMat(self):
        """Returns an affine which can be used to transform world
        coordinates into the surface coordinate system for this image.
        """
        return self.__worldToSurfMat


def voxToSurfMat(img):
    """Generate an affine which can transform the voxel coordinates of
    the given image into a corresponding Freesurfer surface coordinate
    system (known as "Torig", or "vox2ras-tkr").

    See https://surfer.nmr.mgh.harvard.edu/fswiki/CoordinateSystems

    :arg img: An :class:`.Image` object.

    :return:  A ``(4, 4)`` matrix encoding an affine transformation from the
              image voxel coordinate system to the corresponding Freesurfer
              surface coordinate system.
    """

    zooms = np.array(img.pixdim[:3])
    dims  = img.shape[ :3] * zooms / 2

    xform        = np.zeros((4, 4), dtype=np.float32)
    xform[ 0, 0] = -zooms[0]
    xform[ 1, 2] =  zooms[2]
    xform[ 2, 1] = -zooms[1]
    xform[ 3, 3] = 1
    xform[:3, 3] = [dims[0], -dims[2], dims[1]]

    return xform
