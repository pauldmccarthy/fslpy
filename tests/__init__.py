#!/usr/bin/env python
#
# __init__.py - fslpy tests
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Unit tests for ``fslpy``. """


import            os
import            shutil
import os.path as op
import numpy   as np
import nibabel as nib


def make_dummy_file(path):
    """Makes a plain text file. Returns a hash of the file contents. """
    contents = '{}\n'.format(op.basename(path))
    with open(path, 'wt') as f:
        f.write(contents)

    return hash(contents)


def looks_like_image(path):
    """Returns True if the given path looks like a NIFTI/ANALYZE image.
    """
    return any((path.endswith('.nii'),
                path.endswith('.nii.gz'),
                path.endswith('.img'),
                path.endswith('.hdr'),
                path.endswith('.img.gz'),
                path.endswith('.hdr.gz')))


def make_dummy_image_file(path):
    """Makes some plain files with NIFTI/ANALYZE file extensions.
    """

    if   path.endswith('.nii'):    paths = [path]
    elif path.endswith('.nii.gz'): paths = [path]
    elif path.endswith('.img'):    paths = [path, path[:-4] + '.hdr']
    elif path.endswith('.hdr'):    paths = [path, path[:-4] + '.img']
    elif path.endswith('.img.gz'): paths = [path, path[:-7] + '.hdr.gz']
    elif path.endswith('.hdr.gz'): paths = [path, path[:-7] + '.img.gz']
    else: raise RuntimeError()

    for path in paths:
        make_dummy_file(path)


def cleardir(dir):
    """Deletes everything in the given directory, but not the directory
    itself.
    """
    for f in os.listdir(dir):
        f = op.join(dir, f)
        if   op.isfile(f): os.remove(f)
        elif op.isdir(f):  shutil.rmtree(f)


def make_random_image(filename, dims=(10, 10, 10), affine=None):
    """Creates a NIFTI image with random data, returns the hash of said data.
    """

    if affine is None:
        affine = np.eye(4)
    
    data = np.random.random(dims)
    img  = nib.Nifti1Image(data, affine)

    nib.save(img, filename)

    return hash(data.tobytes())

def check_image_hash(filename, datahash):
    """Checks that the given NIFTI image matches the given hash.
    """

    img = nib.load(filename)
    assert hash(img.get_data().tobytes()) == datahash

