#!/usr/bin/env python



import os.path    as op
import itertools  as it
import subprocess as sp
import               os
import               shutil
import               tempfile

import               pytest

import numpy as np
import nibabel as nib

from   fsl.utils.tempdir import tempdir
import fsl.scripts.imcp      as imcp_script
import fsl.scripts.immv      as immv_script

from .. import cleardir
from ..test_immv_imcp import makeImage, checkImageHash, checkFilesToExpect


real_print = print

def print(*args, **kwargs):
    pass





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

                print('adj files_to_expect: ', files_to_expect)

                os.chdir(reldir)

                imcp_args[:-1] = [op.join(tindir, a) for a in imcp_args[:-1]]
                imcp_args[ -1] =  op.join(toutdir, imcp_args[-1])

                for i, a in enumerate(imcp_args):
                    if op.splitdrive(a)[0] == op.splitdrive(reldir)[0]:
                        imcp_args[i] = op.relpath(a, reldir)

                print('indir before:    ', os.listdir(tindir))
                print('outdir before:   ', os.listdir(toutdir))

                if move: result = immv_script.main(imcp_args)
                else:    result = imcp_script.main(imcp_args)

                print('indir after:     ', os.listdir(tindir))
                print('outdir after:    ', os.listdir(toutdir))

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

            print('calling {} {}'.format('immv' if move else 'imcp',
                                         ' '.join(imcp_args)))

            print('indir before:   {}'.format(os.listdir(indir)))
            print('out dir before: {}'.format(os.listdir(outdir)))

            if move: result = immv_script.main(imcp_args)
            else:    result = imcp_script.main(imcp_args)

            print('indir after:   {}'.format(os.listdir(indir)))
            print('out dir after: {}'.format(os.listdir(outdir)))

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

        with open('file.nii.gz', 'wt') as f:
            f.write('1')

        result = imcp_script.main(['file.nii', 'dest'])

        assert result == 0
        assert op.exists('dest.nii.gz')



def test_immv_badExt():
    with tempdir():

        with open('file.nii.gz', 'wt') as f:
            f.write('1')

        result = immv_script.main(['file.nii', 'dest'])

        assert result == 0
        assert op.exists('dest.nii.gz')
