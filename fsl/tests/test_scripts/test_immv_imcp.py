#!/usr/bin/env python



import os.path    as op
import itertools  as it
import subprocess as sp
import               os
import               glob
import               gzip
import               shutil
import               tempfile

from unittest import mock

import               pytest

import numpy as np
import nibabel as nib

from   fsl.utils.tempdir import tempdir
import fsl.scripts.imcp      as imcp_script
import fsl.scripts.immv      as immv_script
import fsl.data.image        as fslimage

from .. import cleardir
from ..test_immv_imcp import makeImage, checkImageHash, checkFilesToExpect


def test_imcp_script_shouldPass(move=False):


    # The imcp/immv scripts should honour the
    # FSLOUTPUTTYPE env var. If it is unset
    # or invalid - '' in this case), they
    # should produce .nii.gz
    outputTypes = ['NIFTI', 'NIFTI_PAIR', 'NIFTI_GZ', '']
    reldirs     = ['neutral', 'samedir', 'indir', 'outdir']

    # Test tuples have the following structure (each
    # item is a string which will be split on spaces):
    #
    #   (files_to_create, imcp_args, files_to_expect)
    #
    # The files_to_expect is a list of
    # prefixes - the suffix(es) is(are)
    # determined by the current outputType
    #
    # If multiple files are being copied, the
    # files_to_create and files_to_expect lists
    # have to be in the same order.
    tests = [

        ('a.nii', 'a     b',        'b'),
        ('a.nii', 'a.nii b',        'b'),
        ('a.nii', 'a     b.nii',    'b'),
        ('a.nii', 'a.nii b.nii',    'b'),
        ('a.nii', 'a     .',        'a'),
        ('a.nii', 'a.nii .',        'a'),
        ('a.nii', 'a     b.hdr',    'b'),
        ('a.nii', 'a     b.img',    'b'),
        ('a.nii', 'a     b.nii.gz', 'b'),
        ('a.nii', 'a.nii b.hdr',    'b'),
        ('a.nii', 'a.nii b.img',    'b'),
        ('a.nii', 'a.nii b.nii.gz', 'b'),

        ('a.nii.gz', 'a        b',        'b'),
        ('a.nii.gz', 'a.nii.gz b',        'b'),
        ('a.nii.gz', 'a        b.nii.gz', 'b'),
        ('a.nii.gz', 'a.nii.gz b.nii.gz', 'b'),
        ('a.nii.gz', 'a        .',        'a'),
        ('a.nii.gz', 'a.nii.gz .',        'a'),
        ('a.nii.gz', 'a        b.hdr',    'b'),
        ('a.nii.gz', 'a        b.img',    'b'),
        ('a.nii.gz', 'a        b.nii',    'b'),
        ('a.nii.gz', 'a.nii.gz b.hdr',    'b'),
        ('a.nii.gz', 'a.nii.gz b.img',    'b'),
        ('a.nii.gz', 'a.nii.gz b.nii',    'b'),

        ('a.img', 'a        b',        'b'),
        ('a.img', 'a        b.img',    'b'),
        ('a.img', 'a        b.hdr',    'b'),
        ('a.img', 'a        .',        'a'),
        ('a.img', 'a.img    b',        'b'),
        ('a.img', 'a.img    b.img',    'b'),
        ('a.img', 'a.img    b.hdr',    'b'),
        ('a.img', 'a.img    .',        'a'),
        ('a.img', 'a.hdr    b',        'b'),
        ('a.img', 'a.hdr    b.img',    'b'),
        ('a.img', 'a.hdr    b.hdr',    'b'),
        ('a.img', 'a.hdr    .',        'a'),

        ('a.img', 'a        b.nii',    'b'),
        ('a.img', 'a        b.nii.gz', 'b'),
        ('a.img', 'a        .',        'a'),
        ('a.img', 'a.hdr    b.nii',    'b'),
        ('a.img', 'a.hdr    b.nii.gz', 'b'),
        ('a.img', 'a.hdr    .',        'a'),
        ('a.img', 'a.img    b.nii',    'b'),
        ('a.img', 'a.img    b.nii.gz', 'b'),
        ('a.img', 'a.img    .',        'a'),

        ('a.nii b.nii', 'a     b     .',   'a b'),
        ('a.nii b.nii', 'a     b.nii .',   'a b'),
        ('a.nii b.nii', 'a.nii b     .',   'a b'),
        ('a.nii b.nii', 'a.nii b.nii .',   'a b'),

        ('a.img b.img', 'a     b     .',   'a b'),
        ('a.img b.img', 'a     b.img .',   'a b'),
        ('a.img b.img', 'a     b.hdr .',   'a b'),
        ('a.img b.img', 'a.img b     .',   'a b'),
        ('a.img b.img', 'a.img b.img .',   'a b'),
        ('a.img b.img', 'a.img b.hdr .',   'a b'),
        ('a.img b.img', 'a.hdr b     .',   'a b'),
        ('a.img b.img', 'a.hdr b.img .',   'a b'),
        ('a.img b.img', 'a.hdr b.hdr .',   'a b'),

        ('a.nii.gz b.nii.gz', 'a        b        .',   'a b'),
        ('a.nii.gz b.nii.gz', 'a        b.nii.gz .',   'a b'),
        ('a.nii.gz b.nii.gz', 'a.nii.gz b        .',   'a b'),
        ('a.nii.gz b.nii.gz', 'a.nii.gz b.nii.gz .',   'a b'),

        # Heterogenous inputs
        ('a.nii b.nii.gz', 'a     b        .', 'a b'),
        ('a.nii b.nii.gz', 'a     b.nii.gz .', 'a b'),
        ('a.nii b.nii.gz', 'a.nii b        .', 'a b'),
        ('a.nii b.nii.gz', 'a.nii b.nii.gz .', 'a b'),
        ('a.nii b.img',    'a     b        .', 'a b'),
        ('a.nii b.img',    'a     b.img    .', 'a b'),
        ('a.nii b.img',    'a     b.hdr    .', 'a b'),
        ('a.nii b.img',    'a.nii b        .', 'a b'),
        ('a.nii b.img',    'a.nii b.img    .', 'a b'),
        ('a.nii b.img',    'a.nii b.hdr    .', 'a b'),
        ('a.img b.nii',    'a     b        .', 'a b'),
        ('a.img b.nii',    'a     b.nii    .', 'a b'),
        ('a.img b.nii',    'a.img b        .', 'a b'),
        ('a.img b.nii',    'a.img b.nii    .', 'a b'),
        ('a.img b.nii',    'a.hdr b        .', 'a b'),
        ('a.img b.nii',    'a.hdr b.nii    .', 'a b'),

        # Duplicate inputs
        ('a.img',       'a     a                 .', 'a'),
        ('a.img',       'a     a.img             .', 'a'),
        ('a.img',       'a     a.hdr             .', 'a'),
        ('a.img',       'a.img a                 .', 'a'),
        ('a.img',       'a.img a.img             .', 'a'),
        ('a.img',       'a.img a.hdr             .', 'a'),
        ('a.img',       'a.hdr a                 .', 'a'),
        ('a.img',       'a.hdr a.img             .', 'a'),
        ('a.img',       'a.hdr a.hdr             .', 'a'),

        ('a.img b.img', 'a     a     b     b     .', 'a b'),
        ('a.img b.img', 'a     a     b     b.img .', 'a b'),
        ('a.img b.img', 'a     a     b     b.hdr .', 'a b'),
        ('a.img b.img', 'a     a     b.img b     .', 'a b'),
        ('a.img b.img', 'a     a     b.img b.img .', 'a b'),
        ('a.img b.img', 'a     a     b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a     a.img b     b     .', 'a b'),
        ('a.img b.img', 'a     a.img b     b.img .', 'a b'),
        ('a.img b.img', 'a     a.img b     b.hdr .', 'a b'),
        ('a.img b.img', 'a     a.img b.img b     .', 'a b'),
        ('a.img b.img', 'a     a.img b.img b.img .', 'a b'),
        ('a.img b.img', 'a     a.img b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a     a.hdr b     b     .', 'a b'),
        ('a.img b.img', 'a     a.hdr b     b.img .', 'a b'),
        ('a.img b.img', 'a     a.hdr b     b.hdr .', 'a b'),
        ('a.img b.img', 'a     a.hdr b.img b     .', 'a b'),
        ('a.img b.img', 'a     a.hdr b.img b.img .', 'a b'),
        ('a.img b.img', 'a     a.hdr b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a     b     b     .', 'a b'),
        ('a.img b.img', 'a.img a     b     b.img .', 'a b'),
        ('a.img b.img', 'a.img a     b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a     b.img b     .', 'a b'),
        ('a.img b.img', 'a.img a     b.img b.img .', 'a b'),
        ('a.img b.img', 'a.img a     b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a.img b     b     .', 'a b'),
        ('a.img b.img', 'a.img a.img b     b.img .', 'a b'),
        ('a.img b.img', 'a.img a.img b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a.img b.img b     .', 'a b'),
        ('a.img b.img', 'a.img a.img b.img b.img .', 'a b'),
        ('a.img b.img', 'a.img a.img b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b     b     .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b     b.img .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b.img b     .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b.img b.img .', 'a b'),
        ('a.img b.img', 'a.img a.hdr b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a     b     b     .', 'a b'),
        ('a.img b.img', 'a.hdr a     b     b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a     b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a     b.img b     .', 'a b'),
        ('a.img b.img', 'a.hdr a     b.img b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a     b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b     b     .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b     b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b.img b     .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b.img b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a.img b.img b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b     b     .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b     b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b     b.hdr .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b.img b     .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b.img b.img .', 'a b'),
        ('a.img b.img', 'a.hdr a.hdr b.img b.hdr .', 'a b'),

        # Inputs which cause the destination
        # to be overwritten - this should be
        # ok, the destination should be the
        # last specified input. The order of
        # files_to_create has to match the
        # imcp_args order, otherwise my bodgy
        # checkFilesToExpect function will
        # break.
        ('a.nii    a.img',             'a.nii    a.img             .', 'a'),
        ('a.img    a.nii',             'a.img    a.nii             .', 'a'),
        ('a.nii    a.img    a.nii.gz', 'a.nii    a.img    a.nii.gz .', 'a'),
        ('a.nii    a.nii.gz a.img   ', 'a.nii    a.nii.gz a.img    .', 'a'),
        ('a.img    a.nii.gz a.nii   ', 'a.img    a.nii.gz a.nii    .', 'a'),
        ('a.img    a.nii    a.nii.gz', 'a.img    a.nii    a.nii.gz .', 'a'),
        ('a.nii.gz a.img    a.nii   ', 'a.nii.gz a.img    a.nii    .', 'a'),
        ('a.nii.gz a.nii    a.img   ', 'a.nii.gz a.nii    a.img    .', 'a'),
    ]

    indir    = tempfile.mkdtemp()
    outdir   = tempfile.mkdtemp()
    startdir = os.getcwd()

    try:

        for outputType, reldir in it.product(outputTypes, reldirs):

            with mock.patch.dict(os.environ, {'FSLOUTPUTTYPE' : outputType}):

                for files_to_create, imcp_args, files_to_expect in tests:

                    imageHashes = []

                    for i, fname in enumerate(files_to_create.split()):
                        imageHashes.append(makeImage(op.join(indir, fname)))

                    imcp_args = imcp_args.split()

                    tindir  = indir
                    toutdir = outdir

                    if   reldir == 'neutral': reldir = startdir
                    elif reldir == 'indir':   reldir = tindir
                    elif reldir == 'outdir':  reldir = toutdir
                    elif reldir == 'samedir':
                        reldir  = tindir
                        toutdir = tindir

                        if not move:

                            infiles = os.listdir(tindir)

                            files_to_expect = files_to_expect +  ' ' + \
                                              ' '.join(infiles)

                            for inf in infiles:
                                img     = nib.load(op.join(tindir, inf),
                                                   mmap=False)
                                imghash = hash(np.asanyarray(img.dataobj).tobytes())
                                img = None
                                imageHashes.append(imghash)

                    os.chdir(reldir)

                    imcp_args[:-1] = [op.join(tindir, a) for a in imcp_args[:-1]]
                    imcp_args[ -1] =  op.join(toutdir, imcp_args[-1])

                    for i, a in enumerate(imcp_args):
                        if op.splitdrive(a)[0] == op.splitdrive(reldir)[0]:
                            imcp_args[i] = op.relpath(a, reldir)

                    if move: result = immv_script.main(imcp_args)
                    else:    result = imcp_script.main(imcp_args)

                    assert result == 0

                    checkFilesToExpect(
                        files_to_expect, toutdir, outputType, imageHashes)

                    # too hard if indir == outdir
                    if move and tindir != toutdir:
                        infiles = os.listdir(tindir)
                        infiles = [f for f in infiles if op.isfile(f)]
                        infiles = [f for f in infiles if op.isfile(f)]
                        assert len(infiles) == 0

                    cleardir(indir)
                    cleardir(outdir)

    finally:
        os.chdir(startdir)
        shutil.rmtree(indir)
        shutil.rmtree(outdir)


@pytest.mark.noroottest
def test_imcp_script_shouldFail(move=False):

    # - len(srcs) > 1 and dest is not dir
    # - input not readable
    # - move=True and input not deleteable
    # - ambiguous inputs
    # - input is incomplete pair (e.g. .hdr
    #   without corresponding .img)

    # a.img
    # a.hdr
    # a.nii
    #
    # FAIL: imcp a           dest

    # (files_to_create, imcp_args[, preproc])
    tests = [

        # non-existent input
        ('',      'a     b'),
        ('a.img', 'b.img a'),

        # dest is non-existent dir
        ('a.img',       'a.img non_existent_dir/'),

        # len(srcs) > 1, but dest is not dir
        ('a.img b.img', 'a b c.img'),

        # destination not writeable
        ('a.img b.img', 'a b ./readonly_dir', 'mkdir outdir/readonly_dir; chmod a-wx outdir/readonly_dir'),
        ('a.img',       'a    b',             'mkdir outdir/b.nii.gz; chmod a-wx outdir/b.nii.gz'),

        # input not readable
        ('a.img', 'a b', 'chmod a-rwx indir/a.img'),

        # ambiguous input
        ('a.img a.nii', 'a b'),

        # input is part of incomplete pair
        ('a.img', 'a     b', 'rm indir/a.hdr'),
        ('a.img', 'a.img b', 'rm indir/a.hdr'),
        ('a.img', 'a.hdr b', 'rm indir/a.hdr'),
        ('a.img', 'a     b', 'rm indir/a.img'),
        ('a.img', 'a.img b', 'rm indir/a.img'),
        ('a.img', 'a.hdr b', 'rm indir/a.img'),
    ]

    if move:
        tests = tests + [
            # Input not deletable
            ('a.img', 'a b', 'chmod a-wx indir'),
            ('a.img', 'a b', 'chmod a-wx indir'),
            ('a.nii', 'a b', 'chmod a-wx indir')
        ]

    indir  = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()

    try:
        for test in tests:

            files_to_create = test[0]
            imcp_args       = test[1]

            if len(test) == 3: preproc = test[2]
            else:              preproc = None

            files_to_create = files_to_create.split()
            imcp_args       = imcp_args      .split()

            for fname in files_to_create:
                makeImage(op.join(indir, fname))

            imcp_args[:-1] = [op.join(indir, a) for a in imcp_args[:-1]]
            imcp_args[ -1] =  op.join(outdir, imcp_args[-1])

            if preproc is not None:
                for cmd in preproc.split(';'):
                    cmd = cmd.replace('indir', indir).replace('outdir', outdir)
                    sp.call(cmd.split())

            if move: result = immv_script.main(imcp_args)
            else:    result = imcp_script.main(imcp_args)

            assert result != 0

            sp.call('chmod u+rwx {}'.format(indir) .split())
            sp.call('chmod u+rwx {}'.format(outdir).split())

            cleardir(indir)
            cleardir(outdir)

    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)

    # Other failure cases
    if move: assert immv_script.main()       != 0
    else:    assert imcp_script.main()       != 0
    if move: assert immv_script.main([])     != 0
    else:    assert imcp_script.main([])     != 0
    if move: assert immv_script.main(['wa']) != 0
    else:    assert imcp_script.main(['wa']) != 0


def test_immv_script_shouldPass():
    test_imcp_script_shouldPass(move=True)


@pytest.mark.noroottest
def test_immv_script_shouldFail():
    test_imcp_script_shouldFail(move=True)


def test_imcp_badExt():
    with tempdir():

        ihash  = makeImage('file.nii.gz')
        result = imcp_script.main(['file.nii', 'dest'])

        assert result == 0
        assert op.exists('dest.nii.gz')
        checkImageHash('dest.nii.gz', ihash)


def test_immv_badExt():
    with tempdir():

        ihash  = makeImage('file.nii.gz')
        result = immv_script.main(['file.nii', 'dest'])

        assert result == 0
        assert op.exists('dest.nii.gz')
        checkImageHash('dest.nii.gz', ihash)



def _make_file(prefix, ftype, dtype):

    mapping = {
        fslimage.FileType.NIFTI          : (nib.Nifti1Image,  'nii'),
        fslimage.FileType.NIFTI2         : (nib.Nifti2Image,  'nii'),
        fslimage.FileType.ANALYZE        : (nib.AnalyzeImage, 'img'),
        fslimage.FileType.NIFTI_PAIR     : (nib.Nifti1Pair,   'img'),
        fslimage.FileType.NIFTI2_PAIR    : (nib.Nifti2Pair,   'img'),
        fslimage.FileType.ANALYZE_GZ     : (nib.AnalyzeImage, 'img.gz'),
        fslimage.FileType.NIFTI_GZ       : (nib.Nifti1Image,  'nii.gz'),
        fslimage.FileType.NIFTI2_GZ      : (nib.Nifti2Image,  'nii.gz'),
        fslimage.FileType.NIFTI_PAIR_GZ  : (nib.Nifti1Pair,   'img.gz'),
        fslimage.FileType.NIFTI2_PAIR_GZ : (nib.Nifti2Pair,   'img.gz'),
    }

    if np.issubdtype(dtype, np.complex64):
        data = np.random.random((20, 20, 20)).astype(np.float32) + \
               np.random.random((20, 20, 20)).astype(np.float32) * 1j
    else:
        data = np.random.random((20, 20, 20)).astype(dtype)

    cls, suffix = mapping[ftype]
    filename    = f'{prefix}.{suffix}'

    cls(data, None).to_filename(filename)

    return filename


def _is_gzip(filename):
    try:
        with gzip.GzipFile(filename, 'rb') as f:
            f.read()
        return True
    except Exception:
        return False


def _is_pair(imgfile):
    prefix, suffix = fslimage.splitExt(imgfile)
    hdrfile        = imgfile
    if   suffix == '.hdr':    imgfile = f'{prefix}.img'
    elif suffix == '.hdr.gz': imgfile = f'{prefix}.img.gz'
    elif suffix == '.img':    hdrfile = f'{prefix}.hdr'
    elif suffix == '.img.gz': hdrfile = f'{prefix}.hdr.gz'
    return op.exists(imgfile) and op.exists(hdrfile)


def _is_analyze(filename):
    img = nib.load(filename)
    return  _is_pair(filename)                                     and \
            isinstance(img, (nib.AnalyzeImage, nib.AnalyzeHeader)) and \
        not isinstance(img, (nib.Nifti1Image,  nib.Nifti1Header, nib.Nifti1Pair))


def _is_nifti1(filename):
    img = nib.load(filename)
    return  isinstance(img, (nib.Nifti1Image, nib.Nifti1Header, nib.Nifti1Pair)) and \
        not isinstance(img, (nib.Nifti2Image, nib.Nifti2Header, nib.Nifti2Pair))


def _is_nifti2(filename):
    img = nib.load(filename)
    return isinstance(img, (nib.Nifti2Image, nib.Nifti2Header, nib.Nifti2Pair))


def _check_file(prefix, expftype, dtype):
    filename = fslimage.addExt(prefix)
    if   'NIFTI2'  in expftype.name: assert _is_nifti2( filename)
    elif 'NIFTI'   in expftype.name: assert _is_nifti1( filename)
    elif 'ANALYZE' in expftype.name: assert _is_analyze(filename)
    if   'GZ'      in expftype.name: assert _is_gzip(   filename)
    if   'PAIR'    in expftype.name: assert _is_pair(   filename)

    img = nib.load(filename)
    assert np.issubdtype(img.get_data_dtype(), dtype)


def test_imcp_script_correct_output_type(move=False):

    # only testing dtypes supported by ANALYZE
    dtypes = [np.uint8, np.int16, np.float32, np.float64, np.complex64]

    # from, to
    for from_, to_, dtype in it.product(fslimage.FileType, fslimage.FileType, dtypes):
        with tempdir():

            fname = f'f{from_.name}'
            tname = f't{to_.name}'

            _make_file(fname, from_, dtype)

            with mock.patch.dict(os.environ, {'FSLOUTPUTTYPE' : to_.name}):
                if move: immv_script.main([fname, tname])
                else:    imcp_script.main([fname, tname])

            _check_file(tname, to_, dtype)
