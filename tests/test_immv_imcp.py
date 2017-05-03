#!/usr/bin/env python
#
# test_immv_imcp.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from __future__ import print_function



import               os
import os.path    as op
import               shutil
import subprocess as sp
import               tempfile
import               logging

import numpy   as np
import nibabel as nib

from nibabel.spatialimages import ImageFileError

import pytest

import fsl.utils.path   as fslpath
import fsl.utils.imcp   as imcp
import fsl.scripts.imcp as imcp_script
import fsl.scripts.immv as immv_script
import fsl.data.image   as fslimage

from . import make_random_image
from . import make_dummy_file
from . import looks_like_image
from . import cleardir


real_print = print

def print(*args, **kwargs):
    pass


def makeImage(filename):
    return hash(make_random_image(filename).get_data().tobytes())


def checkImageHash(filename, datahash):
    """Checks that the given NIFTI image matches the given hash.
    """

    img = nib.load(filename)
    assert hash(img.get_data().tobytes()) == datahash


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


def test_imcp_script_shouldPass(move=False):


    # The imcp/immv scripts should honour the
    # FSLOUTPUTTYPE env var. If it is unset
    # or invalid - '' in this case), they
    # should produce .nii.gz
    outputTypes = ['NIFTI', 'NIFTI_PAIR', 'NIFTI_GZ', '']


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

    indir  = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()

    try:

        for outputType in outputTypes:

            os.environ['FSLOUTPUTTYPE'] = outputType

            for files_to_create, imcp_args, files_to_expect in tests:

                imageHashes = []

                print()
                print('files_to_create: ', files_to_create)
                print('imcp_args:       ', imcp_args)
                print('files_to_expect: ', files_to_expect)

                for i, fname in enumerate(files_to_create.split()):
                    imageHashes.append(makeImage(op.join(indir, fname)))

                imcp_args = imcp_args.split()

                imcp_args[:-1] = [op.join(indir, a) for a in imcp_args[:-1]]
                imcp_args[ -1] =  op.join(outdir, imcp_args[-1])

                print('indir before:    ', os.listdir(indir))
                print('outdir before:   ', os.listdir(outdir))

                if move: immv_script.main(imcp_args)
                else:    imcp_script.main(imcp_args)

                print('indir after:     ', os.listdir(indir))
                print('outdir after:    ', os.listdir(outdir))

                checkFilesToExpect(
                    files_to_expect, outdir, outputType, imageHashes)

                if move:
                    infiles = os.listdir(indir)
                    infiles = [f for f in infiles if op.isfile(f)]
                    assert len(infiles) == 0

                cleardir(indir)
                cleardir(outdir)


    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)



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

            try:
                if move: immv_script.main(imcp_args)
                else:    imcp_script.main(imcp_args)
                assert False
            except (RuntimeError, IOError, fslpath.PathError, ImageFileError):
                pass

            sp.call('chmod u+rwx {}'.format(indir) .split())
            sp.call('chmod u+rwx {}'.format(outdir).split())

            cleardir(indir)
            cleardir(outdir)

    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)


def test_immv_script_shouldPass():
    test_imcp_script_shouldPass(move=True)


def test_immv_script_shouldFail():
    test_imcp_script_shouldFail(move=True)


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
