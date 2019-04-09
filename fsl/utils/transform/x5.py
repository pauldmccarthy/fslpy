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

from . import flirt


def _writeLinearTransform(group, xform):
    group.attrs['Type'] = 'linear'
    group.create_dataset('Transform', data=xform)
    group.create_dataset('Inverse',   data=npla.inv(xform))


def _readLinearTransform(group):
    if group.attrs['Type'] != 'linear':
        raise ValueError('Not a linear transform')
    return np.array(group['Transform'])


def _writeLinearMapping(group, img):
    group.attrs['Type']   = 'image'
    group.attrs['Size']   = img.shape[ :3]
    group.attrs['Scales'] = img.pixdim[:3]

    mapping = group.create_group('Mapping')
    _writeLinearTransform(mapping, img.getAffine('voxel', 'world'))

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


def writeFlirtX5(fname, xform, src, ref):
    """
    """

    xform = flirt.fromFlirt(xform, src, ref, 'world', 'world')

    with h5py.File(fname, 'w') as f:
        f.attrs['Format']   = 'X5'
        f.attrs['Version']  = '0.0.1'
        f.attrs['Metadata'] = json.dumps({'software' : 'flirt'})

        _writeLinearTransform(f, xform)

        from_ = f.create_group('/From')
        to    = f.create_group('/To')

        _writeLinearMapping(from_, src)
        _writeLinearMapping(to,    ref)


def readFlirtX5(fname):
    """
    """
    with h5py.File(fname, 'r') as f:
        xform = _readLinearTransform(f['/'])
        src   = _readLinearMapping(  f['/From'])
        ref   = _readLinearMapping(  f['/To'])

    return xform, src, ref
