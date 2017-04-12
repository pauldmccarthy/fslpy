#!/usr/bin/env python
#
# __init__.py - fslpy tests
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Unit tests for ``fslpy``. """


import            os
import            shutil
import            tempfile
import os.path as op
import numpy   as np
import nibabel as nib


def testdir():
    """Returnsa context manager which creates and returns a temporary
    directory, and then deletes it on exit.
    """
    class ctx(object):
        def __enter__(self):
            self.testdir = tempfile.mkdtemp()
            return self.testdir

        def __exit__(self, *a, **kwa):
            shutil.rmtree(self.testdir)

    return ctx()


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


def make_random_image(filename, dims=(10, 10, 10)):
    """Creates a NIFTI1 image with random data, saves and
    returns it.
    """

    data = np.array(np.random.random(dims) * 100, dtype=np.float32)
    img  = nib.Nifti1Image(data, np.eye(4))

    nib.save(img, filename)

    return img
