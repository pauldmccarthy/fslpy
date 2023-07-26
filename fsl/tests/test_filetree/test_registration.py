from fsl.utils.filetree import register_tree, FileTree
import os.path as op


class SubFileTree(FileTree):
    pass


def test_register_parent():
    directory = op.split(__file__)[0]
    filename = op.join(directory, 'parent.tree')

    # call from sub-type
    tree = SubFileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)

    # call from FileTree
    tree = FileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert not isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)

    # register + call from FileTree
    register_tree('parent', SubFileTree)
    tree = FileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)

    # register + call from SubFileTree
    register_tree('parent', FileTree)
    tree = SubFileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert not isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)


def test_children():
    directory = op.split(__file__)[0]
    filename = op.join(directory, 'parent.tree')

    tree = SubFileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert not isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)

    register_tree('eddy', SubFileTree)
    tree = SubFileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert not isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert isinstance(child, SubFileTree)

    register_tree('eddy', FileTree)
    tree = SubFileTree.read(filename)
    assert isinstance(tree, FileTree)
    assert not isinstance(tree, SubFileTree)
    for child in tree.sub_trees.values():
        assert isinstance(child, FileTree)
        assert not isinstance(child, SubFileTree)
