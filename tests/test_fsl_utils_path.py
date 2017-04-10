#!/usr/bin/env python
#
# test_fsl_utils_path.py - Tests functions in the fsl.utils.path module.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from __future__ import print_function

import            os
import os.path as op
import            shutil
import            tempfile

import pytest

import fsl.utils.path as fslpath
import fsl.data.image as fslimage


real_print = print
def print(*a, **kwa):
    pass


def make_dummy_file(path):
    with open(path, 'wt') as f:
        f.write('{}\n'.format(op.basename(path))) 


def make_dummy_image_file(path):

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
    for f in os.listdir(dir):
        f = op.join(dir, f)
        if op.isfile(f):
            os.remove(f) 


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


def test_addExt_imageFiles_mustExist_shouldPass():
    """Tests the addExt function where the path exists, and the inputs
    are valid.
    """

    groups       = fslimage.FILE_GROUPS
    allowedExts  = fslimage.ALLOWED_EXTENSIONS

    # (files_to_create, path, expected)
    tests = [

        # Single files
        ('file.nii',         'file',        'file.nii'),
        ('file.nii',         'file.nii',    'file.nii'), 
        ('file.nii.gz',      'file',        'file.nii.gz'),
        ('file.nii.gz',      'file.nii.gz', 'file.nii.gz'),
        ('file.img',         'file',        'file.img'),
        ('file.img',         'file.hdr',    'file.hdr'),
        ('file.img',         'file.img',    'file.img'),
        ('file.img.gz',      'file',        'file.img.gz'),
        ('file.img.gz',      'file.hdr.gz', 'file.hdr.gz'),
        ('file.img.gz',      'file.img.gz', 'file.img.gz'),

        # Multiple suffixes should be handled
        ('file.blob.nii',    'file.blob',        'file.blob.nii'),
        ('file.blob.nii',    'file.blob.nii',    'file.blob.nii'),
        ('file.blob.nii.gz', 'file.blob',        'file.blob.nii.gz'),
        ('file.blob.nii.gz', 'file.blob.nii.gz', 'file.blob.nii.gz'),
        ('file.blob.img',    'file.blob',        'file.blob.img'),
        ('file.blob.hdr',    'file.blob.hdr',    'file.blob.hdr'),
        ('file.blob.img',    'file.blob.img',    'file.blob.img'),
        ('file.blob.img.gz', 'file.blob',        'file.blob.img.gz'),
        ('file.blob.hdr.gz', 'file.blob.hdr.gz', 'file.blob.hdr.gz'),
        ('file.blob.img.gz', 'file.blob.img.gz', 'file.blob.img.gz'), 
        
        # Even if that suffix is a itself supported 
        # suffix (as long as the path is unambiguous)
        
        ('file.img.nii',    'file.img.nii',    'file.img.nii'),
        ('file.img.nii.gz', 'file.img.nii.gz', 'file.img.nii.gz'),
        ('file.img.hdr',    'file.img.hdr',    'file.img.hdr'),
        ('file.img.img',    'file.img.img',    'file.img.img'),
        ('file.img.hdr.gz', 'file.img.hdr.gz', 'file.img.hdr.gz'),
        ('file.img.img.gz', 'file.img.img.gz', 'file.img.img.gz'),

        
        # Multiple files exist, but prefix is unambiguous
        ('file.nii     file.nii.gz',  'file.nii',     'file.nii'),
        ('file.nii     file.nii.gz',  'file.nii.gz',  'file.nii.gz'),
        
        ('file1.nii    file2.nii.gz', 'file1',        'file1.nii'),
        ('file1.nii    file2.nii.gz', 'file1.nii',    'file1.nii'),
        ('file1.nii    file2.nii.gz', 'file2',        'file2.nii.gz'),
        ('file1.nii    file2.nii.gz', 'file2.nii.gz', 'file2.nii.gz'),
        
        ('file.nii     file.img',     'file.nii',     'file.nii'),
        ('file.nii     file.img',     'file.img',     'file.img'),
        ('file.nii     file.img',     'file.hdr',     'file.hdr'),

        ('file.img.gz  file.img',     'file.img',     'file.img'),
        ('file.img.gz  file.img',     'file.hdr',     'file.hdr'),
        ('file.img.gz  file.img',     'file.img.gz',  'file.img.gz'),
        ('file.img.gz  file.img',     'file.hdr.gz',  'file.hdr.gz'),

        ('file1.img.gz file2.img',    'file2',        'file2.img'),
        ('file1.img.gz file2.img',    'file2.img',    'file2.img'),
        ('file1.img.gz file2.img',    'file2.hdr',    'file2.hdr'),
        ('file1.img.gz file2.img',    'file1',        'file1.img.gz'),
        ('file1.img.gz file2.img',    'file1.img.gz', 'file1.img.gz'),
        ('file1.img.gz file2.img',    'file1.hdr.gz', 'file1.hdr.gz'), 
        
        ('file1.nii    file2.img',    'file1',        'file1.nii'),
        ('file1.nii    file2.img',    'file1.nii',    'file1.nii'),
        ('file1.nii    file2.img',    'file2',        'file2.img'),
        ('file1.nii    file2.img',    'file2.hdr',    'file2.hdr'),
        ('file1.nii    file2.img',    'file2.img',    'file2.img'),
        
        ('file1.img    file2.img',    'file1',        'file1.img'),
        ('file1.img    file2.img',    'file1.hdr',    'file1.hdr'),
        ('file1.img    file2.img',    'file1.img',    'file1.img'),
        ('file1.img    file2.img',    'file2',        'file2.img'),
        ('file1.img    file2.img',    'file2.hdr',    'file2.hdr'),
        ('file1.img    file2.img',    'file2.img',    'file2.img'), 
    ]

    workdir = tempfile.mkdtemp()

    try:

        for files_to_create, prefix, expected in tests:

            files_to_create = files_to_create.split()
            for f in files_to_create:
                make_dummy_image_file(op.join(workdir, f))

            print('files_to_create: ', files_to_create)
            print('workdir:         ', os.listdir(workdir))
            print('prefix:          ', prefix)
            print('expected:        ', expected)

            result =  fslpath.addExt(op.join(workdir, prefix),
                                     allowedExts,
                                     mustExist=True,
                                     fileGroups=groups)

            print('result:          ', result)

            assert result == op.join(workdir, expected)

            cleardir(workdir)
            
    finally:
        shutil.rmtree(workdir)
            

def test_addExt_otherFiles_mustExist_shouldPass():

    workdir = tempfile.mkdtemp()


    # (files_to_create, path, allowedExts, filegroups, expected)
    tests = [

        # allowedExts is None, fileGroups is None
        ('file.a',        'file.a', '', [], 'file.a'),
        ('file.a file.b', 'file.a', '', [], 'file.a'),
        ('file.a file.b', 'file.b', '', [], 'file.b'),

        # fileGroups is None
        ('file.a',        'file',   '.a', [], 'file.a'),
        ('file.a',        'file.a', '.a', [], 'file.a'),


        ('file.a file.b',   'file',     '.a',    [], 'file.a'),
        ('file.a file.b',   'file.a',   '.a',    [], 'file.a'),
        ('file.a file.b',   'file.b',   '.a .b', [], 'file.b'),

        ('file1.a file2.b', 'file1',    '.a .b', [], 'file1.a'),
        ('file1.a file2.b', 'file1.a',  '.a .b', [], 'file1.a'),
        ('file1.a file2.b', 'file2.b',  '.a .b', [], 'file2.b'),
        ('file1.a file2.b', 'file2.b',  '.a .b', [], 'file2.b'),

        ('file.a file.b', 'file',   '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b', 'file',   '.a .b', ['.b .a'], 'file.b'),
        ('file.a file.b', 'file.a', '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b', 'file.b', '.a .b', ['.a .b'], 'file.b'),
        ('file.a file.b', 'file.a', '.a .b', ['.b .a'], 'file.a'),
        ('file.a file.b', 'file.b', '.a .b', ['.b .a'], 'file.b'), 

        ('file.a file.b file.c file.d', 'file',     '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b file.c file.d', 'file',     '.a .b', ['.b .a'], 'file.b'),
        ('file.a file.b file.c file.d', 'file.a',   '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b file.c file.d', 'file.b',   '.a .b', ['.a .b'], 'file.b'),

        ('file1.a file1.b file2.a file2.b', 'file1',   '.a .b', ['.a .b'], 'file1.a'),
        ('file1.a file1.b file2.a file2.b', 'file1.a', '.a .b', ['.a .b'], 'file1.a'),
        ('file1.a file1.b file2.a file2.b', 'file1.b', '.a .b', ['.a .b'], 'file1.b'),
        ('file1.a file1.b file2.a file2.b', 'file2',   '.a .b', ['.a .b'], 'file2.a'),
        ('file1.a file1.b file2.a file2.b', 'file2.a', '.a .b', ['.a .b'], 'file2.a'),
        ('file1.a file1.b file2.a file2.b', 'file2.b', '.a .b', ['.a .b'], 'file2.b'),

        ('file1.a file1.b file2.c file2.d', 'file1',   '.a .b .c .d', ['.a .b', '.c .d'], 'file1.a'),
        ('file1.a file1.b file2.c file2.d', 'file1.a', '.a .b .c .d', ['.a .b', '.c .d'], 'file1.a'),
        ('file1.a file1.b file2.c file2.d', 'file1.b', '.a .b .c .d', ['.a .b', '.c .d'], 'file1.b'),
        ('file1.a file1.b file2.c file2.d', 'file2',   '.a .b .c .d', ['.a .b', '.c .d'], 'file2.c'),
        ('file1.a file1.b file2.c file2.d', 'file2.c', '.a .b .c .d', ['.a .b', '.c .d'], 'file2.c'),
        ('file1.a file1.b file2.c file2.d', 'file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file2.d'), 
    ]

    try:

        for files_to_create, prefix, allowedExts, fileGroups, expected in tests:

            files_to_create = files_to_create.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]

            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None
 
            for f in files_to_create:
                make_dummy_file(op.join(workdir, f))

            print('files_to_create: ', files_to_create)
            print('prefix:          ', prefix)
            print('allowedExts:     ', allowedExts)
            print('fileGroups:      ', fileGroups)
            print('workdir:         ', os.listdir(workdir))
            print('expected:        ', expected)

            result =  fslpath.addExt(op.join(workdir, prefix),
                                     allowedExts=allowedExts,
                                     mustExist=True,
                                     fileGroups=fileGroups)

            print('result:          ', result)

            assert result == op.join(workdir, expected)

            cleardir(workdir)

    finally:
        shutil.rmtree(workdir)


def test_addExt_imageFiles_mustExist_shouldFail():
    """Tests the addExt function with inputs that should cause it to raise an
    error.
    """

    fileGroups  = fslimage.FILE_GROUPS
    allowedExts = fslimage.ALLOWED_EXTENSIONS

    # All of these should raise an error

    # (files_to_create, path)
    tests = [

        # Invalid path
        ('',                           'file.img'),
        ('file.hdr    file.img',       'blob'),
        ('file.hdr.gz file.img.gz',    'file.img'),
        ('file.hdr    file.img',       'file1'),
        ('file.hdr    file.img',       'file1.im'),
        
        ('file.hdr    file.img',       'filehdr'),
        ('file.hdr    file.img',       'fileimg'),
        ('filehdr     fileimg',        'file.hdr'),
        ('filehdr     fileimg',        'file.img'),
        ('file.hdr    fileimg',        'filehdr'),
        ('file.hdr    fileimg',        'file.img'),
        ('filehdr     file.img',       'fileimg'),
        ('filehdr     file.img',       'file.hdr'), 

        # Unsupported type/invalid path
        ('file.blob', 'file'),
        ('file.blob', 'file.img'),
        ('file.blob', 'file.nii'),
        ('file.blob', 'file.blob'),

        # Ambiguous path
        ('file.hdr file.img file.nii',                'file'),
        ('file.hdr file.img file.hdr.gz file.img.gz', 'file'),

        # Incomplete file pairs
        ('file.hdr',             'file.img'),
        ('file.img',             'file.hdr'),        
        ('file1.hdr  file2.img', 'file1.img'), 
        ('file1.hdr  file2.img', 'file2.hdr'),

        # Stupid file names
        ('file.img.nii.gz', 'file.img'),
        ('file.img.nii',    'file.img'),
        ('file.img.img',    'file.img'),
        ('file.img.img.gz', 'file.img'),
    ]

    workdir = tempfile.mkdtemp()

    try:

        for files_to_create, prefix in tests:

            cleardir(workdir)

            files_to_create = files_to_create.split()
            for f in files_to_create:
                make_dummy_file(op.join(workdir, f))

            print('files_to_create: ', files_to_create)
            print('prefix:          ', prefix)
            print('workdir:         ', os.listdir(workdir))
            
            with pytest.raises(fslpath.PathError):

                result = fslpath.addExt(op.join(workdir, prefix),
                                        allowedExts=allowedExts,
                                        mustExist=True,
                                        fileGroups=fileGroups)

                print('result:          ', result)

    finally:
        shutil.rmtree(workdir)

        
def test_addExt_otherFiles_mustExist_shouldFail():

    workdir = tempfile.mkdtemp()

    # Invalid path
    # Unsupported suffix

    # (files_to_create, path, allowedExts, fileGroups)
    tests = [

        # Invalid path
        ('',       'file.a', '',   []),
        ('file.b', 'file.a', '.a', []),
        ('file.b', 'file.a', '.a', []),

        # No supported extensions/ambiguous
        ('file.a',        'file',   '',      []),
        ('file.a file.b', 'file',   '',      []),
        ('file.a file.b', 'file',   '.a .b', []),

        # Weird group
        ('file.a file.b', 'file',   '.a .b', ['.a']),

        # Multiple groups, ambiguous path
        ('file.a file.b file.c file.d', 'file',  '.a .b .c .d', ['.a .b', '.c .d']),
    ]
    
    try:
        for files_to_create, prefix, allowedExts, fileGroups in tests:

            cleardir(workdir)

            files_to_create = files_to_create.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]
            
            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None

            for f in files_to_create:
                make_dummy_file(op.join(workdir, f))

            print('files_to_create: ', files_to_create)
            print('prefix:          ', prefix)
            print('workdir:         ', os.listdir(workdir)) 

            with pytest.raises(fslpath.PathError):

                result = fslpath.addExt(op.join(workdir, prefix),
                                        allowedExts=allowedExts,
                                        mustExist=True,
                                        fileGroups=fileGroups)

                print('result:          ', result)
                                

    finally:
        shutil.rmtree(workdir)
    pass
        

def test_addExt_noExist():

    allowedExts  = fslimage.ALLOWED_EXTENSIONS

    # When mustExist=False, the addExt 
    # function does not consult fileGroups. 
    # So we are not bothering with them
    # here.

    # Prefix, defaultExt, allowedExts, expected
    tests = [

        # If the prefix already has a supported extension,
        # it should be returned unchanged.
        ('file.img',       None,   allowedExts,  'file.img'),
        ('file.hdr',       None,   allowedExts,  'file.hdr'),
        ('file.nii',       None,   allowedExts,  'file.nii'),
        ('file.nii.gz',    None,   allowedExts,  'file.nii.gz'),
        ('file.img.gz',    None,   allowedExts,  'file.img.gz'),
        ('file.hdr.gz',    None,   allowedExts,  'file.hdr.gz'),
        ('file.blob.img',  '.img', allowedExts,  'file.blob.img'),
        ('file.blob.img',  '.img', None,         'file.blob.img'),        
 
        
        # If the file does not have a prefix,
        # it should be given the default prefix
        ('file',         'img', allowedExts,  'fileimg'),
        ('file',        '.img', allowedExts,  'file.img'),
        ('file',         'img', None,         'fileimg'),
        ('file',        '.img', None,         'file.img'), 

        # Unrecognised prefixes should be ignored
        ('file.blob',    'img', allowedExts,  'file.blobimg'),
        ('file.blob',   '.img', allowedExts,  'file.blob.img'),
        ('file.blob',    'img', None,         'file.blobimg'),
        ('file.blob',   '.img', None,         'file.blob.img'),
    ]

    for prefix, defaultExt, allowedExts, expected in tests:
        
        assert fslpath.addExt(prefix,
                              allowedExts,
                              defaultExt=defaultExt,
                              mustExist=False) == expected


def test_removeExt():

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


def test_getExt():

    allowedExts = fslimage.ALLOWED_EXTENSIONS

    # len(test) == 2 -> allowedExts set from above
    # Otherwise, allowedExts set from test tuple
    tests = [
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

        ('blah',        ''),
        ('blah.blah',   ''),
        ('blah.blah',   '', ['bla']),
        ('blah.nii.gz', '', ['.nii']),
    ]

    for test in tests:
        filename = test[0]
        output   = test[1]

        if len(test) == 2: allowed = allowedExts
        else:              allowed = test[2]

        print(filename, '==', output)
        assert fslpath.getExt(filename, allowed) == output

        
def test_splitExt():

    allowedExts = fslimage.ALLOWED_EXTENSIONS

    # len(test) == 2 -> allowedExts set from above
    # Otherwise, allowedExts set from test tuple 
    tests = [
        ('blah',         ('blah',        '')),
        ('blah.blah',    ('blah.blah',   '')),
        ('blah.blah',    ('blah',        '.blah'),   ['.blah']),
        ('blah.blah',    ('blah.',       'blah'),    ['blah']),
        ('blah.nii',     ('blah',        '.nii')),
        ('blah.nii.gz',  ('blah',        '.nii.gz')),
        ('blah.img',     ('blah',        '.img')),
        ('blah.hdr',     ('blah',        '.hdr')),
        ('blah.img.gz',  ('blah',        '.img.gz')),
        ('blah.nii.gz',  ('blah.nii.gz', ''),        []),
        ('blah.nii.gz',  ('blah.nii',    '.gz'),     ['.gz']),
        ('blah.nii.gz',  ('blah.nii.gz', ''),        ['.nii']),
        ('blah.nii.gz',  ('blah',        '.nii.gz'), ['.nii.gz']),
        ('blah.nii.gz',  ('blah.',       'nii.gz'),  ['nii.gz']),
        ('blah.blah',    ('blah',        '.blah'),   None),
        ('blah.blah',    ('blah',        '.blah'),   ['.blah']),
        ('blah.blah',    ('blah.',       'blah'),    ['blah']),
        ('blah',         ('blah',        ''),        None),
        ('blah.nii',     ('blah',        '.nii'),    None),
        ('blah.nii.gz',  ('blah.nii',    '.gz'),     None),

        ('blah.nii',    ('blah', '.nii')),
        ('blah.nii.gz', ('blah', '.nii.gz')),
        ('blah.hdr',    ('blah', '.hdr')),
        ('blah.img',    ('blah', '.img')),
        ('blah.img.gz', ('blah', '.img.gz')),

        ('blah',        ('blah',        '')),
        ('blah.blah',   ('blah.blah',   '')),
        ('blah.blah',   ('blah.blah',   ''), ['bla']),
        ('blah.nii.gz', ('blah.nii.gz', ''), ['.nii']), 
    ]

    for test in tests:
        filename          = test[0]
        outbase, outext   = test[1]

        if len(test) == 2: allowed = allowedExts
        else:              allowed = test[2]

        print(filename, '==', (outbase, outext))
        assert fslpath.splitExt(filename, allowed) == (outbase, outext)
        

    
def test_getFileGroup_imageFiles_shouldPass():

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    groups      = fslimage.FILE_GROUPS

    # [(files_to_create, path, files_to_expect [, unambiguous]),
    #   ...
    # ]
    #
    tests = [
        ('file.hdr file.img', 'file',     'file.hdr file.img'),
        ('file.hdr file.img', 'file.img', 'file.hdr file.img'),
        ('file.hdr file.img', 'file.hdr', 'file.hdr file.img'),

        ('file.hdr.gz file.img.gz', 'file',        'file.hdr.gz file.img.gz'),
        ('file.hdr.gz file.img.gz', 'file.img.gz', 'file.hdr.gz file.img.gz'),
        ('file.hdr.gz file.img.gz', 'file.hdr.gz', 'file.hdr.gz file.img.gz'),

        ('file.hdr file.img file.hdr.gz file.img.gz', 'file.hdr',    'file.hdr    file.img'),
        ('file.hdr file.img file.hdr.gz file.img.gz', 'file.img',    'file.hdr    file.img'),
        ('file.hdr file.img file.hdr.gz file.img.gz', 'file.hdr.gz', 'file.hdr.gz file.img.gz'),
        ('file.hdr file.img file.hdr.gz file.img.gz', 'file.hdr.gz', 'file.hdr.gz file.img.gz'),

        ('file.hdr file.img file.nii', 'file.img', 'file.hdr file.img'),
        ('file.hdr file.img file.nii', 'file.hdr', 'file.hdr file.img'),

        ('file.hdr file.img file.blob', 'file',     'file.hdr file.img'),
        ('file.hdr file.img file.blob', 'file.hdr', 'file.hdr file.img'),
        ('file.hdr file.img file.blob', 'file.img', 'file.hdr file.img'),

        ('file.nii', 'file',     'file.nii'),
        ('file.nii', 'file.nii', 'file.nii'),

        ('file.nii file.hdr file.img', 'file.nii', 'file.nii'),
        ('file.nii file.blob',         'file',     'file.nii'),
        ('file.nii file.blob',         'file.nii', 'file.nii'),

        # The unambiguous arg defaults to
        # False, so paths to incomplete
        # file groups should still work.
        ('file.hdr', 'file',     'file.hdr'),
        ('file.hdr', 'file.hdr', 'file.hdr'),

        # Unambigiuous paths, when
        # unambiguous = True,
        # should be ok.
        ('file.hdr file.img file.nii', 'file.nii', 'file.nii',          True),
        ('file.hdr file.img file.nii', 'file.hdr', 'file.hdr file.img', True),
        ('file.hdr file.img file.nii', 'file.img', 'file.hdr file.img', True),
        
    ]

    # TODO You need to add passing tests for unambiguous=True

    workdir = tempfile.mkdtemp()

    try: 

        for test in tests:

            files_to_create = test[0]
            path            = test[1]
            files_to_expect = test[2]

            if len(test) == 4: unambiguous = test[3]
            else:              unambiguous = False

            files_to_create = files_to_create.split()
            files_to_expect = files_to_expect.split()

            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            print()
            print('files_to_create: ', files_to_create)
            print('path:            ', path)
            print('files_to_expect: ', files_to_expect)

            fullPaths = fslpath.getFileGroup(
                op.join(workdir, path),
                allowedExts=allowedExts,
                fileGroups=groups,
                fullPaths=True,
                unambiguous=unambiguous)
            exts = fslpath.getFileGroup(
                op.join(workdir, path),
                allowedExts=allowedExts,
                fileGroups=groups,
                fullPaths=False,
                unambiguous=unambiguous)

            assert sorted(fullPaths) == sorted([op.join(workdir, e)            for e in files_to_expect])
            assert sorted(exts)      == sorted([fslpath.getExt(e, allowedExts) for e in files_to_expect])

            cleardir(workdir)

    finally:
        shutil.rmtree(workdir)


def test_getFileGroup_otherFiles_shouldPass():

    # (files_to_create, allowedExts, fileGroups, path, files_to_expect [, unambiguous])

    tests = [
        # allowedExts is None - incomplete paths are not allowed
        ('file.a',        '', '',        'file.a', 'file.a'),
        ('file.a file.b', '', '',        'file.a', 'file.a'),
        ('file.a file.b', '', '',        'file.b', 'file.b'),
        ('file.a file.b', '', ['.a .b'], 'file.a', 'file.a file.b'),
        ('file.a file.b', '', ['.a .b'], 'file.b', 'file.a file.b'),
        
        ('file.a file.b file.c', '', ['.a .b .c'], 'file.a', 'file.a file.b file.c'),
        ('file.a file.b file.c', '', ['.a .b .c'], 'file.b', 'file.a file.b file.c'),
        ('file.a file.b file.c', '', ['.a .b .c'], 'file.c', 'file.a file.b file.c'),

        ('file.a file.b file.c file.d', '', ['.a .b', '.c .d'], 'file.a', 'file.a file.b'),
        ('file.a file.b file.c file.d', '', ['.a .b', '.c .d'], 'file.b', 'file.a file.b'),
        ('file.a file.b file.c file.d', '', ['.a .b', '.c .d'], 'file.c', 'file.c file.d'),
        ('file.a file.b file.c file.d', '', ['.a .b', '.c .d'], 'file.d', 'file.c file.d'), 

        # allowedExts != None - incomplete paths 
        # allowed, but must be unambiguous
        ('file.a',          '.a',     '',       'file',    'file.a'),
        ('file.a',          '.a',     '',       'file.a',  'file.a'),
        ('file.a  file.b',  '.a .b',  '',       'file.a',  'file.a'),
        ('file.a  file.b',  '.a .b',  '',       'file.b',  'file.b'),
        ('file1.a file2.b', '.a .b',  '',       'file1',   'file1.a'),
        ('file1.a file2.b', '.a .b',  '',       'file1.a', 'file1.a'),
        ('file1.a file2.b', '.a .b',  '',       'file2',   'file2.b'), 
        ('file1.a file2.b', '.a .b',  '',       'file2.b', 'file2.b'), 

        ('file.a file.b', '.a .b', ['.a .b'], 'file',   'file.a file.b'),
        ('file.a file.b', '.a .b', ['.a .b'], 'file.a', 'file.a file.b'),
        ('file.a file.b', '.a .b', ['.a .b'], 'file.b', 'file.a file.b'), 

        ('file.a file.b file.c', '.a .b .c', ['.a .b .c'],  'file',   'file.a file.b file.c'),
        ('file.a file.b file.c', '.a .b .c', ['.a .b .c'],  'file.a', 'file.a file.b file.c'),
        ('file.a file.b file.c', '.a .b .c', ['.a .b .c'],  'file.b', 'file.a file.b file.c'),
        ('file.a file.b file.c', '.a .b .c', ['.a .b .c'],  'file.c', 'file.a file.b file.c'),

        ('file.a  file.b  file.c  file.d',  '.a .b .c .d', ['.a .b', '.c .d'], 'file.a',  'file.a  file.b'),
        ('file.a  file.b  file.c  file.d',  '.a .b .c .d', ['.a .b', '.c .d'], 'file.b',  'file.a  file.b'),
        ('file.a  file.b  file.c  file.d',  '.a .b .c .d', ['.a .b', '.c .d'], 'file.c',  'file.c  file.d'),
        ('file.a  file.b  file.c  file.d',  '.a .b .c .d', ['.a .b', '.c .d'], 'file.d',  'file.c  file.d'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file1',   'file1.a file1.b'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file1.a', 'file1.a file1.b'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file1.b', 'file1.a file1.b'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file2',   'file2.c file2.d'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file2.c', 'file2.c file2.d'),
        ('file1.a file1.b file2.c file2.d', '.a .b .c .d', ['.a .b', '.c .d'], 'file2.d', 'file2.c file2.d'),

        # incomplete group should be ok when 
        # unambiguous = False (the default)
        ('file.a', '.a .b', ['.a .b'], 'file',   'file.a'),
        ('file.a', '.a .b', ['.a .b'], 'file.a', 'file.a'),


        # Unambiguous/complete group should 
        # be ok when unambiguous = True
        ('file.a file.b file.c', '.a .b .c', ['.a .b'], 'file.a', 'file.a file.b', True),
        ('file.a file.b file.c', '.a .b .c', ['.a .b'], 'file.b', 'file.a file.b', True),
        ('file.a file.b file.c', '.a .b .c', ['.a .b'], 'file.c', 'file.c',        True),
    ]


    workdir = tempfile.mkdtemp()

    try:
        for test  in tests:

            files_to_create = test[0]
            allowedExts     = test[1]
            fileGroups      = test[2]
            path            = test[3]
            files_to_expect = test[4]

            if len(test) == 6: unambiguous = test[5]
            else:              unambiguous = False
                

            files_to_create = files_to_create.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]
            files_to_expect = files_to_expect.split()

            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None

            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            print()
            print('files_to_create: ', files_to_create)
            print('path:            ', path)
            print('allowedExts:     ', allowedExts)
            print('fileGroups:      ', fileGroups)
            print('files_to_expect: ', files_to_expect)

            fullPaths = fslpath.getFileGroup(
                op.join(workdir, path),
                allowedExts=allowedExts,
                fileGroups=fileGroups,
                fullPaths=True,
                unambiguous=unambiguous)
            exts = fslpath.getFileGroup(
                op.join(workdir, path),
                allowedExts=allowedExts,
                fileGroups=fileGroups,
                fullPaths=False,
                unambiguous=unambiguous)

            assert sorted(fullPaths) == sorted([op.join(workdir, e)            for e in files_to_expect])
            assert sorted(exts)      == sorted([fslpath.getExt(e, allowedExts) for e in files_to_expect])

            cleardir(workdir)

    finally:
        shutil.rmtree(workdir)


def test_getFileGroup_shouldFail():

    # All of these tests should raise an error

    allowedExts = ' '.join(fslimage.ALLOWED_EXTENSIONS)
    fileGroups  = [' '.join(g) for g in fslimage.FILE_GROUPS]

    # (files_to_create, path, allowedExts, fileGroups[, unambiguous])
    tests = [

        # Unsupported extension
        ('file.a', 'file.a', '.b', []),
        
        # Incomplete path, and allowedExts is None
        ('file.a', 'file', '', []),
        
        # non existent path
        ('file.a', 'file.b', '.a', []),
        
        # ambigiuous
        ('file.a file.b file.c file.d', 'file', '.a .b .c .d', ['.a .b', '.c .d']),

        # Incomplete group, when unambiguous is set to True
        ('file.a', 'file',   '.a .b', ['.a .b'], True),
        ('file.a', 'file.a', '.a .b', ['.a .b'], True),

        ('file.hdr', 'file',     allowedExts, fileGroups, True),
        ('file.hdr', 'file.hdr', allowedExts, fileGroups, True),
        ('file.img', 'file',     allowedExts, fileGroups, True),
        ('file.img', 'file.img', allowedExts, fileGroups, True),

        # Part of more than one group, when unambiguous is True
        ('file.a file.b file.c', 'file.a', '.a .b', ['.a .b', '.a .c'], True),
    ]
    
    workdir = tempfile.mkdtemp()

    try:
        for test in tests:

            files_to_create = test[0]
            path            = test[1]
            allowedExts     = test[2]
            fileGroups      = test[3]

            if len(test) > 4: unambiguous = test[4]
            else:             unambiguous = False

            files_to_create = files_to_create.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]

            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None

            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            print()
            print('files_to_create: ', files_to_create)
            print('path:            ', path)
            print('allowedExts:     ', allowedExts)
            print('fileGroups:      ', fileGroups)

            with pytest.raises(fslpath.PathError):
                fullPaths = fslpath.getFileGroup(
                    op.join(workdir, path),
                    allowedExts=allowedExts,
                    fileGroups=fileGroups,
                    fullPaths=True,
                    unambiguous=unambiguous)

                print('fullPaths:       ', fullPaths)

            with pytest.raises(fslpath.PathError):
                exts = fslpath.getFileGroup(
                    op.join(workdir, path),
                    allowedExts=allowedExts,
                    fileGroups=fileGroups,
                    fullPaths=False,
                    unambiguous=unambiguous)
                
                print('exts:            ', exts)

            cleardir(workdir)

    finally:
        shutil.rmtree(workdir)



def test_removeDuplicates_imageFiles_shouldPass():

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    groups      = fslimage.FILE_GROUPS 

    # [(files_to_create,
    #    [(paths, expected),
    #     ...
    #    ]),
    #  ...
    # ]
    allTests = [
        ('file.hdr file.img', [
            ('file',              'file.img'),
            ('file     file',     'file.img'),
            ('file     file.hdr', 'file.img'),
            ('file     file.img', 'file.img'),
            ('file.hdr file',     'file.img'),
            ('file.hdr file.hdr', 'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.img file',     'file.img'),
            ('file.img file.hdr', 'file.img'),
            ('file.img file.img', 'file.img'), 
            ('file.hdr',          'file.img'),
            ('file.img',          'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.img file.hdr', 'file.img'),
        ]),

        ('file.hdr file.img file.blob', [
            ('file',              'file.img'),
            ('file.hdr',          'file.img'),
            ('file.img',          'file.img'),
            ('file.hdr file.img', 'file.img'),
            ('file.img file.hdr', 'file.img'),
        ]),


        ('file.hdr file.img file.nii', [
            ('file.hdr',                   'file.img'),
            ('file.img',                   'file.img'),
            ('file.hdr file.nii',          'file.img file.nii'),
            ('file.img file.nii',          'file.img file.nii'), 
            ('file.hdr file.img',          'file.img'),
            ('file.img file.hdr',          'file.img'),
            ('file.img file.hdr',          'file.img'),
            ('file.hdr file.img file.nii', 'file.img file.nii'),
            ('file.img file.hdr file.nii', 'file.img file.nii'),
            ('file.img file.hdr file.nii', 'file.img file.nii'), 
        ]),        
                

        ('001.hdr 001.img 002.hdr 002.img 003.hdr 003.img', [
            ('001     002     003',                             '001.img 002.img 003.img'), 
            ('001.hdr 002.hdr 003.hdr',                         '001.img 002.img 003.img'),
            ('001.img 002.img 003.img',                         '001.img 002.img 003.img'),
            ('001.hdr 001.img 002.hdr 002.img 003.img',         '001.img 002.img 003.img'), 
            ('001.hdr 001.img 002.hdr 002.img 003.hdr 003.img', '001.img 002.img 003.img'),
            ('001.img 001.hdr 002.img 002.hdr 003.img 003.hdr', '001.img 002.img 003.img'), 
        ])
    ]

    workdir = tempfile.mkdtemp()

    try:
        for files_to_create, tests in allTests:

            files_to_create = files_to_create.split()
            
            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            for paths, expected in tests:

                paths    = paths.split()
                expected = expected.split()
                
                print()
                print('files_to_create: ', files_to_create)
                print('paths:           ', paths)
                print('expected:        ', expected)
                  
                paths  = [op.join(workdir, p) for p in paths]
                result = fslpath.removeDuplicates(paths, allowedExts, groups)

                print('result:   ', result)

                assert result == [op.join(workdir, e) for e in expected]

            cleardir(workdir)
                    
    finally:
        shutil.rmtree(workdir)

    
    
def test_removeDuplicates_otherFiles_shouldPass():
    
    # files_to_create, paths, allowedExts, fileGroups, expected
    tests = [
        
        # allowedExts is None, but paths are unambiguouos
        ('file.a file.b', 'file.a file.b', '', [], 'file.a file.b'),

        # Retured path should be the first in the group
        ('file.a file.b', 'file.a file.b', '', ['.a .b'], 'file.a'),
        ('file.a file.b', 'file.a file.b', '', ['.b .a'], 'file.b'),
        
        ('file.a file.b file.c', 'file.a file.b file.c',      '', ['.a .b'], 'file.a file.c'),
        ('file.a file.b file.c', 'file.a file.b file.c',      '', ['.b .a'], 'file.b file.c'),
        
        ('file.a file.b file.c', 'file.a file.b file.c',      '', ['.a .b .c'], 'file.a'),
        ('file.a file.b file.c', 'file.a file.b file.c',      '', ['.a .b .c'], 'file.a'),
        ('file.a file.b file.c', 'file.a file.b file.c',      '', ['.a .b .c'], 'file.a'),

        ('file.a  file.b  file.c  file.d',  'file.a  file.b  file.c  file.d',  '', ['.a .b', '.c .d'], 'file.a  file.c'),
        ('file1.a file1.b file2.a file2.b', 'file1.a file1.b file2.a file2.b', '', ['.a .b'],          'file1.a file2.a'),
        
        # Incomplete paths (but are unambiguouos because of allowedExts)
        ('file.a'       , 'file',   '.a', [], 'file.a'), 
        ('file.a'       , 'file.a', '.a', [], 'file.a'),
        
        ('file.a file.b', 'file.a',             '.a',    [],        'file.a'),
        ('file.a file.b', 'file.a file.b',      '.a .b', [],        'file.a file.b'),
        ('file.a file.b', 'file',               '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b', 'file file',          '.a .b', ['.a .b'], 'file.a'),
        ('file.a file.b', 'file file.a file.b', '.a .b', ['.a .b'], 'file.a'),

        ('file1.a file1.b file2.a file2.b', 'file1   file1.a file2   file2.a', '.a .b', ['.a .b'], 'file1.a file2.a'),
        ('file1.a file1.b file2.a file2.b', 'file1           file2',           '.a .b', ['.a .b'], 'file1.a file2.a'),
        ('file1.a file1.b file2.a file2.b', 'file1   file1.a file2',           '.a .b', ['.a .b'], 'file1.a file2.a'),
    ]


    workdir = tempfile.mkdtemp()


    try:
        for files_to_create, paths, allowedExts, fileGroups, expected in tests:

            files_to_create = files_to_create.split()
            paths           = paths.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]
            expected        = expected.split()

            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None

            for f in files_to_create:
                make_dummy_file(op.join(workdir, f))

            print('files_to_create: {}'.format(files_to_create))
            print('paths:           {}'.format(paths))
            print('allowedExts:     {}'.format(allowedExts))
            print('fileGroups:      {}'.format(fileGroups))
            print('workdir:         {}'.format(os.listdir(workdir)))
            print('expected:        {}'.format(expected))
 
            result = fslpath.removeDuplicates([op.join(workdir, p) for p in paths],
                                              allowedExts=allowedExts,
                                              fileGroups=fileGroups)

            print('result:          {}'.format(result))

            assert result == [op.join(workdir, e) for e in expected]

            cleardir(workdir)

    finally:
        shutil.rmtree(workdir)


def test_removeDuplicates_shouldFail():

    # (files_to_create, paths, allowedExts, fileGroups)
    tests = [
        # Invalid path(s)
        ('',       'file.a',        '',      []),
        ('file.a', 'file.b',        '',      []),
        ('file.a', 'file.b file.c', '',      []),
        ('file.a', 'file',          '',      []),
        ('file.a', 'file.b',        '.a .b', ['.a .b']),

        # Unsupported extension
        ('file.a', 'file.a', '.b', []),

        # Ambiguous
        ('file.a file.b',        'file',        '.a .b',    []),
        ('file.a file.b file.c', 'file file.c', '.a .b .c', ['.a .b']),
    ]

    workdir = tempfile.mkdtemp()


    try:
        for files_to_create, path, allowedExts, fileGroups in tests:

            cleardir(workdir)

            files_to_create = files_to_create.split()
            allowedExts     = allowedExts.split()
            fileGroups      = [g.split() for g in fileGroups]

            if len(allowedExts) == 0: allowedExts = None
            if len(fileGroups)  == 0: fileGroups  = None

            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            print()
            print('files_to_create: ', files_to_create)
            print('path:            ', path)
            print('allowedExts:     ', allowedExts)
            print('fileGroups:      ', fileGroups)

            with pytest.raises(fslpath.PathError):
                result = fslpath.removeDuplicates(path,
                                                  allowedExts=allowedExts,
                                                  fileGroups=fileGroups)
                print('result:          ', result) 
    
    finally:
        shutil.rmtree(workdir)


def test_uniquePrefix():

    contents = """
    100307.32k_fs_LR.wb.spec
    100307.ArealDistortion_FS.32k_fs_LR.dscalar.nii
    100307.ArealDistortion_MSMSulc.32k_fs_LR.dscalar.nii
    100307.BA.32k_fs_LR.dlabel.nii
    100307.L.ArealDistortion_FS.32k_fs_LR.shape.gii
    100307.L.ArealDistortion_MSMSulc.32k_fs_LR.shape.gii
    100307.L.BA.32k_fs_LR.label.gii
    100307.L.MyelinMap.32k_fs_LR.func.gii
    100307.L.MyelinMap_BC.32k_fs_LR.func.gii
    100307.L.SmoothedMyelinMap.32k_fs_LR.func.gii
    100307.L.SmoothedMyelinMap_BC.32k_fs_LR.func.gii
    100307.L.aparc.32k_fs_LR.label.gii
    100307.L.aparc.a2009s.32k_fs_LR.label.gii
    100307.L.atlasroi.32k_fs_LR.shape.gii
    100307.L.corrThickness.32k_fs_LR.shape.gii
    100307.L.curvature.32k_fs_LR.shape.gii
    100307.L.flat.32k_fs_LR.surf.gii
    100307.L.inflated.32k_fs_LR.surf.gii
    100307.L.midthickness.32k_fs_LR.surf.gii
    100307.L.pial.32k_fs_LR.surf.gii
    100307.L.sphere.32k_fs_LR.surf.gii
    100307.L.sulc.32k_fs_LR.shape.gii
    100307.L.thickness.32k_fs_LR.shape.gii
    100307.L.very_inflated.32k_fs_LR.surf.gii
    100307.L.white.32k_fs_LR.surf.gii
    100307.MyelinMap.32k_fs_LR.dscalar.nii
    100307.MyelinMap_BC.32k_fs_LR.dscalar.nii
    100307.R.ArealDistortion_FS.32k_fs_LR.shape.gii
    100307.R.ArealDistortion_MSMSulc.32k_fs_LR.shape.gii
    100307.R.BA.32k_fs_LR.label.gii
    100307.R.MyelinMap.32k_fs_LR.func.gii
    100307.R.MyelinMap_BC.32k_fs_LR.func.gii
    100307.R.SmoothedMyelinMap.32k_fs_LR.func.gii
    100307.R.SmoothedMyelinMap_BC.32k_fs_LR.func.gii
    100307.R.aparc.32k_fs_LR.label.gii
    100307.R.aparc.a2009s.32k_fs_LR.label.gii
    100307.R.atlasroi.32k_fs_LR.shape.gii
    100307.R.corrThickness.32k_fs_LR.shape.gii
    100307.R.curvature.32k_fs_LR.shape.gii
    100307.R.flat.32k_fs_LR.surf.gii
    100307.R.inflated.32k_fs_LR.surf.gii
    100307.R.midthickness.32k_fs_LR.surf.gii
    100307.R.pial.32k_fs_LR.surf.gii
    100307.R.sphere.32k_fs_LR.surf.gii
    100307.R.sulc.32k_fs_LR.shape.gii
    100307.R.thickness.32k_fs_LR.shape.gii
    100307.R.very_inflated.32k_fs_LR.surf.gii
    100307.R.white.32k_fs_LR.surf.gii
    100307.SmoothedMyelinMap.32k_fs_LR.dscalar.nii
    100307.SmoothedMyelinMap_BC.32k_fs_LR.dscalar.nii
    100307.aparc.32k_fs_LR.dlabel.nii
    100307.aparc.a2009s.32k_fs_LR.dlabel.nii
    100307.corrThickness.32k_fs_LR.dscalar.nii
    100307.curvature.32k_fs_LR.dscalar.nii
    100307.sulc.32k_fs_LR.dscalar.nii
    100307.thickness.32k_fs_LR.dscalar.nii 
    """.split()

    # (filename, expected_result)
    tests = [
        ('100307.32k_fs_LR.wb.spec',                        '100307.3'),
        ('100307.ArealDistortion_FS.32k_fs_LR.dscalar.nii', '100307.ArealDistortion_F'),
        ('100307.L.ArealDistortion_FS.32k_fs_LR.shape.gii', '100307.L.ArealDistortion_F'),
        ('100307.L.flat.32k_fs_LR.surf.gii',                '100307.L.f'),
        ('100307.R.flat.32k_fs_LR.surf.gii',                '100307.R.f'),
        ('100307.MyelinMap.32k_fs_LR.dscalar.nii',          '100307.MyelinMap.'),
        ('100307.SmoothedMyelinMap.32k_fs_LR.dscalar.nii',  '100307.SmoothedMyelinMap.'),
        ('100307.sulc.32k_fs_LR.dscalar.nii',               '100307.s'),
    ]
    
    workdir = tempfile.mkdtemp()

    try:
        for fname in contents:
            with open(op.join(workdir, fname), 'wt') as f:
                f.write(fname)

        for filename, expected in tests:

            expected = op.join(workdir, expected)
            result   = fslpath.uniquePrefix(op.join(workdir, filename))

            assert result == expected

    finally:
        shutil.rmtree(workdir)
