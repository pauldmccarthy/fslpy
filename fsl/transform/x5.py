#!/usr/bin/env python
#
# x5.py - Functions for working with BIDS X5 files.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains functions for reading/writing linear/non-linear
transformations from/to BIDS X5 files. The following functions are available:

.. autosummary::
   :nosignatures:

   readLinearX5
   writeLinearX5
   readNonLinearX5
   writeNonLinearX5


An X5 file is a HDF5 container file which stores a linear or non-linear
transformation from one NIfTI image to another.


Several terms may be used to refer to these images, such as **source** and
**reference**, **moving** and **fixed**, **from** and **to**, etc.  In an X5
file, the two images are simply referred to as **A** and **B**, where **A**
refers to the starting point of the transformation, and **B** to the end
point.


X5 files enable a transformation from the **world coordinate system** of image
**A** to the **world coordinate system** of image **B**.  The **world
coordinate system** of an image is defined by its ``sform`` or ``qform``
(hereafter referred to as the ``sform``), which is contained in its NIfTI
header.


Custom HDF5 groups
==================


HDF5 files are composed primarily of *groups*, *attributes*, and
*datasets*:


 - *Groups* are simply containers for attributes, datasets, and other groups.
 - *Datasets* are strongly-typed, structured N-dimensional arrays.
 - *Attributes* are strongly-typed scalar values associated with a group or
   dataset.


To simplify the file format definitions below, we shall first define a few
custom HDF5 groups. In the file format definitions, a HDF5 group which is
listed as being of one of these custom types shall contain the
attributes/datasets that are listed here.


*affine*
--------


A HDF5 group which is listed as being of type *affine* contains an affine
transformation, which can be used to transform coordinates from one space into
another. Groups of type *affine* have the following fields:


+-------------+-----------+---------------------------------------------------+
| **Name**    | **Type**  | **Value/Description**                             |
+-------------+-----------+---------------------------------------------------+
| ``Type``    | attribute | ``'affine'``                                      |
+-------------+-----------+---------------------------------------------------+
| ``Matrix``  | dataset   | The affine transformation matrix - a ``float64``  |
|             |           | array of shape ``(4, 4)``                         |
+-------------+-----------+---------------------------------------------------+
| ``Inverse`` | dataset   | Optional pre-calculated inverse                   |
+-------------+-----------+---------------------------------------------------+


*space*
-------


A HDF5 group which is listed as being of type *space* contains all of the
information required to define the space of a NIfTI image, including its
shape, dimensions, and voxel-to-world affine transformation.


Groups of type *space* have the following fields:


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


*deformation*
-------------


A HDF5 group which is listed as being of type *deformation* contains a
non-linear transformation, which can be used to transform coordinates from
one space (space **A**) into another (space **B**).


The transformation is represented as a 3D **deformation field** which, at each
voxel within the field, may contain:

 - *relative displacements* from space **A** to space **B** (i.e. for a given
   location in space **A**, you can add the displacement values to the
   coordinates of that location to obtain the coordinates of the corresponding
   location in space **B**).

 - *absolute coordinates* in space **B**.


The ``Mapping`` affine can be used to calculate a correspondence between the
deformation field coordinate system and the coordinate system of space **A** -
it is assumed that space **A** and the deformation field share a common world
coordinate system.


Groups of type *deformation* have the following fields:


+-------------+-----------+---------------------------------------------------+
| **Name**    | **Type**  | **Value/Description**                             |
+-------------+-----------+---------------------------------------------------+
| ``Type``    | attribute | ``'deformation'``                                 |
+-------------+-----------+---------------------------------------------------+
| ``SubType`` | attribute | ``'absolute'`` or ``'relative'``.                 |
+-------------+-----------+---------------------------------------------------+
| ``Matrix``  | dataset   | The deformation field - a ``float64`` array of    |
|             |           | shape ``(X, Y, Z, 3)``                            |
+-------------+-----------+---------------------------------------------------+
| ``Mapping`` | affine    | The field voxel-to-world transformation (its      |
|             |           | ``sform``)                                        |
+-------------+-----------+---------------------------------------------------+


Linear X5 files
===============


Linear X5 transformation files contain an affine transformation matrix of
shape ``(4, 4)``, which can be used to transform image **A** world
coordinates into image **B** world coordinates.


Linear X5 transformation files are assumed to adhere to the HDF5 structure
defined in the table below.  All fields are required unless otherwise noted.


+-----------------+-----------+-----------------------------------------------+
| **Name**        | **Type**  | **Value/Description**                         |
+-----------------+-----------+-----------------------------------------------+
| *Metadata*                                                                  |
+-----------------+-----------+-----------------------------------------------+
| ``/Format``     | attribute | ``'X5'``                                      |
+-----------------+-----------+-----------------------------------------------+
| ``/Version``    | attribute | ``'0.0.1'``                                   |
+-----------------+-----------+-----------------------------------------------+
| ``/Metadata``   | attribute | JSON string containing unstructured metadata. |
+-----------------+-----------+-----------------------------------------------+
| *Transformation*                                                            |
+-----------------+-----------+-----------------------------------------------+
| ``/Type``       | attribute | ``'linear'``                                  |
+-----------------+-----------+-----------------------------------------------+
| ``/Transform/`` | affine    | Affine transformation from image **A** world  |
|                 |           | coordinates to image **B** world coordinates  |
+-----------------+-----------+-----------------------------------------------+
| ``/A/``         | space     | Image **A** space                             |
+-----------------+-----------+-----------------------------------------------+
| ``/B/``         | space     | Image **B** space                             |
+-----------------+-----------+-----------------------------------------------+


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


The :mod:`fsl.transform.flirt` module contains functions for converting
between FLIRT-style matrices and X5 style matrices.


.. [*] For a given image, FSL coordinates are voxel coordinates scaled by the
       ``pixdim`` values in the NIFTI header, and an inversion along the X
       axis if the voxel-to-world affine (the ``sform``) has a positive
       determinant.


Non-linear X5 files
===================


Non-linear X5 transformation files contain a non-linear transformation from
image **A** world coordinates to image **B** world coordinates. The
transformation is represented as a 3D **deformation field** which, at each
voxel within the field, may contain:

 - *relative displacements* from image **A** to image **B** (i.e. for a given
   location in the image **A** world coordinate system, add the displacement
   values to the coordinates to obtain the corresponding location in the
   image **B** world coordinate system).

 - *absolute coordinates* in the image **B** world coordinate system.


File format specification
-------------------------


Non-linear X5 transformation files are assumed to adhere to the following
HDF5 structure. All fields are required unless otherwise noted.


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
+-----------------+-------------+---------------------------------------------+
| **Name**        | **Type**    | **Value/Description**                       |
+-----------------+-------------+---------------------------------------------+
| ``/Type``       | attribute   | ``'nonlinear'``                             |
+-----------------+-------------+---------------------------------------------+
| ``/Transform/`` | deformation | The deformation field, encoding a nonlinear |
|                 |             | transformation from image **A** to image    |
|                 |             | **B**                                       |
+-----------------+-------------+---------------------------------------------+
| ``/Inverse/``   | deformation | Optional pre-calculated inverse, encoding a |
|                 |             | nonlinear transformation from image **B**   |
|                 |             | to image **A**                              |
+-----------------+-------------+---------------------------------------------+
| ``/A/``         | space       | Image **A** space                           |
+-----------------+-------------+---------------------------------------------+
| ``/B/``         | space       | Image **B** space                           |
+-----------------+-------------+---------------------------------------------+


Storage of FSL FNIRT warp fields in non-linear X5 files
-------------------------------------------------------


FLIRT outputs the result of a non-linear registration from a source image to a
reference image as either a warp field, or a coefficient field which can be
used to generate a warp field. A warp field is defined in terms of the
reference image - the warp field has the same shape and FOV as the reference
image, and contains either:

 - relative displacements from the corresponding reference image location to
   the unwarped source image location
 - absolute unwarped source image coordinates


The reference image for a FNIRT warp field thus corresponds to image **A** in
a X5 non-linear transform, and the FNIRT source image to image **B**.


FNIRT warp fields are defined in FSL coordinates - a relative warp contains
displacements from reference image FSL coordinates to source image FSL
coordinates, and an absolute warp contains source image FSL coordinates.


When a FNIRT warp field is stored in an X5 file, the displacements/coordinates
must be adjusted so that they encode a transformation from reference image
world coordinates to source image world coordinates.


Conversion of FNIRT coefficient fields
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


A FNIRT coefficient field can be used to generate a deformation field which
contains relative displacements from reference image FSL coordinates to source
image FSL coordinates. If an initial affine registration was used as the
starting point for FNIRT, this generated displacement field contains relative
displacements from the reference image to the *aligned* source image,
i.e. after it has been transformed by the initial affine alignment.


When a FNIRT coefficient field is stored in an X5 file, it must first be
converted to a displacement field. The displacements must then be adjusted so
that they take into account the initial affine alignment (if relevant), and
so that they encode displacements from reference image world coordinates
to source image world coordinates.


The :mod:`fsl.transform.fnirt` module contains functions which can be used to
perform all of the conversions and adjustments required to store FNIRT
transformations as X5 files.
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
