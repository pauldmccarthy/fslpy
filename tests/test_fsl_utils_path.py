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


def test_addExt_exists_shouldPass(testdir):
    """Tests the addExt function where the path exists, and the inputs
    are valid.
    """

    groups       = fslimage.FILE_GROUPS
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
                              fileGroups=groups) == output


def test_addExt_exists_shouldFail(testdir):
    """Tests the addExt function with inputs that should cause it to raise an
    error.
    """
    
    groups      = fslimage.FILE_GROUPS
    allowedExts = fslimage.ALLOWED_EXTENSIONS

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
        group   = groups

        if len(test) >= 2:
            if not (test[1] == False):
                allowed = test[1]

        if len(test) == 3:
            if not (test[2] == False):
                group = test[2]

        with pytest.raises(fslpath.PathError):
            
            fslpath.addExt(prefix,
                           allowed,
                           mustExist=True,
                           fileGroups=group)


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


def test_removeDuplicates():

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    groups      = fslimage.FILE_GROUPS 

    # [(files_to_create,
    #    [([paths], [expected]),
    #     ...
    #    ]),
    #  ...
    # ]
    allTests = [
        (['file.hdr', 'file.img'], [
            (['file'],                 ['file']),
            (['file.hdr'],             ['file.hdr']),
            (['file.img'],             ['file.img']),
            (['file.hdr', 'file.img'], ['file.hdr']),
            (['file.img', 'file.hdr'], ['file.img']),
        ]),

        (['file.hdr', 'file.img', 'file.blob'], [
            (['file'],                 ['file']),
            (['file.hdr'],             ['file.hdr']),
            (['file.img'],             ['file.img']),
            (['file.hdr', 'file.img'], ['file.hdr']),
            (['file.img', 'file.hdr'], ['file.img']),
        ]),


        (['file.hdr', 'file.img', 'file.nii'], [
            (['file'],                 ['file']),
            (['file.hdr'],             ['file.hdr']),
            (['file.img'],             ['file.img']),
            (['file.hdr', 'file.img'], ['file.hdr']),
            (['file.img', 'file.hdr'], ['file.img']), 
        ]),        
                

        (['001.hdr', '001.img', '002.hdr', '002.img', '003.hdr', '003.img'], [
            (['001', '002', '003'],
             ['001', '002', '003']), 
            
            (['001.hdr', '002.hdr', '003.hdr'],
             ['001.hdr', '002.hdr', '003.hdr']),
            (['001.img', '002.img', '003.img'],
             ['001.img', '002.img', '003.img']),

            (['001.hdr', '001.img', '002.hdr', '002.img', '003.img'],
             ['001.hdr', '002.hdr', '003.img']), 
            (['001.hdr', '001.img', '002.hdr', '002.img', '003.hdr', '003.img'],
             ['001.hdr', '002.hdr', '003.hdr']),
            (['001.img', '001.hdr', '002.img', '002.hdr', '003.img', '003.hdr'],
             ['001.img', '002.img', '003.img']), 
        ])
    ]

    workdir = tempfile.mkdtemp()

    try:
        for files_to_create, tests in allTests:
            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            for paths, expected in tests:

                paths  = [op.join(workdir, p) for p in paths]
                result = fslpath.removeDuplicates(paths, allowedExts, groups)

                assert result == [op.join(workdir, e) for e in expected]

            for f in files_to_create:
                os.remove(op.join(workdir, f))
                    
    finally:
        shutil.rmtree(workdir)



def test_getFileGroup():

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    groups      = fslimage.FILE_GROUPS

    # (files_to_create,
    #   [(path, expected),
    #    ...
    #   ]
    # )
    #
    # expected == 'all' is equivalent to expected == files_to_create
    allTests = [
        (['file.hdr', 'file.img'], [
            ('file.hdr', 'all'),
            ('file.img', 'all')]),

        (['file.hdr.gz', 'file.img.gz'], [
            ('file.hdr.gz', 'all'),
            ('file.img.gz', 'all')]), 

        (['file.hdr', 'file.img', 'file.nii'], [
            ('file.hdr', ['file.hdr', 'file.img']),
            ('file.img', ['file.hdr', 'file.img'])]), 
        
        (['file.hdr', 'file.img', 'file.blob'], [
            ('file.hdr', ['file.hdr', 'file.img']),
            ('file.img', ['file.hdr', 'file.img'])]),


        (['file.hdr'], [
            ('file.hdr', ['file.hdr']),
            ('file.img', ['file.img'])]),

        (['file.img'], [
            ('file.hdr', ['file.hdr']),
            ('file.img', ['file.img'])]), 
    ]

    workdir = tempfile.mkdtemp()

    try: 

        for files_to_create, tests in allTests:

            for fn in files_to_create:
                with open(op.join(workdir, fn), 'wt') as f:
                    f.write('{}\n'.format(fn))

            for path, expected in tests:
                if expected == 'all':
                    expected = list(files_to_create)


                fullPaths = fslpath.getFileGroup(
                    op.join(workdir, path),
                    allowedExts=allowedExts,
                    fileGroups=groups,
                    fullPaths=True)
                exts = fslpath.getFileGroup(
                    op.join(workdir, path),
                    allowedExts=allowedExts,
                    fileGroups=groups,
                    fullPaths=False)

                assert sorted(fullPaths) == sorted([op.join(workdir, e)            for e in expected])
                assert sorted(exts)      == sorted([fslpath.getExt(e, allowedExts) for e in expected])

            for f in files_to_create:
                try:    os.remove(op.join(workdir,  f))
                except: pass 

    finally:
        shutil.rmtree(workdir)


def test_imcp_shouldPass(move=False):

    allowedExts = fslimage.ALLOWED_EXTENSIONS
    groups      = fslimage.FILE_GROUPS
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
                for fn in files_to_create:
                    with open(op.join(indir, fn), 'wt') as f:
                        f.write('{}\n'.format(fn))

                for src in imcp_src:

                    src = op.join(indir, src)
                    
                    if move: fslpath.immv(src, imcp_dest, allowedExts=allowedExts, fileGroups=groups, overwrite=True)
                    else:    fslpath.imcp(src, imcp_dest, allowedExts=allowedExts, fileGroups=groups, overwrite=True)

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
