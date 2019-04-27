#!/usr/bin/env python
#
# x5.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""

Functions for reading/writing linear/non-linear FSL transformations from/to
BIDS X5 files.
"""

import json

import numpy        as np
import numpy.linalg as npla
import nibabel      as nib
import h5py

import fsl.version as version


def _writeMetadata(group):
    group.attrs['Format']   = 'X5'
    group.attrs['Version']  = '0.0.1'
    group.attrs['Metadata'] = json.dumps({'fslpy' : version.__version__})


def _readLinearTransform(group):
    if group.attrs['Type'] != 'linear':
        raise ValueError('Not a linear transform')
    return np.array(group['Transform'])


def _writeLinearTransform(group, xform):

    xform = np.asarray(xform,           dtype=np.float32)
    inv   = np.asarray(npla.inv(xform), dtype=np.float32)

    group.attrs['Type'] = 'linear'
    group.create_dataset('Transform', data=xform)
    group.create_dataset('Inverse',   data=inv)


def _readLinearMapping(group):

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


    ::
        /Format                       # "X5"
        /Version                      # "0.0.1"
        /Metadata                     # json string containing unstructured metadata

        /Type                         # "linear"
        /Transform                    # the transform itself
        /Inverse                      # optional pre-calculated inverse

        /From/Type                    # "image" - could in principle be something other than
                                      # "image" (e.g. "surface"), in which case the "Size" and
                                      # "Scales" entries might be replaced with something else
        /From/Size                    # voxel dimensions
        /From/Scales                  # voxel pixdims
        /From/Mapping/Type            # "linear" - could be also be "nonlinear"
        /From/Mapping/Transform       # source voxel-to-world sform
        /From/Mapping/Inverse         # optional inverse

        /To/Type                      # "image"
        /To/Size                      # voxel dimensions
        /To/Scales                    # voxel pixdims
        /To/Mapping/Type              # "linear"
        /To/Mapping/Transform         # reference voxel-to-world sform
        /To/Mapping/Inverse           # optional inverse
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

        /Type                         # "nonlinear"
        /Transform                    # the displacement/coefficient field itself
        /Inverse                      # optional pre-calculated inverse

        /From/Type                    # "image"
        /From/Size                    # voxel dimensions
        /From/Scales                  # voxel pixdims
        /From/Mapping/Type            # "linear"
        /From/Mapping/Transform       # source voxel-to-world sform
        /From/Mapping/Inverse         # optional inverse

        /To/Type                      # "image"
        /To/Size                      # voxel dimensions
        /To/Scales                    # voxel pixdims
        /To/Mapping/Type              # "linear"
        /To/Mapping/Transform         # reference voxel-to-world sform
        /To/Mapping/Inverse           # optional inverse
    """

    # TODO coefficient fields

    with h5py.File(fname, 'w') as f:
        _writeMetadata(f)
        _writeNonLinearTransform(f, field.data)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeLinearMapping(from_, field.src)
        _writeLinearMapping(to,    field.ref)
