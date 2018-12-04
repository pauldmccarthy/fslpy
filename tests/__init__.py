#!/usr/bin/env python
#
# __init__.py - fslpy tests
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Unit tests for ``fslpy``. """


import              os
import              sys
import              glob
import              shutil
import              fnmatch
import              logging
import              tempfile
import              contextlib
import itertools as it
import os.path   as op
import numpy     as np
import nibabel   as nib

from six import StringIO


try: from unittest import mock
except ImportError: import mock

import fsl.data.image                     as fslimage
from   fsl.utils.tempdir import              tempdir
from   fsl.utils.platform import platform as fslplatform


logging.getLogger().setLevel(logging.WARNING)


@contextlib.contextmanager
def mockFSLDIR(**kwargs):

    oldfsldir    = fslplatform.fsldir
    oldfsldevdir = fslplatform.fsldevdir

    try:
        with tempdir() as td:
            fsldir = op.join(td, 'fsl')
            bindir = op.join(fsldir, 'bin')
            os.makedirs(bindir)
            for subdir, files in kwargs.items():
                subdir = op.join(fsldir, subdir)
                if not op.isdir(subdir):
                    os.makedirs(subdir)
                for fname in files:
                    touch(op.join(subdir, fname))
            fslplatform.fsldir = fsldir
            fslplatform.fsldevdir = None

            path = op.pathsep.join((bindir, os.environ['PATH']))

            with mock.patch.dict(os.environ, {'PATH': path}):
                yield fsldir
    finally:
        fslplatform.fsldir    = oldfsldir
        fslplatform.fsldevdir = oldfsldevdir


def touch(fname):
    with open(fname, 'wt') as f:
        pass


class CaptureStdout(object):
    """Context manager which captures stdout and stderr. """

    def __init__(self):
        self.reset()

    def reset(self):
        self.__mock_stdout = StringIO('')
        self.__mock_stderr = StringIO('')
        self.__mock_stdout.mode = 'w'
        self.__mock_stderr.mode = 'w'
        return self

    def __enter__(self):
        self.__real_stdout = sys.stdout
        self.__real_stderr = sys.stderr

        sys.stdout = self.__mock_stdout
        sys.stderr = self.__mock_stderr


    def __exit__(self, *args, **kwargs):
        sys.stdout = self.__real_stdout
        sys.stderr = self.__real_stderr

        if args[0] is not None:
            print('Error')
            print('stdout:')
            print(self.stdout)
            print('stderr:')
            print(self.stderr)

        return False

    @property
    def stdout(self):
        self.__mock_stdout.seek(0)
        return self.__mock_stdout.read()

    @property
    def stderr(self):
        self.__mock_stderr.seek(0)
        return self.__mock_stderr.read()



def testdir(contents=None, suffix=""):
    """Returnsa context manager which creates, changes to, and returns a
    temporary directory, and then deletes it on exit.
    """

    if contents is not None:
        contents = [op.join(*c.split('/')) for c in contents]

    class ctx(object):

        def __init__(self, contents):
            self.contents = contents

        def __enter__(self):

            self.testdir = tempfile.mkdtemp(suffix=suffix)
            self.prevdir = os.getcwd()

            os.chdir(self.testdir)

            if self.contents is not None:
                contents = [op.join(self.testdir, c) for c in self.contents]
                make_dummy_files(contents)

            return self.testdir

        def __exit__(self, *a, **kwa):
            os.chdir(self.prevdir)
            shutil.rmtree(self.testdir)

    return ctx(contents)

def make_dummy_files(paths):
    """Creates dummy files for all of the given paths. """
    for p in paths:
        make_dummy_file(p)


def make_dummy_file(path, contents=None):
    """Makes a plain text file. Returns a hash of the file contents. """
    dirname = op.dirname(path)

    if not op.exists(dirname):
        os.makedirs(dirname)

    if contents is None:
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


def cleardir(dir, pat=None):
    """Deletes everything in the given directory, but not the directory
    itself.
    """
    for f in os.listdir(dir):

        if pat is not None and not fnmatch.fnmatch(f, pat):
            continue

        f = op.join(dir, f)

        if   op.isfile(f): os.remove(f)
        elif op.isdir(f):  shutil.rmtree(f)


def checkdir(dir, *expfiles):
    for f in expfiles:
        assert op.exists(op.join(dir, f))


def random_voxels(shape, nvoxels=1):
    randVoxels = np.vstack(
        [np.random.randint(0, s, nvoxels) for s in shape[:3]]).T

    if nvoxels == 1:
        return randVoxels[0]
    else:
        return randVoxels


def make_random_image(filename=None,
                      dims=(10, 10, 10),
                      xform=None,
                      imgtype=1,
                      pixdims=None,
                      dtype=np.float32):
    """Convenience function which makes an image containing random data.
    Saves and returns the nibabel object.

    imgtype == 0: ANALYZE
    imgtype == 1: NIFTI1
    imgtype == 2: NIFTI2
    """

    if   imgtype == 0: hdr = nib.AnalyzeHeader()
    elif imgtype == 1: hdr = nib.Nifti1Header()
    elif imgtype == 2: hdr = nib.Nifti2Header()

    if pixdims is None:
        pixdims = [1] * len(dims)

    pixdims = pixdims[:len(dims)]
    zooms   = [abs(p) for p in pixdims]

    hdr.set_data_dtype(dtype)
    hdr.set_data_shape(dims)
    hdr.set_zooms(zooms)

    if xform is None:
        xform = np.eye(4)
        for i, p in enumerate(pixdims[:3]):
            xform[i, i] = p

    data  = np.array(np.random.random(dims) * 100, dtype=dtype)

    if   imgtype == 0: img = nib.AnalyzeImage(data, xform, hdr)
    elif imgtype == 1: img = nib.Nifti1Image( data, xform, hdr)
    elif imgtype == 2: img = nib.Nifti2Image( data, xform, hdr)

    if filename is not None:

        if op.splitext(filename)[1] == '':
            if imgtype == 0: filename = '{}.img'.format(filename)
            else:            filename = '{}.nii'.format(filename)

        nib.save(img, filename)

    return img


def make_mock_feat_analysis(featdir,
                            testdir,
                            shape4D,
                            xform=None,
                            indata=True,
                            voxEVs=True,
                            pes=True,
                            copes=True,
                            zstats=True,
                            residuals=True,
                            clustMasks=True):

    if xform is None:
        xform = np.eye(4)

    timepoints = shape4D[ 3]
    shape      = shape4D[:3]

    src     = featdir
    dest    = op.join(testdir, op.basename(featdir))
    featdir = dest

    shutil.copytree(src, dest)

    if indata:
        filtfunc = op.join(featdir, 'filtered_func_data.nii.gz')
        img = make_random_image(filtfunc, shape4D, xform)
        del img

    # and some dummy voxelwise EV files
    if voxEVs:
        voxFiles = list(it.chain(
            glob.glob(op.join(featdir, 'designVoxelwiseEV*nii.gz')),
            glob.glob(op.join(featdir, 'InputConfoundEV*nii.gz'))))

        for i, vf in enumerate(voxFiles):

            # Each voxel contains range(i, i + timepoints),
            # offset by the flattened voxel index
            data = np.meshgrid(*[range(s) for s in shape], indexing='ij')
            data = np.ravel_multi_index(data, shape)
            data = data.reshape(list(shape) + [1]).repeat(timepoints, axis=3)
            data[..., :] += range(i, i + timepoints)

            img = nib.nifti1.Nifti1Image(data, xform)

            nib.save(img, vf)
            del img

    otherFiles  = []
    otherShapes = []

    if pes:
        files = glob.glob(op.join(featdir, 'stats', 'pe*nii.gz'))
        otherFiles .extend(files)
        otherShapes.extend([shape] * len(files))

    if copes:
        files = glob.glob(op.join(featdir, 'stats', 'cope*nii.gz'))
        otherFiles .extend(files)
        otherShapes.extend([shape] * len(files))

    if zstats:
        files = glob.glob(op.join(featdir, 'stats', 'zstat*nii.gz'))
        otherFiles .extend(files)
        otherShapes.extend([shape] * len(files))

    if residuals:
        files = glob.glob(op.join(featdir, 'stats', 'res4d.nii.gz'))
        otherFiles .extend(files)
        otherShapes.extend([shape4D])

    if clustMasks:
        files = glob.glob(op.join(featdir, 'cluster_mask*nii.gz'))
        otherFiles .extend(files)
        otherShapes.extend([shape] * len(files))

    for f, s in zip(otherFiles, otherShapes):
        img = make_random_image(f, s, xform)
        del img

    return featdir


def make_mock_melodic_analysis(basedir, shape4D, ntimepoints, xform=None):

    if xform is None:
        xform = np.eye(4)

    ncomps = shape4D[-1]
    halftime = int(np.floor(ntimepoints / 2))

    os.makedirs(basedir)

    make_random_image(op.join(basedir, 'melodic_IC.nii.gz'),
                      dims=shape4D,
                      xform=xform)

    mix   = np.random.randint(1, 255, (ntimepoints, ncomps))
    ftmix = np.random.randint(1, 255, (halftime,    ncomps))

    np.savetxt(op.join(basedir, 'melodic_mix'),   mix)
    np.savetxt(op.join(basedir, 'melodic_FTmix'), ftmix)


def make_mock_dtifit_analysis(basedir, shape3D, basename='dti', xform=None, tensor=False):

    if xform is None:
        xform = np.eye(4)

    os.makedirs(basedir)

    shape4D = tuple(shape3D) + (3,)

    def mk(ident, shp):
        make_random_image(
            op.join(basedir, '{}_{}.nii.gz'.format(basename, ident)),
            shp,
            xform)

    mk('V1', shape4D)
    mk('V2', shape4D)
    mk('V3', shape4D)
    mk('L1', shape3D)
    mk('L2', shape3D)
    mk('L3', shape3D)
    mk('S0', shape3D)
    mk('MD', shape3D)
    mk('MO', shape3D)
    mk('FA', shape3D)

    if tensor:
        mk('tensor', tuple(shape3D) + (6,))


def make_random_mask(filename, shape, xform, premask=None, minones=1):
    """Make a random binary mask image. """

    mask = np.zeros(shape, dtype=np.uint8)

    numones = np.random.randint(minones, np.prod(shape) / 100)
    xc      = np.random.randint(0, shape[0], numones)
    yc      = np.random.randint(0, shape[1], numones)
    zc      = np.random.randint(0, shape[2], numones)

    mask[xc, yc, zc] = 1

    if premask is not None:
        mask[premask == 0] = 0

    img = fslimage.Image(mask, xform=xform)
    img.save(filename)

    return img
