# Sample Test passing with nose and pytest
from fsl.utils import filetree
from pathlib import PurePath
import os.path as op
import pytest
from glob import glob


def same_path(p1, p2):
    assert PurePath(p1) == PurePath(p2)


def test_simple_tree():
    tree = filetree.FileTree.read('eddy')
    assert tree.variables['basename'] == 'eddy_output'
    same_path(tree.get('basename'), './eddy_output')
    same_path(tree.get('image'), './eddy_output.nii.gz')

    tree = filetree.FileTree.read('eddy.tree', basename='out')
    same_path(tree.get('basename'), './out')
    same_path(tree.update(basename='test').get('basename'), './test')
    same_path(tree.get('basename'), './out')

    with pytest.raises(ValueError):
        filetree.FileTree.read('non_existing')


def test_complicated_tree():
    tree = filetree.FileTree.read('HCP_directory').update(subject='100307')

    same_path(tree.get('T1w_acpc_dc'), '100307/T1w/T1w_acpc_dc.nii.gz')

    L_white = '100307/T1w/fsaverage_LR32k/100307.L.white.32k_fs_LR.surf.gii'
    same_path(tree.update(hemi='L').get('T1w_32k/white'), L_white)
    same_path(tree.sub_trees['T1w_32k'].update(hemi='L').get('white'), L_white)

    assert tree.defines(('T1w_32k/white', ))
    assert tree.defines('T1w_32k/white')
    assert not tree.defines(('T1w_32k/white_misspelled', ))
    assert not tree.defines(('T1w_32k/white', 'T1w_32k/white_misspelled', ))
    assert not tree.defines(('T1w_32k_err/white', ))
    assert not tree.defines(('../test'))
    with pytest.raises(ValueError):
        assert not tree.defines(('../test'), error=True)
    with pytest.raises(ValueError):
        tree.defines(('T1w_32k_err/white', ), error=True)
    assert tree.defines(('T1w_32k/white', ), error=True)


def test_parent_tree():
    directory = op.split(__file__)[0]
    tree = filetree.FileTree.read(op.join(directory, 'parent.tree'))
    same_path(tree.get('sub0/basename'), '0')
    same_path(tree.get('sub1/basename'), 'dir1/1')
    same_path(tree.get('sub1b/basename'), 'dir1/1b')
    same_path(tree.get('sub2/basename'), 'dir1/dir2/2')
    same_path(tree.update(subvar='grot').get('subvar/basename'), 'subvar_grot')
    with pytest.raises(KeyError):
        tree.get('sub_var/basename')

    # test updating in parent tree
    sub0_tree = tree.sub_trees['sub0']
    same_path(sub0_tree.update(subvar='test').get('../subvar/basename'), 'subvar_test')
    with pytest.raises(KeyError):
        sub0_tree.update(subvar='test', set_parent=False).get('../subvar/basename')

    sub0_tree = tree.update(subvar='grot').sub_trees['sub0']
    same_path(sub0_tree.update(subvar='test').get('../subvar/basename'), 'subvar_test')
    same_path(sub0_tree.update(subvar='test', set_parent=False).get('../subvar/basename'), 'subvar_grot')
    same_path(sub0_tree.get('../subvar/basename'), 'subvar_grot')


def test_custom_tree():
    directory = op.split(__file__)[0]
    tree = filetree.FileTree.read(op.join(directory, 'custom.tree'), directory=directory)
    same_path(tree.get('sub_file'), op.join(directory, 'parent/sub_file.nii.gz'))
    same_path(tree.update(opt='test').get('sub_file'), op.join(directory, 'parent/opt_layer_test/sub_file.nii.gz'))

    with pytest.raises(KeyError):
        tree.get('opt_file')
    same_path(tree.update(opt='test').get('opt_file'), op.join(directory, 'parent/opt_layer_test/opt_file_test.nii.gz'))

    assert len(tree.update(opt='test').get_all('sub_file')) == 1
    assert len(tree.update(opt='test').get_all_vars('sub_file')) == 1
    assert len(tree.update(opt='test2').get_all('sub_file')) == 0
    assert len(tree.update(opt='test2').get_all_vars('sub_file')) == 0
    assert len(tree.get_all('sub_file', glob_vars=['opt'])) == 2
    assert len(tree.get_all('sub_file', glob_vars='all')) == 2
    assert len(tree.get_all('sub_file')) == 1
    assert len(tree.update(opt=None).get_all('sub_file')) == 1
    assert len(tree.update(opt=None).get_all('sub_file', glob_vars=['opt'])) == 2
    assert len(tree.update(opt=None).get_all('sub_file', glob_vars='all')) == 2

    for fn, settings in zip(tree.get_all('sub_file', glob_vars='all'),
                            tree.get_all_vars('sub_file', glob_vars='all')):
        same_path(fn, tree.update(**settings).get('sub_file'))

    assert len(tree.update(opt='test2').get_all('opt_file')) == 0
    assert len(tree.update(opt='test').get_all('opt_file')) == 1
    with pytest.raises(KeyError):
        tree.get_all('opt_file')
    assert len(tree.get_all('opt_file', glob_vars=['opt'])) == 1

    for short_name in ('sub_file', 'opt_file'):
        for glob_vars in (['opt'], 'all'):
            assert tree.get_all(short_name, glob_vars) == tuple(stree.get(short_name) for stree in tree.get_all_trees(short_name, glob_vars))

    for vars in ({'opt': None}, {'opt': 'test'}):
        filename = tree.update(**vars).get('sub_file')
        assert vars == tree.extract_variables('sub_file', filename)
    assert {'opt': None} == tree.extract_variables('sub_file', tree.get('sub_file'))

    assert tree.on_disk(('sub_file', 'opt_file'), error=True, glob_vars=['opt'])
    assert tree.on_disk(('sub_file', 'opt_file'), glob_vars=['opt'])
    assert not tree.on_disk(('sub_file', 'opt_file'), error=False)
    with pytest.raises(KeyError):
        assert tree.on_disk(('sub_file', 'opt_file'), error=True)
    assert not tree.update(opt='test2').on_disk(('sub_file', 'opt_file'))
    with pytest.raises(IOError):
        tree.update(opt='test2').on_disk(('sub_file', 'opt_file'), error=True)

    assert tree.template_variables() == {'opt'}
    assert tree.template_variables(optional=False) == {'opt'}
    assert tree.template_variables(required=False) == set()
    assert tree.template_variables(required=False, optional=False) == set()

    assert tree.template_variables('sub_file') == {'opt'}
    assert tree.template_variables('sub_file', required=False) == {'opt'}
    assert tree.template_variables('sub_file', optional=False) == set()
    assert tree.template_variables('sub_file', optional=False, required=False) == set()

    assert tree.template_variables('opt_file') == {'opt'}
    assert tree.template_variables('opt_file', required=False) == set()
    assert tree.template_variables('opt_file', optional=False) == {'opt'}
    assert tree.template_variables('opt_file', optional=False, required=False) == set()


def test_format():
    directory = op.split(__file__)[0]
    tree = filetree.FileTree.read(op.join(directory, 'format.tree'), var=1.23)
    same_path(tree.get('int'), '1')
    same_path(tree.get('f1'), '1.2')
    same_path(tree.get('f2'), '1.23')


def test_read_all():
    for directory in filetree.tree_directories:
        if directory != '.':
            for filename in glob(op.join(directory, '*.tree')):
                filetree.FileTree.read(filename)


def test_extract_vars_but():
    """
    Reproduces a bug where the already provided variables are ignored
    """
    directory = op.split(__file__)[0]
    tree = filetree.FileTree.read(op.join(directory, 'extract_vars.tree'))
    fn = 'parent/opt_layer_test/opt_file_test.nii.gz'
    assert {'p1': 'opt_file', 'p2': 'test'} == tree.extract_variables('fn', fn)
    assert {'p1': 'opt_file', 'p2': 'test'} == tree.update(p1='opt_file').extract_variables('fn', fn)
    assert {'p1': 'opt', 'p2': 'file_test'} == tree.update(p1='opt').extract_variables('fn', fn)
    assert {'p1': 'opt_{p3}', 'p2': 'test', 'p3': 'file'} == tree.update(p1='opt_{p3}').extract_variables('fn', fn)
