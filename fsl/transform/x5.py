#!/usr/bin/env python
#
# x5.py - Functions for working with BIDS X5 files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for reading/writing linear/non-linear FSL
transformations from/to BIDS X5 files. The following functions are available:

.. autosummary::
   :nosignatures:

   readLinearX5
   writeLinearX5
   readNonLinearX5
   writeNonLinearX5


An X5 file is a HDF5 container file which stores a linear or non-linear
transformation between a **source** NIfTI image and a **reference** image. In
an X5 file, the source image is referred to as the ``From`` space, and the
reference image the ``To`` space.


Custom HDF5 groups
------------------


HDF5 files are composed primarily of *groups*, *attributes*, and
*datasets*:


 - *Groups* are simply containers for attributes, datasets, and other groups.
 - *Attributes* are strongly-typed scalar values.
 - *Datasets* are strongly-typed, structured N-dimensional arrays.


To simplify the file format definitions below, we shall first define a few
custom HDF5 groups. In the file format definitions, a HDF5 group which is
listed as being of one of these custom types shall contain the
attributes/datasets that are listed here.


*affine*
^^^^^^^^


A HDF5 group which is listed as being of type "affine" contains an affine
transformation, which can be used to transform coordinates from one space into
another. Groups of type "affine" have the following fields:


+---------------+-----------+-------------------------------------------------+
| **Name**      | **Type**  | **Value/Description**                           |
+---------------+-----------+-------------------------------------------------+
| ``Type``      | attribute | ``'linear'``                                    |
+---------------+-----------+-------------------------------------------------+
| ``Transform`` | dataset   | The affine transformation - a ``float64`` array |
|               |           | of shape ``(4, 4)``                             |
+---------------+-----------+-------------------------------------------------+
| ``Inverse``   | dataset   | Optional pre-calculated inverse                 |
+---------------+-----------+-------------------------------------------------+


*space*
^^^^^^^


A HDF5 group which is listed as being of type "space" contains all of the
information required to define the space of a NIfTI image, including its
shape, dimensions, and voxel-to-world affine transformation. The *world*
coordinate system of an image is defined by its ``sform`` or ``qform``
(hereafter referred to as the ``sform``), which is contained in the NIfTI
header.


Groups of type "space" have the following fields:


+-------------+-----------+---------------------------------------------------+
| **Name**    | **Type**  | **Value/Description**                             |
+-------------+-----------+---------------------------------------------------+
| ``Type``    | attribute | ``'image'``                                       |
+-------------+-----------+---------------------------------------------------+
| ``Size``    | attribute | ``uint64`` ``(X, Y, Z)`` voxel dimensions         |
+-------------+-----------+---------------------------------------------------+
| ``Scales``  | attribute | ``float64`` ``(X, Y, Z)`` voxel pixdims           |
+-------------+-----------+---------------------------------------------------+
| ``Mapping`` | affine    | The image voxel-to-world transformation (its      |
|             |           | ``sform``)                                        |
+-------------+-----------+---------------------------------------------------+


Linear X5 files
---------------


Linear X5 transformation files contain an affine transformation matrix of
shape ``(4, 4)``, which can be used to transform **source image world
coordinates** into **reference image world coordinates**.


Linear X5 transformation files are assumed to adhere to the HDF5 structure
defined in the table below.  All fields are required.


+-----------------------------+-----------+-----------------------------------+
| **Name**                    | **Type**  | **Value/Description**             |
+-----------------------------+-----------+-----------------------------------+
| *Metadata*                                                                  |
+-----------------------------+-----------+-----------------------------------+
| ``/Format``                 | attribute | ``'X5'``                          |
+-----------------------------+-----------+-----------------------------------+
| ``/Version``                | attribute | ``'0.0.1'``                       |
+-----------------------------+-----------+-----------------------------------+
| ``/Metadata``               | attribute | JSON string containing            |
|                             |           | unstructured metadata.            |
+-----------------------------+-----------+-----------------------------------+
| *Transformation*                                                            |
+-----------------------------+-----------+-----------------------------------+
| ``/``                       | affine    | Affine transformation from source |
|                             |           | image world coordinates to        |
|                             |           | reference image world coordinates |
+-----------------------------+-----------+-----------------------------------+
| ``/From/``                  | space     | Source image definition           |
+-----------------------------+-----------+-----------------------------------+
| ``/To/``                    | space     | Reference image definition        |
+-----------------------------+-----------+-----------------------------------+


Non-linear X5 transformation files
----------------------------------


Non-linear X5 transformation files contain a non-linear transformation between
a source image coordinate system and a reference image coordinate system. The
transformation is represented as either:

 - A *displacement field*, which is defined in the same space as the reference
   image, and which contains displacements from reference image coordinates to
   source image coordinates.

 - A quadratic or cubic B-spline *coefficient field*, which contains
   coefficients defined in a coarse grid overlaid onto the same space as the
   reference image, and from which a displacement field can be calculated.


Displacement fields
^^^^^^^^^^^^^^^^^^^


A displacement field is a ``float64`` array of shape ``(X, Y, Z, 3)``, defined
in the same space as the reference image (i.e. the reference image is assumed
to have shape ``(X, Y, Z)``. A displacement field may contain either:

 - *relative* displacements, where each voxel in the displacement field
   contains an offset which can be added to the reference image coordinates
   for that voxel, in order to calculate the corresponding source image
   coordinates.

 - *absolute* displacements, where each voxel in the displacement field simply
   contains the source image coordinates which correspond to those reference
   image coordinates.


Coefficient fields
^^^^^^^^^^^^^^^^^^


A coefficient field is a ``float64`` array of shape ``(X, Y, Z, 3)`` which
contains the coefficients of a set of quadratic or cubic B-spline functions
defined on a regular 3D grid overlaid on the reference image voxel coordinate
system. Each coefficient in this grid may be referred to as a *control point*
or a *knot*.


Evaluating the spline functions at a particular location in the grid will
result in a relative displacement which can be applied to that location's
reference image coordinates, in order to determine the corresponding source
image coordinates.


The shape of this coefficient grid is not necessarily the same as the shape of
the reference image grid. For this reason, some additional parameters are
stored in coefficient field files, in a sub-group called ``/Parameters``:

 - The distance between control points, defined in terms of reference image
   voxels
 - An affine transformation which can be used to transform reference image
   voxel coordinates into coefficient field voxel coordinates.


Non-linear coordinate systems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The coordinate systems used in a displacement field, or in a displacement
field that has been generated from a coefficient field, defines relative
displacements from a reference image coordinate system to a source image
coordinate system. The coordinate systems used are not defined in this
specification - they may be voxels, world coordinates, FSL coordinates, or
some other coordinate system.


Howewer, if the transformation does not transform between source and reference
image **world** coordinates, the ``/Pre`` and ``/Post`` affine transformations
must be provided.

The ``/Pre/`` affine transformation will be used to transform reference image
world coordinates into the reference image coordinate system required for use
with the displacement values (or required for the spline coefficient
evaluation).  Similarly, the ``/Post/`` affine transformation will be used to
transform the resulting source image coordinates into the source image world
coordinate system.


Initial affine alignment
^^^^^^^^^^^^^^^^^^^^^^^^


Non-linear transformations are often accompanied by an initial affine
transformation, which provides a coarse global initial alignment that is used
as the starting point for the non-linear registration process. The non-linear
transformation will then typically encode displacements between the
registered, or aligned source image, and the reference image.


Now we have three spaces, and three sets of coordinate systems, to consider:

 1. Source image space - the source image, before initial linear registration
    to the reference image

 2. Aligned-source image space - the source image, after it has been linearly
    transformed to the reference image space

 3. Reference image space

The initial affine registration encodes a transformation between spaces 1 and
2, and the non-linear registration encodes a transformation between spaces 2
and 3. Note that the fields-of-view for spaces 2 and 3 are typically
equivalent.


The initial affine transformation may be included in an X5 file, in the
``/InitialAlignment/`` group.  If provided, this initial transformation is
assumed to provide a transformation:

 - *From* the **source image** world coordinate system (or the coordinate
   system used as input to the ``/Post/`` affine, if provided).

 - *To* the **aligned source** image coordinate system used within the
   non-linear transformation.


File format specification
^^^^^^^^^^^^^^^^^^^^^^^^^


Non-linear X5 transformation files are assumed to adhere to the following
HDF5 structure:


+---------------------+-----------+-------------------------------------------+
| **Name**            | **Type**  | **Value/Description**                     |
+---------------------+-----------+-------------------------------------------+
| *Metadata*                                                                  |
+---------------------+-----------+-------------------------------------------+
| ``/Format``         | attribute | ``'X5'``                                  |
+---------------------+-----------+-------------------------------------------+
| ``/Version``        | attribute | ``'0.0.1'``                               |
+---------------------+-----------+-------------------------------------------+
| ``/Metadata``       | attribute | JSON string containing unstructured       |
|                     |           | metadata.                                 |
+---------------------+-----------+-------------------------------------------+
| *Transformation*                                                            |
+------------------------+-----------+----------------------------------------+
| **Name**               | **Type**  | **Value/Description**                  |
+------------------------+-----------+----------------------------------------+
| ``/Type``              | attribute | ``'nonlinear'``                        |
+------------------------+-----------+----------------------------------------+
| ``/SubType``           | attribute | ``'displacement'`` or                  |
|                        |           | ``'coefficient'``                      |
+------------------------+-----------+----------------------------------------+
| ``/Representation``    | attribute | If ``/SubType`` is ``'displacement'``, |
|                        |           | ``/Representation`` may be either      |
|                        |           | ``'absolute'`` or ``'relative'``.      |
|                        |           | If ``/SubType`` is ``'coefficient'``,  |
|                        |           | ``/Representation`` may be either      |
|                        |           | ``'quadratic bspline'`` or             |
|                        |           | ``'cubic bspline'``.                   |
+------------------------+-----------+----------------------------------------+
| ``/Transform``         | dataset   | The displacement/coefficient field -   |
|                        |           | see above description.                 |
+------------------------+-----------+----------------------------------------+
| ``/Inverse``           | dataset   | Optional pre-calculated inverse        |
+------------------------+-----------+----------------------------------------+
| ``/From/``             | space     | Source image definition                |
+------------------------+-----------+----------------------------------------+
| ``/To/``               | space     | Reference image definition             |
+------------------------+-----------+----------------------------------------+
| ``/Pre/``              | affine    | Optional affine transformation from    |
|                        |           | reference image world coordinates to   |
|                        |           | the reference image coordinate system  |
|                        |           | required by the displacement/          |
|                        |           | coefficient field.                     |
+------------------------+-----------+----------------------------------------+
| ``/Post/``             | affine    | Optional affine transformation from    |
|                        |           | the source image coordinate system     |
|                        |           | produced by the displacement/          |
|                        |           | coefficient field to the source image  |
|                        |           | world coordinate system.               |
+------------------------+-----------+----------------------------------------+
| ``/InitialAlignment/`` | affine    | Optional initial affine registration   |
|                        |           | from the source image to the reference |
|                        |           | image.                                 |
+------------------------+-----------+----------------------------------------+
| *Coefficient field parameters* (required for ``'coefficient'`` files)       |
+-----------------------------------+-----------+-----------------------------+
| **Name**                          | **Type**  | **Value/Description**       |
+-----------------------------------+-----------+-----------------------------+
| ``/Parameters/Spacing``           | attribute | ``uint64`` ``(X, Y, Z)``    |
|                                   |           | knot spacing (defined in    |
|                                   |           | reference image voxels)     |
+-----------------------------------+-----------+-----------------------------+
| ``/Parameters/ReferenceToField/`` | affine    | Reference image voxel to    |
|                                   |           | coefficient field voxel     |
|                                   |           | affine transformation.      |
+-----------------------------------+-----------+-----------------------------+
"""


import json

import numpy   as np
import nibabel as nib
import h5py

import fsl.version as version
from . import         affine
from . import         nonlinear


X5_FORMAT  = 'X5'
X5_VERSION = '0.0.1'


class InvalidFileError(Exception):
    """Error raised if an invalid/incompatible file is detected. """
    pass


def _writeMetadata(group):
    """Writes a metadata block into the given group.

    :arg group: A ``h5py.Group`` object.
    """
    group.attrs['Format']   = X5_FORMAT
    group.attrs['Version']  = X5_VERSION
    group.attrs['Metadata'] = json.dumps({'fslpy' : version.__version__})


def _validateMetadata(group):
    """Reads a metadata block from the given group, and raises an
    :exc:`InvalidFileError` if it does not look valid.
    """

    try:
        format  = group.attrs['Format']
        version = group.attrs['Version']

    except Exception:
        raise InvalidFileError('File does not appear to be an X5 file')

    if (format != X5_FORMAT) or (version != X5_VERSION):
        raise InvalidFileError('Incompatible format/version (required: {}/{}, '
                               'present: {}/{})'.format(X5_FORMAT, X5_VERSION,
                                                        format, version))


def _readAffine(group):
    """Reads an affine from the given group,

    :arg group: A ``h5py.Group`` object.
    :returns:   ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    if group.attrs['Type'] != 'linear':
        raise ValueError('Not a linear transform')

    xform = np.array(group['Transform'])

    if xform.shape != (4, 4):
        raise ValueError('Not a linear transform')

    return xform


def _writeAffine(group, xform):
    """Writes the given affine transformation and its inverse to the given
    group.

    :arg group: A ``h5py.Group`` object.
    :arg xform: ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    xform = np.asarray(xform,                 dtype=np.float64)
    inv   = np.asarray(affine.inverse(xform), dtype=np.float64)

    group.attrs['Type'] = 'linear'
    group.create_dataset('Transform', data=xform)
    group.create_dataset('Inverse',   data=inv)


def _readSpace(group):
    """Reads a "space" group, defining a source or reference space.

    :arg group: A ``h5py.Group`` object.
    :returns:   :class:`.Nifti` object. defining the mapping
    """

    import fsl.data.image as fslimage

    if group.attrs['Type'] != 'image':
        raise ValueError('Not an image mapping')

    shape  = group.attrs['Size']
    pixdim = group.attrs['Scales']
    xform  = _readAffine(group['Mapping'])

    hdr = nib.Nifti2Header()
    hdr.set_data_shape(shape)
    hdr.set_zooms(     pixdim)
    hdr.set_sform(     xform, 'aligned')
    return fslimage.Nifti(hdr)


def _writeSpace(group, img):
    """Writes a space specified by ``img`` to the given group.

    :arg group: A ``h5py.Group`` object.
    :arg img:   :class:`.Nifti` object. defining the mapping
    """
    group.attrs['Type']   = 'image'
    group.attrs['Size']   = np.asarray(img.shape[ :3], np.uint32)
    group.attrs['Scales'] = np.asarray(img.pixdim[:3], np.float32)

    mapping = group.create_group('Mapping')
    _writeAffine(mapping, img.getAffine('voxel', 'world'))


def _readDisplacementField(group):
    """
    """

    field    = np.array(group['Transform'])
    dispType = group.attrs['Representation']
    src      = _readSpace( group['From'])
    ref      = _readSpace( group['To'])
    pre      = _readAffine(group['Pre'])
    post     = _readAffine(group['Post'])
    srcToRef = _readAffine(group['InitialAlignment'])

    refSpace = affine.identify(ref, pre,  from_='world')[1]
    srcSpace = affine.identify(src, post, to='world')[   0]

    return nonlinear.DisplacementField(field,
                                       src,
                                       ref,
                                       srcSpace=srcSpace,
                                       refSpace=refSpace,
                                       srcToRefMat=srcToRef,
                                       dispType=dispType)


def _readCoefficientField(group):
    """
    """
    field     = np.array(group['Transform'])
    fieldType = group.attrs['Representation']
    src       = _readSpace( group['From'])
    ref       = _readSpace( group['To'])
    pre       = _readAffine(group['Pre'])
    post      = _readAffine(group['Post'])
    srcToRef  = _readAffine(group['InitialAlignment'])

    spacing    = group['Parameters'].attrs['Spacing']
    refToField = _readAffine(group['Parameters']['ReferenceToField'])
    fieldToRef = affine.inverse(refToField)

    refSpace = affine.identify(ref, pre,  from_='world')[1]
    srcSpace = affine.identify(src, post, to='world')[   0]

    return nonlinear.CoefficientField(field,
                                      src,
                                      ref,
                                      srcSpace=srcSpace,
                                      refSpace=refSpace,
                                      fieldType=fieldType,
                                      knotSpacing=spacing,
                                      srcToRefMat=srcToRef,
                                      fieldToRefMat=fieldToRef)



def readLinearX5(fname):
    """Read a linear X5 transformation file from ``fname``.

    :return: A tuple containing:

              - A ``(4, 4)`` ``numpy`` array containing the affine
                transformation
              - A :class:`.Nifti` instance representing the source space
              - A :class:`.Nifti` instance representing the reference space
    """
    with h5py.File(fname, 'r') as f:
        _validateMetadata(   f['/'])
        xform = _readAffine( f['/'])
        src   = _readSpace(  f['/From'])
        ref   = _readSpace(  f['/To'])

    return xform, src, ref


def writeLinearX5(fname, xform, src, ref):
    """Write a linear transformation to the specified file.

    :arg fname: File name to write to
    :arg xform: ``(4, 4)`` ``numpy`` array containing the affine transformation
    :arg src:   :class:`.Nifti` image representing the source space
    :arg ref:   :class:`.Nifti` image representing the reference
    """

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)
        _writeAffine(f, xform)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeSpace(from_, src)
        _writeSpace(to,    ref)


def readNonLinearX5(fname):
    """
    """

    from . import nonlinear

    with h5py.File(fname, 'r') as f:
        field = _readNonLinearTransform(f['/'])
        src   = _readSpace(f['/From'])
        ref   = _readSpace(f['/To'])

    # TODO coefficient fields
    return nonlinear.DisplacementField(field,
                                       src=src,
                                       ref=ref,
                                       srcSpace='world',
                                       refSpace='world')


def writeNonLinearX5(fname, field):
    """
    """

    # TODO coefficient fields

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)
        _writeNonLinearTransform(f, field.data)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeLinearMapping(from_, field.src)
        _writeLinearMapping(to,    field.ref)
