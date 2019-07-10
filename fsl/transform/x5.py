#!/usr/bin/env python
#
# x5.py - Functions for working with BIDS X5 files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for reading/writing linear/non-linear FSL
transformations from/to BIDS X5 files.


An X5 file is a HDF5 container file which stores a linear or non-linear
transformation between a **source** NIfTI image and a **refernece** image. In
an X5 file, the source image is referred to as the ``From`` space, and the
reference image the ``To`` space.


Custom HDF5 groups
------------------


HDF5 files are composed of *groups*, *attributes*, and *datasets*. Groups are
simply containers for attributes, datasets, and other groups. Attributes are
strongly-typed scalar values. Datasets are strongly-typed, structured
N-dimensional arrays.


To simplify the file format efinitions below, we shall first define a few
custom HDF5 groups. In the file format definitions, a HDF5 group which is
listed as being of one of these custom types shall contain the
attributes/datasets that are listed here.


*affine*
^^^^^^^^


A HDF5 group which is listed as being of type "affine" contains an affine
transformation, which can be used to transform coordinates from one space into
another. Groups of type "affine" have the following fields:


+---------------+-----------+-------------------------------------------------+
| Name          | Type      | Value/Description                               |
+---------------+-----------+-------------------------------------------------+
| ``Type``      | attribute | ``'linear'``                                    |
| ``Transform`` | dataset   | The transformation itself - a 4x4 ``float64``   |
|               |           | affine transformation                           |
| ``Inverse``   | dataset   | Optional pre-calculated inverse                 |
+---------------+-----------+-------------------------------------------------+


*mapping*
^^^^^^^^^


A HDF5 group which is listed as being of type "mapping" contains all of the
information required to define the space of a NIfTI image, including its
dimensions, and voxel-to-world affine transformation. The *world* coordinate
system of an image is defined by its ``sform`` or ``qform`` (hereafter
referred to as the ``sform``), which is contained in the NIfTI header.


Groups of type "mapping" have the following fields:


+-------------+-----------+---------------------------------------------------+
| Name        | Type      | Value/Description                                 |
+-------------+-----------+---------------------------------------------------+
| ``Type``    | attribute | ``'image'``                                       |
| ``Size``    | attribute | ``uint64`` ``(X, Y, Z)`` voxel dimensions         |
| ``Scales``  | attribute | ``float64`` ``(X, Y, Z)`` voxel pixdims           |
| ``Mapping`` | affine    | The image voxel-to-world transformation (its      |
|             |           | "sform")                                          |
+-------------+-----------+---------------------------------------------------+


Linear X5 files
---------------


Linear X5 transformation files contain an affine transformation matrix of
shape ``(4, 4)``, which can be used to transform **source image world
coordinates into reference image world coordinates**.


Linear X5 transformation files are assumed to adhere to the HDF5 structure
defined in the table below.  All fields are required.


+-----------------------------+-----------+-----------------------------------+
| Name                        | Type      | Value/Description                 |
+-----------------------------+-----------+-----------------------------------+
| *Metadata*                                                                  |
+-----------------------------+-----------+-----------------------------------+
| ``/Format``                 | attribute | ``'X5'``                          |
| ``/Version``                | attribute | ``'0.0.1'``                       |
| ``/Metadata``               | attribute | JSON string containing            |
|                             |           | unstructured metadata.            |
+-----------------------------+-----------+-----------------------------------+
| *Transformation*                                                            |
+-----------------------------+-----------+-----------------------------------+
| ``/From/``                  | mapping   | Source image mapping              |
| ``/To/``                    | mapping   | Reference image mapping           |
| ``/``                       | affine    | Affine transformation from source |
|                             |           | image world coordinates to        |
|                             |           | reference image world coordinates |
+-----------------------------+-----------+-----------------------------------+


Non-linear X5 transformation files
----------------------------------


Non-linear X5 transformation files contain a non-linear transformation between
a source image coordinate system and a reference image coordinate system. The
transformation is represented as either:

 - A *displacement field*, which is defined in the same space as the reference
   image, and which contains displacements.

 - A quadratic or cubic B-spline *coefficient field*, which contains
   coefficients defined in a coarse grid which overlays the same space as the
   reference image, and from which a displacement field can be calculated.

Displacement fields may contain either:

 - *relative displacements*, which contains displacements *from* the
   reference image coordinates *to* the source image coordinates (i.e. add the
   displacements to the reference image coordinates to get the corresponding
   source image coordinates)

 - *absolute displacement* which simply contain the source image coordinates
   at each voxel in the reference image space.


Displacement field transformations define displacements between the refernece
image *world* coordinate system, and the source image *world* coordinate
system.


The displacement field generated from a coefficient field defines relative
displacements from a reference image space to a source image space. These
spaces are undefined; however, the ``/Pre`` affine transformation may be used
to transform reference image world coordinates into the reference image space,
and the ``/Post`` affine transformation may be used to transform the resulting
source image coordinates into the source image world coordinate system.


Non-linear X5 transformation files are assumed to adhere to the following
HDF5 structure::


+-----------------------------+-----------+-----------------------------------+
| Name                        | Type      | Value/Description                 |
+-----------------------------+-----------+-----------------------------------+
| *Metadata* - same as for linear transformation files                        |
+-----------------------------------------------------------------------------+
| *Transformation*                                                            |
+-----------------------------+-----------+-----------------------------------+
| ``/Type``                   | attribute | ``'nonlinear'``                   |
| ``/SubType``                | attribute | ``'displacement'`` or             |
|                             |           | ``'coefficient'``                 |
| ``/Representation``         | attribute | If ``/SubType`` is                |
|                             |           | ``'displacement'``, its           |
|                             |           | ``/Representation`` may be either |
|                             |           | ``'absolute'`` or ``'relative'``. |
|                             |           | If ``/SubType`` is                |
|                             |           | ``'coefficient'``, its            |
|                             |           | ``/Representation`` may be either |
|                             |           | ``'quadratic bspline'`` or        |
|                             |           | ``'cubic bspline'``.              |
| ``/Transform``              | dataset   | The transformation itself - see   |
|                             |           | above.                            |
| ``/Inverse``                | dataset   | Optional pre-calculated inverse   |
| ``/From/``                  | mapping   | Source image mapping              |
| ``/To/``                    | mapping   | Reference image mapping           |
|-----------------------------+-----------+-----------------------------------+
| *Coefficient field parameters* (required for ``'coefficient'`` files)       |
|-----------------------------+-----------+-----------------------------------+
| ``/Parameters/Spacing``          | attribute |
| ``/Parameters/ReferenceToField`` | affine    |    | attribute |
+-----------------------------+-----------+-----------------------------------+

"""


import json

import numpy   as np
import nibabel as nib
import h5py

import fsl.version as version
from . import         affine


X5_FORMAT  = 'X5'
X5_VERSION = '0.0.1'


def _writeMetadata(group):
    """Writes a metadata block into the given group.

    :arg group: A ``h5py.Group`` object.
    """
    group.attrs['Format']   = X5_FORMAT
    group.attrs['Version']  = X5_VERSION
    group.attrs['Metadata'] = json.dumps({'fslpy' : version.__version__})


def _readLinearTransform(group):
    """Reads a linear transformation from the given group,

    :arg group: A ``h5py.Group`` object.
    :returns:   ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    if group.attrs['Type'] != 'linear':
        raise ValueError('Not a linear transform')

    xform = np.array(group['Transform'])

    if xform.shape != (4, 4):
        raise ValueError('Not a linear transform')

    return xform


def _writeLinearTransform(group, xform):
    """Writes the given linear transformation and its inverse to the given
    group.

    :arg group: A ``h5py.Group`` object.
    :arg xform: ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    xform = np.asarray(xform,                 dtype=np.float64)
    inv   = np.asarray(affine.inverse(xform), dtype=np.float64)

    group.attrs['Type'] = 'linear'
    group.create_dataset('Transform', data=xform)
    group.create_dataset('Inverse',   data=inv)


def _readLinearMapping(group):
    """Reads a linear mapping, defining a source or reference space, from the
    given group.

    :arg group: A ``h5py.Group`` object.
    :returns:   :class:`.Nifti` object. defining the mapping
    """

    import fsl.data.image as fslimage

    if group.attrs['Type'] != 'image':
        raise ValueError('Not an image mapping')

    shape  = group.attrs['Size']
    pixdim = group.attrs['Scales']
    xform  = _readLinearTransform(group['Mapping'])

    hdr = nib.Nifti2Header()
    hdr.set_data_shape(shape)
    hdr.set_zooms(     pixdim)
    hdr.set_sform(     xform, 'aligned')
    return fslimage.Nifti(hdr)


def _writeLinearMapping(group, img):
    """Writes a linear mapping specified by ``img`` to the given group.

    :arg group: A ``h5py.Group`` object.
    :arg img:   :class:`.Nifti` object. defining the mapping
    """
    group.attrs['Type']   = 'image'
    group.attrs['Size']   = np.asarray(img.shape[ :3], np.uint32)
    group.attrs['Scales'] = np.asarray(img.pixdim[:3], np.float32)

    mapping = group.create_group('Mapping')
    _writeLinearTransform(mapping, img.getAffine('voxel', 'world'))


def _readNonLinearTransform(group):
    if group.attrs['Type'] != 'nonlinear':
        raise ValueError('Not a nonlinear transform')
    return np.array(group['Transform'])


def _writeNonLinearTransform(group, field):
    """
    """
    group.attrs['Type'] = 'nonlinear'
    group.create_dataset('Transform', data=field, dtype=np.float32)


def readLinearX5(fname):
    """
    """
    with h5py.File(fname, 'r') as f:
        xform = _readLinearTransform(f['/'])
        src   = _readLinearMapping(  f['/From'])
        ref   = _readLinearMapping(  f['/To'])

    return xform, src, ref


def writeLinearX5(fname, xform, src, ref):
    """
    """

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)
        _writeLinearTransform(f, xform)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeLinearMapping(from_, src)
        _writeLinearMapping(to,    ref)


def readNonLinearX5(fname):
    """
    """

    from . import nonlinear

    with h5py.File(fname, 'r') as f:
        field = _readNonLinearTransform(f['/'])
        src   = _readLinearMapping(f['/From'])
        ref   = _readLinearMapping(f['/To'])

    # TODO coefficient fields
    return nonlinear.DisplacementField(field,
                                       src=src,
                                       ref=ref,
                                       srcSpace='world',
                                       refSpace='world')


def writeNonLinearX5(fname, field):
    """
    ::
        /Format                       # "X5"
        /Version                      # "0.0.1"
        /Metadata                     # json string containing unstructured metadata

        /Transform                    # the displacement/coefficient field itself
        /Type                         # "nonlinear"
        /SubType                      # "displacement" / "deformation"
        /Representation               # "cubic bspline" / "quadratic bspline"
        /Inverse                      # optional pre-calculated inverse

        /Pre/Type                     # "linear"
        /Pre/Transform                # ref world-to-[somewhere], to prepare ref
                                      # world coordinates as inputs to the nonlinear
                                      # transform
        /Pre/Inverse                  # optional pre-calculated inverse
        /Post/Type                    #  "linear"
        /Post/Transform               # source [somewhere]-to-world, to transform
                                      # source coordinates produced by the nonlinear
                                      # transform into world coordinates
        /Post/Inverse                 # optional pre-calculated inverse

        /From/Type                    # "image"
        /From/Size                    # voxel dimensions
        /From/Scales                  # voxel pixdims
        /From/Mapping/Transform       # source voxel-to-world sform
        /From/Mapping/Type            # "linear"
        /From/Mapping/Inverse         # optional inverse

        /To/Type                      # "image"
        /To/Size                      # voxel dimensions
        /To/Scales                    # voxel pixdims
        /To/Mapping/Transform         # reference voxel-to-world sform
        /To/Mapping/Type              # "linear"
        /To/Mapping/Inverse           # optional inverse
    """  # noqa

    # TODO coefficient fields

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)
        _writeNonLinearTransform(f, field.data)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeLinearMapping(from_, field.src)
        _writeLinearMapping(to,    field.ref)
