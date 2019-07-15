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


X5 files enable a transformation between **source image world coordinates**
and **reference image world coordinates**.  The *world coordinate system* of
an image is defined by its ``sform`` or ``qform`` (hereafter referred to as
the ``sform``), which is contained in the NIfTI header.


Custom HDF5 groups
==================


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
--------


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
-------


A HDF5 group which is listed as being of type "space" contains all of the
information required to define the space of a NIfTI image, including its
shape, dimensions, and voxel-to-world affine transformation.


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
===============


Linear X5 transformation files contain an affine transformation matrix of
shape ``(4, 4)``, which can be used to transform source image world
coordinates into reference image world coordinates.


Linear X5 transformation files are assumed to adhere to the HDF5 structure
defined in the table below.  All fields are required.


+---------------+-----------+-------------------------------------------------+
| **Name**      | **Type**  | **Value/Description**                           |
+---------------+-----------+-------------------------------------------------+
| *Metadata*                                                                  |
+---------------+-----------+-------------------------------------------------+
| ``/Format``   | attribute | ``'X5'``                                        |
+---------------+-----------+-------------------------------------------------+
| ``/Version``  | attribute | ``'0.0.1'``                                     |
+---------------+-----------+-------------------------------------------------+
| ``/Metadata`` | attribute | JSON string containing unstructured metadata.   |
+---------------+-----------+-------------------------------------------------+
| *Transformation*                                                            |
+---------------+-----------+-------------------------------------------------+
| ``/``         | affine    | Affine transformation from source image world   |
|               |           | coordinates to reference image world            |
|               |           | coordinates                                     |
+---------------+-----------+-------------------------------------------------+
| ``/From/``    | space     | Source image definition                         |
+---------------+-----------+-------------------------------------------------+
| ``/To/``      | space     | Reference image definition                      |
+---------------+-----------+-------------------------------------------------+


Storage of FSL FLIRT matrices in linear X5 files
------------------------------------------------


FLIRT outputs the result of a linear registration from a source image to a
reference image as an affine matrix of shape ``(4, 4)``. This matrix encodes a
transformation from source image **FSL coordinates** to reference image **FSL
coordinates** [*]_.


In contrast, X5 matrices encode a transformation in **world coordinates**,
i.e. they can be used to transform coordinates from the source image to the
reference image, after both images have been transformed into a common
coordinate system via their respective ``sform`` affines.


.. image:: images/x5_linear_transform_file.png
   :width: 80%
   :align: center


The :mod:`fsl.transform.flirt` module contains functions for converting
between FLIRT-style matrices and X5 style matrices.


.. [*] For a given image, FSL coordinates are voxel coordinates scaled by the
       ``pixdim`` values in the NIFTI header, and an inversion along the X
       axis if the voxel-to-world affine (the ``sform``) has a positive
       determinant.


Non-linear X5 files
===================


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
-------------------


A displacement field is a ``float64`` array of shape ``(X, Y, Z, 3)``, defined
in the same space as the reference image. A displacement field may contain
either:

 - *relative* displacements, where each voxel in the displacement field
   contains an offset which can be added to the reference image coordinates
   for that voxel, in order to calculate the corresponding source image
   coordinates.

 - *absolute* displacements, where each voxel in the displacement field simply
   contains the source image coordinates which correspond to those reference
   image coordinates.


Coefficient fields
------------------


A coefficient field is a ``float64`` array of shape ``(X, Y, Z, 3)`` which
contains the coefficients of a set of quadratic or cubic B-spline functions
defined on a regular 3D grid overlaid on the reference image voxel coordinate
system. Each coefficient in this grid may be referred to as a *control point*
or a *knot*.


Evaluating the spline functions at a particular location in the grid will
result in a relative displacement which can be added to that location's
reference image coordinates, in order to determine the corresponding source
image coordinates.


The shape of this coefficient grid is not necessarily the same as the shape of
the reference image grid. For this reason, some additional parameters are
stored in coefficient field files, in a sub-group called ``/Parameters/``:

 - The distance between control points, defined in terms of reference image
   voxels.
 - An affine transformation which can be used to transform reference image
   voxel coordinates into coefficient field voxel coordinates.


Non-linear coordinate systems
-----------------------------


The coordinate systems used in a displacement field, or in a displacement
field that has been generated from a coefficient field, defines relative
displacements from a reference image coordinate system to a source image
coordinate system. The coordinate systems used are not defined in this
specification - they may be voxels, world coordinates, FSL coordinates, or
some other coordinate system.


Howewer, if the transformation does not transform between source and reference
image **world coordinates**, the ``/Pre/`` and ``/Post/`` affine
transformations must be provided.


The ``/Pre/`` affine transformation will be used to transform reference image
world coordinates into the reference image coordinate system required for use
with the displacement values (or required for the spline coefficient
evaluation).  Similarly, the ``/Post/`` affine transformation will be used to
transform the resulting source image coordinates into the source image world
coordinate system.


Initial linear registration
---------------------------


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

The initial affine registration calculates a transformation between spaces 1
and 2, and the non-linear registration calculates a transformation between
spaces 2 and 3. Note that the fields-of-view for spaces 2 and 3 are typically
equivalent.


This initial affine transformation may be included in an X5 file, in the
``/InitialAlignment/`` group.  If provided, this initial transformation is
assumed to provide a transformation:

 - *From* the **source image world coordinate system** (or the coordinate
   system used as input to the ``/Post/`` affine, if provided).

 - *To* the **aligned source image coordinate system** used within the
   non-linear transformation.


File format specification
-------------------------


Non-linear X5 transformation files are assumed to adhere to the following
HDF5 structure. All fields are required unless otherwise noted:


+---------------+-----------+-------------------------------------------------+
| **Name**      | **Type**  | **Value/Description**                           |
+---------------+-----------+-------------------------------------------------+
| *Metadata*                                                                  |
+---------------+-----------+-------------------------------------------------+
| ``/Format``   | attribute | ``'X5'``                                        |
+---------------+-----------+-------------------------------------------------+
| ``/Version``  | attribute | ``'0.0.1'``                                     |
+---------------+-----------+-------------------------------------------------+
| ``/Metadata`` | attribute | JSON string containing unstructured metadata.   |
+---------------+-----------+-------------------------------------------------+
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


Storage of FSL FNIRT transformations in non-linear X5 files
-----------------------------------------------------------


Non-linear registration using FNIRT generally follows the process depicted
here:


.. image:: images/nonlinear_registration_process.png
   :width: 80%
   :align: center


First, an initial linear registration is performed from the source image to
the reference image using FLIRT; this provides an initial global alignment
which can be used as the starting point for the non-linear registration. Next,
FNIRT is used to non-linearly register the aligned source image to the
reference image.  Importantly, both of these steps are performed using FSL
coordinates.


The non-linear transformation file generated by FNIRT typically contains the
initial linear registration, with it either being encoded directly into the
displacements, or being stored in the NIfTI header.


Storage of FNIRT displacement fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


A FNIRT displacement field contains either:

 - relative displacements from reference image FSL coordinates to source
   image FSL coordinates, or
 - absolute source image FSL coordinates.


If an initial linear registration was used as the starting point for FNIRT,
this is encoded into the displacements/coordinates themselves, so they can be
used to transform from the reference image to the *original* source image.


.. image:: images/fnirt_displacement_field.png
   :width: 80%
   :align: center


When a FNIRT displacement field is stored in a X5 file, the ``/Pre/`` and
``/Post/`` affine transformations are set so that the displacement field can
be used to perform a transformation from reference image world coordinates to
source image world coordinates.


.. image:: images/x5_nonlinear_displacement_field_file.png
   :width: 95%
   :align: center


Storage of FNIRT coefficient fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


A FNIRT coefficient field contains the coefficients of a grid of B-spline
functions; these coefficients can be used to generate a displacement field
which encodes a transformation from reference image FSL coordinates to source
image FSL coordinates.


If an initial linear registration was used as the starting point for FNIRT,
the generated displacement field will encode a transformtion to *aligned*
source image coordinates, and the initial affine will be stored in the NIfTI
header of the coefficient field file.


.. image:: images/fnirt_coefficient_field.png
   :width: 80%
   :align: center


When a FNIRT coefficient field is stored in an X5 file, the ``/Pre/`` and
``/Post/`` affine transformations are set as for displacement
fields. Additionally, the initial linear registration transformation is stored
as the ``/InitialAlignment/``, so that its inverse can be used to transform
the aligned source image FSL coordinates back into the original source image
FSL coordinates.


.. image:: images/x5_nonlinear_coefficient_field_file.png
   :width: 95%
   :align: center
"""


import json

import numpy   as np
import nibabel as nib
import h5py

import fsl.version    as version
import fsl.data.image as fslimage
from . import            affine
from . import            nonlinear


X5_FORMAT  = 'X5'
X5_VERSION = '0.0.1'


class X5Error(Exception):
    """Error raised if an invalid/incompatible file is detected. """
    pass


def readLinearX5(fname):
    """Read a linear X5 transformation file from ``fname``.

    :arg fname: File name to read from
    :returns:    A tuple containing:

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
    """Write a linear transformation to ``fname``.

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
    """Read a nonlinear X5 transformation file from ``fname``.

    :arg fname: File name to read from
    :returns:   A :class:`.DisplacementField` or :class:`.CoefficientField`
    """

    with h5py.File(fname, 'r') as f:

        root = f['/']
        _validateNonLinearTransform(root)

        subtype = root.attrs['SubType']

        if   subtype == 'displacement': field = _readDisplacementField(root)
        elif subtype == 'coefficient':  field = _readCoefficientField(root)

    return field


def writeNonLinearX5(fname, field):
    """Write a nonlinear X5 transformation to ``fname``.

    :arg fname: File name to write to
    :arg field: A :class:`.DisplacementField` or :class:`.CoefficientField`
    """

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)

        f.attrs['Type'] = 'nonlinear'

        if isinstance(field, nonlinear.DisplacementField):
            _writeDisplacementField(f, field)
        elif isinstance(field, nonlinear.CoefficientField):
            _writeCoefficientField(f, field)


def _writeMetadata(group):
    """Writes a metadata block into the given group.

    :arg group: A ``h5py.Group`` object.
    """
    group.attrs['Format']   = X5_FORMAT
    group.attrs['Version']  = X5_VERSION
    group.attrs['Metadata'] = json.dumps({'fslpy' : version.__version__})


def _validateMetadata(group):
    """Reads a metadata block from the given group, and raises a :exc:`X5Error`
    if it does not look valid.

    :arg group: A ``h5py.Group`` object.
    """

    try:
        format  = group.attrs['Format']
        version = group.attrs['Version']

    except Exception:
        raise X5Error('File does not appear to be an X5 file')

    if (format != X5_FORMAT) or (version != X5_VERSION):
        raise X5Error('Incompatible format/version (required: {}/{}, '
                      'present: {}/{})'.format(X5_FORMAT, X5_VERSION,
                                               format, version))


def _readAffine(group):
    """Reads an affine from the given group.

    :arg group: A ``h5py.Group`` object.
    :returns:   ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    if group.attrs['Type'] != 'linear':
        raise X5Error('Not a linear transform')

    xform = group['Transform']

    if xform.shape != (4, 4):
        raise X5Error('Not a linear transform')

    return np.array(xform)


def _writeAffine(group, xform):
    """Writes the given affine transformation and its inverse to the given
    group.

    :arg group: A ``h5py.Group`` object.
    :arg xform: ``numpy`` array containing a ``(4, 4)`` affine transformation.
    """

    xform = np.asarray(xform,                dtype=np.float64)
    inv   = np.asarray(affine.invert(xform), dtype=np.float64)

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
        raise X5Error('Not an image space')

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


def _validateNonLinearTransform(group):
    """Checks that the attributes of the given group, assumed to contain a
    nonlinear transform, are valid. Raises a :exc:`X5Error` if not.

    :arg group: A ``h5py.Group`` object.
    """

    type     = group.attrs['Type']
    subtype  = group.attrs['SubType']
    repr     = group.attrs['Representation']

    if type != 'nonlinear':
        raise X5Error('Not a nonlinear transform')

    if subtype not in ('displacement', 'coefficient'):
        raise X5Error('Unrecognised nonlinear subtype: {}'.format(subtype))

    if (subtype == 'displacement') and \
       (repr not in ('absolute', 'relative')):
        raise X5Error('Unrecognised nonlinear representation: '
                      '{}'.format(repr))

    if (subtype == 'coefficient') and \
       (repr not in ('quadratic bspline', 'cubic bspline')):
        raise X5Error('Unrecognised nonlinear representation: '
                      '{}'.format(repr))


def _readNonLinearCommon(group):
    """Reads the spaces and affines from the given group, assumed to contain a
    nonlinear transform.

    :arg group: A ``h5py.Group`` object.

    :returns:   A tuple containing:
                 - A :class:`.Nifti` representing the source
                 - A :class:`.Nifti` representing the reference
                 - A ``(4, 4)`` ``numpy`` array containing the pre affine, or
                   ``None``  if there is not one.
                 - A ``(4, 4)`` ``numpy`` array containing the post affine, or
                   ``None``  if there is not one.
                 - A ``(4, 4)`` ``numpy`` array containing the initial
                   alignment affine, or ``None``  if there is not one.
                 - A string describing the source space - see
                   :meth:`.Nifti.getAffine`
                 - A string describing the reference  space - see
                   :meth:`.Nifti.getAffine`
    """

    src  = _readSpace(group['From'])
    ref  = _readSpace(group['To'])

    pre  = group.get('Pre')
    post = group.get('Post')
    init = group.get('InitialAlignment')

    if pre  is not None: pre  = _readAffine(pre)
    if post is not None: post = _readAffine(post)
    if init is not None: init = _readAffine(init)

    refSpace = 'world'
    srcSpace = 'world'

    try:
        if pre is not None:
            refSpace = fslimage.Nifti.identifyAffine(
                ref, pre,  from_='world')[1]
        if post is not None:
            srcSpace = fslimage.Nifti.identifyAffine(
                src, post, to='world')[   0]

    except ValueError:
        raise X5Error('Invalid pre/post affine')

    return src, ref, pre, post, init, srcSpace, refSpace


def _writeNonLinearCommon(group, field):
    """Writes the spaces and affines for the given nonlinear transform to the
    given group.

    :arg group: A ``h5py.Group`` object.
    :arg field: A :class:`.NonLinearTransform` object
    """

    _writeSpace(group.create_group('From'), field.src)
    _writeSpace(group.create_group('To'),   field.ref)

    pre  = field.ref.getAffine('world', field.refSpace)
    post = field.src.getAffine(field.srcSpace, 'world')

    _writeAffine(group.create_group('Pre'),  pre)
    _writeAffine(group.create_group('Post'), post)

    if field.srcToRefMat is not None:
        _writeAffine(group.create_group('InitialAlignment'), field.srcToRefMat)


def _readDisplacementField(group):
    """Reads a nonlinear displacement field from the given group.

    :arg group: A ``h5py.Group`` object.
    :returns:   A :class:`.DisplacementField` object
    """

    src, ref, pre, post, init, srcSpace, refSpace = _readNonLinearCommon(group)
    field = np.array(group['Transform'])
    dtype = group.attrs['Representation']
    field = nonlinear.DisplacementField(field,
                                        src=src,
                                        ref=ref,
                                        srcSpace=srcSpace,
                                        refSpace=refSpace,
                                        dispType=dtype,
                                        srcToRefMat=init,
                                        xform=ref.voxToWorldMat)
    return field


def _writeDisplacementField(group, field):
    """Writes a nonlinear displacement field to the given group.

    :arg group: A ``h5py.Group`` object.
    :arg field: A :class:`.DisplacementField` object
    """

    _writeNonLinearCommon(group, field)

    group.attrs['SubType']        = 'displacement'
    group.attrs['Representation'] = field.displacementType

    xform = field.data.astype(np.float64)

    group.create_dataset('Transform', data=xform)


def _readCoefficientField(group):
    """Reads a nonlinear coefficient field from the given group.

    :arg group: A ``h5py.Group`` object.
    :returns:   A :class:`.CoefficientField` object
    """

    src, ref, pre, post, init, srcSpace, refSpace = _readNonLinearCommon(group)

    field      = np.array(group['Transform'])
    ftype      = group.attrs['Representation']
    spacing    = group['Parameters'].attrs['Spacing']
    refToField = _readAffine(group['Parameters/ReferenceToField'])
    fieldToRef = affine.invert(refToField)

    if   ftype == 'quadratic bspline': ftype = 'quadratic'
    elif ftype == 'cubic bspline':     ftype = 'cubic'

    if spacing.shape != (3,):
        raise X5Error('Invalid spacing: {}'.format(spacing))

    field = nonlinear.CoefficientField(field,
                                       src=src,
                                       ref=ref,
                                       srcSpace=srcSpace,
                                       refSpace=refSpace,
                                       fieldType=ftype,
                                       knotSpacing=spacing,
                                       fieldToRefMat=fieldToRef,
                                       srcToRefMat=init)

    return field


def _writeCoefficientField(group, field):
    """Writes a nonlinear coefficient field to the given group.

    :arg group: A ``h5py.Group`` object.
    :arg field: A :class:`.CoefficientField` object
    """

    _writeNonLinearCommon(group, field)

    group.attrs['SubType'] = 'coefficient'

    if field.fieldType == 'cubic':
        group.attrs['Representation'] = 'cubic bspline'
    elif field.fieldType == 'quadratic':
        group.attrs['Representation'] = 'quadratic bspline'

    xform = field.data.astype(np.float64)

    group.create_dataset('Transform', data=xform)

    params = group.create_group('Parameters')
    refToField = params.create_group('ReferenceToField')

    params.attrs['Spacing'] = field.knotSpacing
    _writeAffine(refToField, field.refToFieldMat)
