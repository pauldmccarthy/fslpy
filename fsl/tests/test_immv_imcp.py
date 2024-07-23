#!/usr/bin/env python
#
# test_immv_imcp.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from __future__ import print_function

import              gzip
import itertools as it
import os.path   as op
import              os
import              shutil
import              tempfile

from unittest import mock

import numpy   as np
import nibabel as nib

import fsl.utils.imcp    as imcp
import fsl.utils.tempdir as tempdir
import fsl.data.image    as fslimage

from fsl.tests import (make_random_image,
                       make_dummy_file,
                       looks_like_image,
                       sha256)


real_print = print

def print(*args, **kwargs):
    pass


def makeImage(filename):
    return hash(np.asanyarray(make_random_image(filename).dataobj).tobytes())


def checkImageHash(filename, datahash):
    """Checks that the given NIFTI image matches the given hash.
    """

    img = nib.load(filename)
    assert hash(np.asanyarray(img.dataobj).tobytes()) == datahash


def checkFilesToExpect(files, outdir, outputType, datahashes):

    exts = {
        'NIFTI'      : ['.nii'],
        'NIFTI_PAIR' : ['.hdr', '.img'],
        'NIFTI_GZ'   : ['.nii.gz'],
        ''           : ['.nii.gz'],
    }.get(outputType, None)

    allFiles = []

    if isinstance(files, str):
        files = files.split()

    for f in files:

        f, fe = fslimage.splitExt(f)
        fexts = exts

        if fexts is None:
            fexts = {
                '.img'    : ['.hdr', '.img'],
                '.hdr'    : ['.hdr', '.img'],
                '.nii'    : ['.nii'],
                '.nii.gz' : ['.nii.gz']
            }.get(fe, [])
        # filename already has a different extension
        elif fe != '' and fe not in fexts:
            fexts = [fe]

        for e in fexts:

            expected = op.join(outdir, f + e)

            allFiles.append(expected)

            print('  ', expected)

            assert op.exists(expected)

    allThatExist = os.listdir(outdir)
    allThatExist = [f for f in allThatExist if op.isfile(op.join(outdir, f))]

    assert len(allThatExist) == len(allFiles)

    for i, f in enumerate(files):
        f = fslimage.addExt(op.join(outdir, f), mustExist=True)

        if isinstance(datahashes, list):
            if len(datahashes) > len(files):
                diff = len(datahashes) - len(files)
                h    = datahashes[i + diff]

            else:
                h = datahashes[i]
        else:
            h = datahashes[op.basename(f)]

        checkImageHash(f, h)


def test_imcp_shouldPass(move=False):


    #
    # if not useDefaultExt:
    #
    #      imcp src.img dest     -> dest.img
    #      imcp src.img dest.nii -> dest.nii
    #
    # if defaultExt:
    #      imgp src.img dest     -> dest.nii.gz
    #      imgp src.img dest.nii -> dest.nii.gz

    #
    # (files_to_create,
    #    [( imcp_args, files_which_should_exist),
    #     ...
    #    ]
    # )
    shouldPass = [
        ('file.img', [
            ('file     file',     'file.img'),
            ('file     file.img', 'file.img'),
            ('file     file.hdr', 'file.img'),
            ('file     .',        'file.img'),
            ('file.img file',     'file.img'),
            ('file.img file.img', 'file.img'),
            ('file.img file.hdr', 'file.img'),
            ('file.img .',        'file.img'),
            ('file.hdr file',     'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.hdr file.hdr', 'file.img'),
            ('file.hdr .',        'file.img'),
        ]),

        ('file.img file.blob', [
            ('file     file',     'file.img'),
            ('file     file.img', 'file.img'),
            ('file     file.hdr', 'file.img'),
            ('file     .',        'file.img'),
            ('file.img file',     'file.img'),
            ('file.img file.img', 'file.img'),
            ('file.img file.hdr', 'file.img'),
            ('file.img .',        'file.img'),
            ('file.hdr file',     'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.hdr file.hdr', 'file.img'),
            ('file.hdr .',        'file.img'),
        ]),


        ('file.img file.nii', [
            ('file.img file',     'file.img'),
            ('file.img file.img', 'file.img'),
            ('file.img file.hdr', 'file.img'),
            ('file.img .',        'file.img'),
            ('file.hdr file',     'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.hdr file.hdr', 'file.img'),
            ('file.hdr .',        'file.img'),
            ('file.nii file',     'file.nii'),
            ('file.nii file.nii', 'file.nii'),

            # TODO both img/nii files
        ]),


        ('file.nii', [
            ('file     file',     'file.nii'),
            ('file     file.nii', 'file.nii'),
            ('file     .',        'file.nii'),
            ('file.nii file',     'file.nii'),
            ('file.nii file.nii', 'file.nii'),
            ('file.nii .',        'file.nii'),
        ]),

        ('file.nii.gz', [
            ('file        file',        'file.nii.gz'),
            ('file        file.nii.gz', 'file.nii.gz'),
            ('file        .',           'file.nii.gz'),
            ('file.nii.gz file',        'file.nii.gz'),
            ('file.nii.gz file.nii.gz', 'file.nii.gz'),
            ('file.nii.gz .',           'file.nii.gz'),
        ]),


        ('file.nii file.blob', [
            ('file     file',     'file.nii'),
            ('file     file.nii', 'file.nii'),
            ('file     .',        'file.nii'),
            ('file.nii file',     'file.nii'),
            ('file.nii file.nii', 'file.nii'),
            ('file.nii .',        'file.nii'),
        ]),


        ('file.nii file.nii.gz', [
            ('file.nii    file',        'file.nii'),
            ('file.nii    file.nii',    'file.nii'),
            ('file.nii    .',           'file.nii'),
            ('file.nii.gz file',        'file.nii.gz'),
            ('file.nii.gz file.nii.gz', 'file.nii.gz'),
            ('file.nii.gz .',           'file.nii.gz'),

            # TODO both
        ]),

        ('file.img file.nii file.nii.gz', [
            ('file.img file.nii file.nii.gz .', 'file.img file.nii file.nii.gz'),
            ('file.img                      .', 'file.img'),
            ('file.img                      .', 'file.img'),
            ('file.nii                      .', 'file.nii'),
            ('file.nii file.nii.gz          .', 'file.nii file.nii.gz'),
        ]),


        ('001.img 002.img 003.img', [

            ('001     002     003     .', '001.img 002.img 003.img'),
            ('001.img 002.img 003.img .', '001.img 002.img 003.img'),
            ('001.hdr 002.hdr 003.hdr .', '001.img 002.img 003.img'),

            ('001.img 002     003     .', '001.img 002.img 003.img'),
            ('001.hdr 002     003     .', '001.img 002.img 003.img'),

            ('001.img 002.hdr 003.img .', '001.img 002.img 003.img'),
            ('001.hdr 002.img 003.hdr .', '001.img 002.img 003.img'),

            ('001     003             .', '001.img 003.img'),
            ('001.img 003.img         .', '001.img 003.img'),
            ('001.hdr 003.hdr         .', '001.img 003.img'),

            ('001.img 003             .', '001.img 003.img'),
            ('001.hdr 003             .', '001.img 003.img'),

            ('001.img 003.img         .', '001.img 003.img'),
            ('001.hdr 003.hdr         .', '001.img 003.img'),
        ]),
    ]


    indir  = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()

    try:

        for files_to_create, tests in shouldPass:

            files_to_create = files_to_create.split()

            for imcp_args, should_exist in tests:

                should_exist    = should_exist.split()
                imcp_args       = imcp_args.split()
                imcp_srcs       = imcp_args[:-1]
                imcp_dest       = imcp_args[ -1]

                hashes = {}
                for fn in files_to_create:
                    if looks_like_image(fn):
                        hashes[fn] = makeImage(op.join(indir, fn))
                    else:
                        hashes[fn] = make_dummy_file(op.join(indir, fn))

                print()
                print('files_to_create: ', files_to_create)
                print('imcp_srcs:       ', imcp_srcs)
                print('imcp_dest:       ', imcp_dest)
                print('should_exist:    ', should_exist)
                print('indir:           ', os.listdir(indir))

                for src in imcp_srcs:

                    print('  src: {}'.format(src))

                    src = op.join(indir, src)

                    if move: imcp.immv(src, op.join(outdir, imcp_dest), overwrite=True)
                    else:    imcp.imcp(src, op.join(outdir, imcp_dest), overwrite=True)


                print('indir after:     ', os.listdir(indir))
                print('outdir after:    ', os.listdir(outdir))

                # check file contents
                checkFilesToExpect(should_exist,
                                   outdir,
                                   None,
                                   hashes)

                # If move, check that
                # input files are gone
                if move:
                    for f in should_exist:
                         assert not op.exists(op.join(indir, f))

                for f in os.listdir(indir):
                    try:    os.remove(op.join(indir,  f))
                    except: pass

                for f in os.listdir(outdir):
                    os.remove(op.join(outdir, f))


    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)


def test_immv_shouldPass():
    test_imcp_shouldPass(move=True)


def test_imcp_data_unmodified():
    """Test that the data in an imcp'd image file is not modified. """

    dtypes = [
       np.int16,
       np.int32,
       np.float32,
       np.float64]

    slints = [(None, None), (1, 0), (3, 1.5)]

    for dtype, (slope, inter) in it.product(dtypes, slints):
        with tempdir.tempdir():
            data = np.random.randint(1, 100, (10, 10, 10)).astype(dtype)
            hdr  = nib.Nifti1Header()
            hdr.set_data_dtype(dtype)
            hdr.set_data_shape((10, 10, 10))
            hdr.set_slope_inter(slope, inter)
            hdr.set_sform(np.eye(4))

            # write header/data separately, as otherwise
            # nibabel will automatically rescale the data
            with open('image.nii', 'wb') as f:
                hdr.write_to(f)
                f.write(data.tobytes())

            # Input/output formats the same,
            # should induce a straight file copy
            imcp.imcp('image.nii', 'copied.nii', useDefaultExt=False)

            # uncompresed->compressed will cause imcp
            # to load in the image, rather than doing a
            # file copy
            with mock.patch.dict(os.environ, FSLOUTPUTTYPE='NIFTI_GZ'):
                imcp.imcp('image.nii', 'converted.nii.gz', useDefaultExt=True)

            # copied files should be identical
            assert sha256('image.nii') == sha256('copied.nii')

            # Converted files should have the same
            # data, slope, and intercept. Read result
            # header/data separately to avoid nibabel
            # auto-rescaling.
            with gzip.open('converted.nii.gz', 'rb') as f:
                gothdr    = nib.Nifti1Header.from_fileobj(f)
                databytes = f.read()

            gotdata = np.frombuffer(databytes, dtype=dtype).reshape((10, 10, 10))

            # Data should be binary identical
            assert np.all(gotdata == data)

            if slope is None: slope = 1
            if inter is None: inter = 0
            assert np.all(np.isclose(gothdr.get_slope_inter(), (slope, inter)))
