#!/usr/bin/env python


import               glob
import               gzip
import               bz2
import itertools  as it
import os.path    as op
import subprocess as sp
import               shlex
import               tempfile

import numpy          as np
import nibabel        as nib
import fsl.data.image as fslimage

try:
    from compression import zstd
except ImportError:
    from backports import zstd


from fsl.scripts import fslchfiletype


FILE_TYPES = {
    "ANALYZE"         : ('.img',    '.hdr'),
    "ANALYZE_GZ"      : ('.img.gz', '.hdr.gz'),
    "NIFTI"           : ('.nii',),
    "NIFTI_GZ"        : ('.nii.gz',),
    "NIFTI_ZST"       : ('.nii.zst',),
    "NIFTI_BZ2"       : ('.nii.bz2',),
    "NIFTI_PAIR"      : ('.img', '.hdr'),
    "NIFTI_PAIR_GZ"   : ('.img.gz', '.hdr.gz'),
    "NIFTI_PAIR_ZST"  : ('.img.zst', '.hdr.zst'),
    "NIFTI_PAIR_BZ2"  : ('.img.bz2', '.hdr.bz2'),
    "NIFTI2"          : ('.nii',),
    "NIFTI2_GZ"       : ('.nii.gz',),
    "NIFTI2_ZST"      : ('.nii.zst',),
    "NIFTI2_BZ2"      : ('.nii.bz2',),
    "NIFTI2_PAIR"     : ('.img', '.hdr'),
    "NIFTI2_PAIR_GZ"  : ('.img.gz', '.hdr.gz'),
    "NIFTI2_PAIR_ZST" : ('.img.zst', '.hdr.zst'),
    "NIFTI2_PAIR_BZ2" : ('.img.bz2', '.hdr.bz2'),
}

def sprun(cmd):
    print(f'Running: {cmd}')
    sp.run(shlex.split(cmd), check=True, text=True)


def make_file(prefix, ftype, dtype):
    classes = {
        'ANALYZE'         : nib.AnalyzeImage,
        'ANALYZE_GZ'      : nib.AnalyzeImage,
        'NIFTI'           : nib.Nifti1Image,
        'NIFTI2'          : nib.Nifti2Image,
        'NIFTI_PAIR'      : nib.Nifti1Pair,
        'NIFTI2_PAIR'     : nib.Nifti2Pair,
        'NIFTI_GZ'        : nib.Nifti1Image,
        'NIFTI2_GZ'       : nib.Nifti2Image,
        'NIFTI_PAIR_GZ'   : nib.Nifti1Pair,
        'NIFTI2_PAIR_GZ'  : nib.Nifti2Pair,
        'NIFTI_ZST'       : nib.Nifti1Image,
        'NIFTI2_ZST'      : nib.Nifti2Image,
        'NIFTI_PAIR_ZST'  : nib.Nifti1Pair,
        'NIFTI2_PAIR_ZST' : nib.Nifti2Pair,
        'NIFTI_BZ2'       : nib.Nifti1Image,
        'NIFTI2_BZ2'      : nib.Nifti2Image,
        'NIFTI_PAIR_BZ2'  : nib.Nifti1Pair,
        'NIFTI2_PAIR_BZ2' : nib.Nifti2Pair,
    }

    if np.issubdtype(dtype, np.complex64):
        data = np.random.random((20, 20, 20)).astype(np.float32) + \
               np.random.random((20, 20, 20)).astype(np.float32) * 1j
    else:
        data = np.random.random((20, 20, 20)).astype(dtype)

    suffix    = FILE_TYPES[ftype][0]
    cls       = classes[   ftype]
    filename  = f'{prefix}{suffix}'

    cls(data, None).to_filename(filename)

    return filename


def is_x(filename, filetype):
    try:
        with filetype(filename, 'rb') as f:
            f.read()
        return True
    except Exception:
        return False

def is_gzip(filename):
    return is_x(filename, gzip.GzipFile)

def is_bzip2(filename):
    return is_x(filename, bz2.BZ2File)

def is_zstd(filename):
    return is_x(filename, zstd.ZstdFile)

def is_pair(imgfile):
    prefix, suffix = fslimage.splitExt(imgfile)
    hdrfile        = imgfile
    if   suffix == '.hdr':     imgfile = f'{prefix}.img'
    elif suffix == '.hdr.gz':  imgfile = f'{prefix}.img.gz'
    elif suffix == '.hdr.zst': imgfile = f'{prefix}.img.zst'
    elif suffix == '.hdr.bz2': imgfile = f'{prefix}.img.bz2'
    elif suffix == '.img':     hdrfile = f'{prefix}.hdr'
    elif suffix == '.img.gz':  hdrfile = f'{prefix}.hdr.gz'
    elif suffix == '.img.zst': hdrfile = f'{prefix}.hdr.zst'
    elif suffix == '.img.bz2': hdrfile = f'{prefix}.hdr.bz2'
    return op.exists(imgfile) and op.exists(hdrfile)


def is_analyze(filename):
    img = nib.load(filename)
    return  is_pair(filename)                                      and \
            isinstance(img, (nib.AnalyzeImage, nib.AnalyzeHeader)) and \
        not isinstance(img, (nib.Nifti1Image,  nib.Nifti1Header, nib.Nifti1Pair))


def is_nifti1(filename):
    img = nib.load(filename)
    return  isinstance(img, (nib.Nifti1Image, nib.Nifti1Header, nib.Nifti1Pair)) and \
        not isinstance(img, (nib.Nifti2Image, nib.Nifti2Header, nib.Nifti2Pair))


def is_nifti2(filename):
    img = nib.load(filename)
    return isinstance(img, (nib.Nifti2Image, nib.Nifti2Header, nib.Nifti2Pair))


def check_file(prefix, expftype, dtype):

    # check that file(s) were created with correct suffix(es)
    gotfiles = glob.glob(f'{prefix}*')
    expfiles = [f'{prefix}{suffix}' for suffix in FILE_TYPES[expftype]]
    assert sorted(gotfiles) == sorted(expfiles)

    # check that file is of correct type
    filename = fslimage.addExt(prefix)
    if   'NIFTI2'  in expftype: assert is_nifti2( filename)
    elif 'NIFTI'   in expftype: assert is_nifti1( filename)
    elif 'ANALYZE' in expftype: assert is_analyze(filename)
    if   'GZ'      in expftype: assert is_gzip(   filename)
    if   'ZST'     in expftype: assert is_zstd(   filename)
    if   'BZ2'     in expftype: assert is_bzip2(  filename)
    if   'PAIR'    in expftype: assert is_pair(   filename)

    # check that file has correct data type
    img = nib.load(filename)
    assert np.issubdtype(img.get_data_dtype(), dtype)


def test_fslchfiletype_conversion():

    dtypes = [np.uint8, np.int16, np.float32, np.float64, np.complex64]

    for to, from_, dtype in it.product(FILE_TYPES, FILE_TYPES, dtypes):
        with tempfile.TemporaryDirectory() as td:

            fromprefix = op.join(td, f'f{from_}_{dtype.__name__}')
            toprefix   = op.join(td, f't{to}_{dtype.__name__}')

            make_file(fromprefix, from_, dtype)

            fslchfiletype.main((to, fromprefix, toprefix))

            check_file(toprefix, to, dtype)


def test_fslchfiletype_copy():

    for to, from_ in it.product(FILE_TYPES, FILE_TYPES):
        with tempfile.TemporaryDirectory() as td:
            image1 = op.join(td, 'image1')
            image2 = op.join(td, 'image2')
            make_file(image1, from_, np.int16)
            fslchfiletype.main((to, image1, image2))
            check_file(image1, from_, np.int16)
            check_file(image2, to,    np.int16)


def test_fslchfiletype_inplace():
    for to, from_ in it.product(FILE_TYPES, FILE_TYPES):
        with tempfile.TemporaryDirectory() as td:
            image = op.join(td, 'image')
            make_file(image, from_, np.int16)
            fslchfiletype.main((to, image))
            check_file(image, to, np.int16)
