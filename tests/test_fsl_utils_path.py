#!/usr/bin/env python
#
# test_fsl_utils_path.py - Tests functions in the fsl.utils.path module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op

import pytest

import fsl.utils.path as fslpath
import fsl.data.image as fslimage


def test_addExt_exists_shouldPass(testdir):
    """Tests the addExt function where the path exists, and the inputs
    are valid.
    """

    replacements = fslimage.REPLACEMENTS
    allowedExts  = fslimage.ALLOWED_EXTENSIONS

    tests = [
        ('compressed',                     'compressed.nii.gz'),
        ('compressed.nii.gz',              'compressed.nii.gz'),
        ('uncompressed',                   'uncompressed.nii'),
        ('uncompressed.nii',               'uncompressed.nii'),
        ('img_hdr_pair',                   'img_hdr_pair.img'),
        ('img_hdr_pair.hdr',               'img_hdr_pair.hdr'),
        ('img_hdr_pair.img',               'img_hdr_pair.img'),
        ('compressed_img_hdr_pair',        'compressed_img_hdr_pair.img.gz'),
        ('compressed_img_hdr_pair.hdr.gz', 'compressed_img_hdr_pair.hdr.gz'),
        ('compressed_img_hdr_pair.img.gz', 'compressed_img_hdr_pair.img.gz'),
    ]

    for test in tests:
        prefix = op.join(testdir, 'nifti_formats', test[0])
        output = op.join(testdir, 'nifti_formats', test[1]) 

        assert fslpath.addExt(prefix,
                              allowedExts,
                              mustExist=True,
                              replace=replacements) == output


def test_addExt_exists_shouldFail(testdir):
    """Tests the addExt function with inputs that should cause it to raise an
    error.
    """
    
    replacements = fslimage.REPLACEMENTS
    allowedExts  = fslimage.ALLOWED_EXTENSIONS

    shouldFail = [

        # For tests of length 1, allowedExts/replacements are set from above
        #
        # For tests of length 2, replacements is set from above, allowedExts
        #   is set from the tuple (unless False)
        #
        # For tests of length 3, replacements and allowedExts are set
        #   from the tuple (unless False)
        ('compressed', []),
        ('compressed', ['.badsuf']),
        
        ('img_hdr_pair'),
        ('img_hdr_pair', []),
        
        ('ambiguous'),
        ('ambiguous',  []),
        ('ambiguous',  False,   {'.hdr' : ['.img']}),
        ('ambiguous',  [],      {'.hdr' : ['.img']}),
        ('ambiguous',  False,   {'.hdr' : ['.img.gz']}),
        ('ambiguous',  [],      {'.hdr' : ['.img.gz']}),
        ('ambiguous',  False,   {'.hdr' : ['.img', '.img.gz', '.nii']}),
        ('ambiguous',  [],      {'.hdr' : ['.img', '.img.gz', '.nii']}),
        
        ('badpath'),
        ('badpath.nii.gz'),
    ]

    for test in shouldFail:
        prefix  = op.join(testdir, 'nifti_formats', test[0])
        allowed = allowedExts
        replace = replacements 

        if len(test) >= 2:
            if not (test[1] == False):
                allowed = test[1]

        if len(test) == 3:
            if not (test[2] == False):
                replace = test[2]

        with pytest.raises(fslpath.PathError):
            
            fslpath.addExt(prefix,
                           allowed,
                           mustExist=True,
                           replace=replace)


def test_addExt_noExist(testdir):

    allowedExts  = fslimage.ALLOWED_EXTENSIONS 

    # Prefix, output, defaultExt, allowedExts
    tests = [
        ('blah',        'blahblah',    'blah'),
        ('blah',        'blah.blah',  '.blah'),
        ('blah',         None,          None),
        ('blah.nii',     None,          None,  ['blah']),
        ('blah.nii',    'blah.nii',    'blah'),
        ('blah',        'blah.nii',    '.nii'),
        ('blah',        'blah.nii',    '.nii', []),
        ('blah.nii.gz', 'blah.nii.gz', 'blah'),
        ('blah',        'blah.nii',   '.nii'),
        ('blah',        'blah.nii',   '.nii',  []),
    ]

    for test in tests:
        
        prefix = test[0]
        output = test[1]
        
        if len(test) >= 3: default = test[2]
        else:              default = None
        if len(test) >= 4: allowed = test[3]
        else:              allowed = allowedExts

        assert fslpath.addExt(prefix,
                              allowed,
                              defaultExt=default,
                              mustExist=False) == output
            


def test_removeExt(testdir):

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    
    # If len(test) == 2, allowedExts is set from above
    # Otherwise, it is set from the test tuple
    tests = [
        ('blah',        'blah'),
        ('blah.blah',   'blah.blah'),
        ('blah.blah',   'blah', ['.blah']),
        ('blah.blah',   'blah.', ['blah']),
        ('blah.nii',    'blah'),
        ('blah.nii.gz', 'blah'),
        ('blah.img',    'blah'),
        ('blah.hdr',    'blah'),
        ('blah.img.gz', 'blah'),
        ('blah.nii.gz', 'blah.nii.gz', []),
        ('blah.nii.gz', 'blah.nii',    ['.gz']),
        ('blah.nii.gz', 'blah.nii.gz', ['.nii']),
        ('blah.nii.gz', 'blah',        ['.nii.gz']),
        ('blah.nii.gz', 'blah.',        ['nii.gz']),
    ]

    for test in tests:
        
        path   = test[0]
        output = test[1]

        if len(test) == 2: allowed = allowedExts
        else:              allowed = test[2]

        assert fslpath.removeExt(path, allowed) == output


def test_getExt(testdir):

    allowedExts = fslimage.ALLOWED_EXTENSIONS

    # len(test) == 2 -> allowedExts set from above
    # Otherwise, allowedExts set from test tuple
    shouldPass = [
        ('blah.blah',   '.blah',    None),
        ('blah.blah',   '.blah', ['.blah']),
        ('blah.blah',    'blah',  ['blah']),
        ('blah',        '',         None),
        ('blah.nii',    '.nii',     None),
        ('blah.nii.gz', '.gz',      None),

        ('blah.nii',    '.nii'),
        ('blah.nii.gz', '.nii.gz'),
        ('blah.hdr',    '.hdr'),
        ('blah.img',    '.img'),
        ('blah.img.gz', '.img.gz'),
    ]

    shouldRaise = [
        ('blah',        ''),
        ('blah.blah',   ''),
        ('blah.blah',   '', ['bla']),
        ('blah.nii.gz', '', ['.nii']),
    ]

    for test in shouldPass:
        filename = test[0]
        output   = test[1]

        if len(test) == 2: allowed = allowedExts
        else:              allowed = test[2]

        print filename, '==', output
        assert fslpath.getExt(filename, allowed) == output


    for test in shouldRaise:
        filename = test[0]
        output   = test[1]

        if len(test) == 2: allowed = allowedExts
        else:              allowed = test[2]
 
        with pytest.raises(fslpath.PathError):
            fslpath.getExt(filename, allowed)


def test_deepest():

    # path, suffixes, output
    tests = [
        
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat'],           '/blah.feat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat', '.gfeat'], '/blah.feat/foo.ica/fum.gfeat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.gfeat'],          '/blah.feat/foo.ica/fum.gfeat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.ica'],            '/blah.feat/foo.ica/fum.gfeat/moo.ica'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.bob'],              None),
        ('/blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica'],            '/blah.feat/foo.ica'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.bob', ['.bob'],            '/blah.feat/foo.ica/fum.gfeat/moo.bob'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat'],            'blah.feat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat', '.gfeat'],  'blah.feat/foo.ica/fum.gfeat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.gfeat'],           'blah.feat/foo.ica/fum.gfeat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.ica'],             'blah.feat/foo.ica/fum.gfeat/moo.ica'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.bob'],              None),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica'],             'blah.feat/foo.ica'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica', '.bob'],     'blah.feat/foo.ica/fum.gfeat/moo.bob'),
        
        ('/',   [],       None),
        ('',    [],       None),
        ('///', [],       None),
        ('/',   ['blah'], None),
        ('',    ['blah'], None),
        ('///', ['blah'], None),
    ]

    for path, suffixes, output in tests:
        assert fslpath.deepest(path, suffixes) == output


def test_shallowest():
    # path, suffixes, output
    tests = [
        
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat'],           '/blah.feat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat', '.gfeat'], '/blah.feat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.gfeat'],          '/blah.feat/foo.ica/fum.gfeat'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.ica'],            '/blah.feat/foo.ica'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.ica', ['.bob'],              None),
        ('/blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica'],            '/blah.feat/foo.ica'),
        ('/blah.feat/foo.ica/fum.gfeat/moo.bob', ['.bob'],            '/blah.feat/foo.ica/fum.gfeat/moo.bob'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat'],            'blah.feat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.feat', '.gfeat'],  'blah.feat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.gfeat'],           'blah.feat/foo.ica/fum.gfeat'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.ica'],             'blah.feat/foo.ica'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.ica', ['.bob'],              None),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica'],             'blah.feat/foo.ica'),
        ( 'blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica', '.bob'],     'blah.feat/foo.ica'),
        (' blah.feat/foo.ica/fum.gfeat/moo.bob', ['.ica', '.bob'],     'blah.feat/foo.ica'),
        
        ('/',   [],       None),
        ('',    [],       None),
        ('///', [],       None),
        ('/',   ['blah'], None),
        ('',    ['blah'], None),
        ('///', ['blah'], None),
    ]
    
    for path, suffixes, output in tests:
        assert fslpath.shallowest(path, suffixes) == output 
