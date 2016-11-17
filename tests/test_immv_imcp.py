#!/usr/bin/env python
#
# test_immv_imcp.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import            os
import os.path as op
import            shutil
import            tempfile

import numpy   as np
import nibabel as nib

import fsl.utils.path   as fslpath
import fsl.utils.imcp   as imcp
import fsl.scripts.imcp as imcp_script
import fsl.scripts.immv as immv_script
import fsl.data.image   as fslimage


def createImageFile(filename):

    data = np.random.random((10, 10, 10))
    img  = nib.Nifti1Image(data, np.eye(4))

    nib.save(img, filename)

    return hash(data.tobytes())


def checkImageFile(filename, datahash):

    img = nib.load(filename)
    assert hash(img.get_data().tobytes()) == datahash


def checkFilesToExpect(files, outdir, outputType, datahashes):

    exts = {
        'NIFTI'      : ['.nii'],
        'NIFTI_PAIR' : ['.hdr', '.img'],
        'NIFTI_GZ'   : ['.nii.gz'],
    }.get(outputType, ['.nii.gz'])


    allFiles = []

    for f, h in zip(files.split(), datahashes):

        for e in exts:

            expected = op.join(outdir, f + e)

            allFiles.append(expected)

            assert op.exists(expected)

    allThatExist = os.listdir(outdir)
    allThatExist = [f for f in allThatExist if op.isfile(op.join(outdir, f))]

    assert len(allThatExist) == len(allFiles)

    for f, h in zip(files.split(), datahashes):
        f = fslimage.addExt(op.join(outdir, f), mustExist=True)

        checkImageFile(f, h)


def test_imcp_script_shouldPass(move=False):
    

    # The imcp/immv scripts should honour the
    # FSLOUTPUTTYPE env var. If it is unset 
    # or invalid), they should produce .nii.gz
    outputTypes = ['NIFTI', 'NIFTI_PAIR', 'NIFTI_GZ', 'BLAH_DI_BLAH']
 

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
    ]

    indir  = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()
    
    try:

        for outputType in outputTypes:
            
            os.environ['FSLOUTPUTTYPE'] = outputType
            
            for files_to_create, imcp_args, files_to_expect in tests:

                imageHashes = []

                print 
                print 'files_to_create: ', files_to_create
                print 'imcp_args:       ', imcp_args
                print 'files_to_expect: ', files_to_expect

                for fname in files_to_create.split():
                    imageHashes.append(createImageFile(op.join(indir, fname)))

                imcp_args = imcp_args.split()

                imcp_args[:-1] = [op.join(indir, a) for a in imcp_args[:-1]]
                imcp_args[ -1] =  op.join(outdir, imcp_args[-1])


                if move: immv_script.main(imcp_args)
                else:    imcp_script.main(imcp_args)

                checkFilesToExpect(files_to_expect, outdir, outputType, imageHashes)

                if move:
                    infiles = os.listdir(indir)
                    infiles = [f for f in infiles if op.isfile(f)]
                    assert len(infiles) == 0

                for f in os.listdir(outdir):
                    f = op.join(outdir, f)
                    if op.isfile(f):
                        os.remove(f)

                for f in os.listdir(indir):
                    f = op.join(indir, f)
                    if op.isfile(f):
                        os.remove(f)
        
    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)
        


def test_imcp_script_shouldFail(move=False):

    # - non-existent input
    # - destination exists
    # - input not readable
    # - move=True and input not deleteable
    # - destination not writeable
    pass

def test_immv_script_shouldPass():
    test_imcp_script_shouldPass(move=True)


def test_imcp_shouldPass(move=False):

    # 
    # (files_to_create,
    #    [( imcp_src,   imcp_dest,  files_which_should_exist),
    #     ( imcp_src,   imcp_dest, [files_which_should_exist]),
    #     ([imcp_srcs], imcp_dest,  files_which_should_exist),
    #     ([imcp_srcs], imcp_dest, [files_which_should_exist]),
    #     ...
    #    ]
    # )
    #
    # if icmp_dest == '', it means to copy to the directory
    # files_which_should_exist == 'all' is equivalent to files_which_should_exist == files_to_create
    shouldPass = [
        (['file.hdr', 'file.img'], [
            ('file',     'file',     'all'),
            ('file',     'file.img', 'all'),
            ('file',     'file.hdr', 'all'),
            ('file',     '',         'all'),
            ('file.img', 'file',     'all'),
            ('file.img', 'file.img', 'all'),
            ('file.img', 'file.hdr', 'all'),
            ('file.img', '',         'all'),
            ('file.hdr', 'file',     'all'),
            ('file.hdr', 'file.img', 'all'),
            ('file.hdr', 'file.hdr', 'all'),
            ('file.hdr', '',         'all'),
        ]),

        (['file.hdr', 'file.img', 'file.blob'], [
            ('file',     'file',     ['file.hdr', 'file.img']),
            ('file',     'file.img', ['file.hdr', 'file.img']),
            ('file',     'file.hdr', ['file.hdr', 'file.img']),
            ('file',     '',         ['file.hdr', 'file.img']),
            ('file.img', 'file',     ['file.hdr', 'file.img']),
            ('file.img', 'file.img', ['file.hdr', 'file.img']),
            ('file.img', 'file.hdr', ['file.hdr', 'file.img']),
            ('file.img', '',         ['file.hdr', 'file.img']),
            ('file.hdr', 'file',     ['file.hdr', 'file.img']),
            ('file.hdr', 'file.img', ['file.hdr', 'file.img']),
            ('file.hdr', 'file.hdr', ['file.hdr', 'file.img']),
            ('file.hdr', '',         ['file.hdr', 'file.img']),
        ]),


        (['file.hdr', 'file.img', 'file.nii'], [
            ('file.img', 'file',     ['file.hdr', 'file.img']),
            ('file.img', 'file.img', ['file.hdr', 'file.img']),
            ('file.img', 'file.hdr', ['file.hdr', 'file.img']),
            ('file.img', '',         ['file.hdr', 'file.img']),
            ('file.hdr', 'file',     ['file.hdr', 'file.img']),
            ('file.hdr', 'file.img', ['file.hdr', 'file.img']),
            ('file.hdr', 'file.hdr', ['file.hdr', 'file.img']),
            ('file.hdr', '',         ['file.hdr', 'file.img']),
            ('file.nii', 'file',     'file.nii'),
            ('file.nii', 'file.nii', 'file.nii'),
            ('file.nii', '',         'file.nii'),
        ]),        
                
        
        (['file.nii'], [
            ('file',     'file',     'all'),
            ('file',     'file.nii', 'all'),
            ('file',     '',         'all'),
            ('file.nii', 'file',     'all'),
            ('file.nii', 'file.nii', 'all'),
            ('file.nii', '',         'all'),
        ]),

        (['file.nii.gz'], [
            ('file',        'file',        'all'),
            ('file',        'file.nii.gz', 'all'),
            ('file',        '',            'all'),
            ('file.nii.gz', 'file',        'all'),
            ('file.nii.gz', 'file.nii.gz', 'all'),
            ('file.nii.gz', '',            'all'),
        ]),

        
        (['file.nii', 'file.blob'], [
            ('file',     'file',     'file.nii'),
            ('file',     'file.nii', 'file.nii'),
            ('file',     '',         'file.nii'),
            ('file.nii', 'file',     'file.nii'),
            ('file.nii', 'file.nii', 'file.nii'),
            ('file.nii', '',         'file.nii'),
        ]), 
        

        (['file.nii', 'file.nii.gz'], [
            ('file.nii',    'file',        'file.nii'),
            ('file.nii',    'file.nii',    'file.nii'),
            ('file.nii',    '',            'file.nii'),
            ('file.nii.gz', 'file',        'file.nii.gz'),
            ('file.nii.gz', 'file.nii.gz', 'file.nii.gz'),
            ('file.nii.gz', '',            'file.nii.gz'),
        ]),

        (['file.hdr', 'file.img', 'file.nii', 'file.nii.gz'], [
            (['file.img', 'file.nii', 'file.nii.gz'], '', 'all'),
            ('file.img',                              '', ['file.hdr', 'file.img']),
            (['file.hdr', 'file.img'],                '', ['file.hdr', 'file.img']),

            ('file.nii',                              '', 'file.nii'),
            (['file.nii', 'file.nii.gz'],             '', ['file.nii', 'file.nii.gz']),
        ]),


        (['001.hdr', '001.img', '002.hdr', '002.img', '003.hdr', '003.img'], [
            
            (['001',     '002',     '003'],                                      '', 'all'),
            (['001.img', '002.img', '003.img'],                                  '', 'all'),
            (['001.hdr', '002.hdr', '003.hdr'],                                  '', 'all'),
                                                                                    
            (['001.img', '002',     '003'],                                      '', 'all'),
            (['001.hdr', '002',     '003'],                                      '', 'all'),

            (['001.img', '002.hdr', '003.img'],                                  '', 'all'),
            (['001.hdr', '002.img', '003.hdr'],                                  '', 'all'),

            (['001',     '003'],                                                 '', ['001.hdr', '001.img', '003.hdr', '003.img']),
            (['001.img', '003.img'],                                             '', ['001.hdr', '001.img', '003.hdr', '003.img']),
            (['001.hdr', '003.hdr'],                                             '', ['001.hdr', '001.img', '003.hdr', '003.img']),
                                                                         
            (['001.img', '003'],                                                 '', ['001.hdr', '001.img', '003.hdr', '003.img']),
            (['001.hdr', '003'],                                                 '', ['001.hdr', '001.img', '003.hdr', '003.img']),

            (['001.img', '003.img'],                                             '', ['001.hdr', '001.img', '003.hdr', '003.img']),
            (['001.hdr', '003.hdr'],                                             '', ['001.hdr', '001.img', '003.hdr', '003.img']), 

            (['001.img', '001.hdr', '002.img', '002.hdr', '003.img', '003.hdr'], '', 'all'),
        ]),  
    ]


    indir  = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()

    try:

        for files_to_create, tests in shouldPass:
            
            if not isinstance(files_to_create, list):
                files_to_create = [files_to_create]
                
            for imcp_src, imcp_dest, should_exist in tests:

                if   not isinstance(imcp_src, list):     imcp_src     = [imcp_src]
                if   should_exist == 'all':              should_exist = list(files_to_create)
                elif not isinstance(should_exist, list): should_exist = [should_exist]

                imcp_dest = op.join(outdir, imcp_dest)

                # Each input file contains
                # its name in plain text,
                # so we can verify that the
                # files were correctly copied
                hashes = []
                for fn in files_to_create:
                    hashes.append(createImageFile(op.join(indir, fn)))

                print()
                print('files_to_create: ', files_to_create)
                print('imcp_src:        ', imcp_src)
                print('imcp_dest:       ', imcp_dest)
                print('should_exist:    ', should_exist)

                for src in imcp_src:

                    print('  src: {}'.format(src))

                    src = op.join(indir, src)
                    
                    if move: imcp.immv(src, imcp_dest, overwrite=True)
                    else:    imcp.imcp(src, imcp_dest, overwrite=True)

                copied = os.listdir(outdir)
                copied = [f for f in copied if op.isfile(op.join(outdir, f))]

                assert sorted(copied) == sorted(should_exist)


                # check file contents 
                for fn in should_exist:
                    with open(op.join(outdir, fn), 'rt') as f:
                        assert f.read() == '{}\n'.format(fn)

                # If move, check that
                # input files are gone
                if move:
                    for f in should_exist:
                         assert not op.exists(op.join(indir, f))
                         
                for f in files_to_create:
                    try:    os.remove(op.join(indir,  f))
                    except: pass
                        
                for f in should_exist:
                    os.remove(op.join(outdir, f))
        
        
    finally:
        shutil.rmtree(indir)
        shutil.rmtree(outdir)


def test_immv_shouldPass():
    test_imcp_shouldPass(move=True)
