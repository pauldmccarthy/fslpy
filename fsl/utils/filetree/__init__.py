"""
Easy format to define input/output files in a python pipeline.

The goal is to separate the definition of the input/output filenames from the actual code
by defining a directory tree (i.e., FileTree) in a separate file from the code.

Loading FileTrees
-----------------
.. code-block:: python

    from fsl.utils.filetree import FileTree, tree_directories
    tree = FileTree.read('bids_raw')

This creates a `tree` object that describes input/output filenames
for your pipeline based on `this file <trees/bids_raw.tree>`

:py:func:`filetree.FileTree.read` will search through the `filetree.tree_directories` list of directories
for any FileTrees matching the given name. This list by default includes the current directory. Of course,
a full path to the requested FileTree can also be provided. This includes all FileTrees defined
`here <https://git.fmrib.ox.ac.uk/fsl/fslpy/tree/master/fsl/utils/filetree/trees>`_.

FileTree format
---------------
The FileTrees are defined in a simple to type format, where indendation is used to indicate subdirectories, for example:

::

    parent
        file1.txt
        child
            file2
        file3.txt
    file4.txt

In the top-level directory this represents one file ("file4.txt") and one directory ("parent"). The directory
contains two files ("file1.txt" and "file3.txt") and one directory ("child") which contains a single file ("file2").

Individual aspects of this format are defined in more detail below.

Short names
^^^^^^^^^^^
Each directory and file in the FileTree is assigned a short name for convenient access.
For example, for the FileTree

::

    parent
        file1.txt
        child
            file2
        file3.txt
    file4.txt

We can load this FileTree using

.. code-block:: python

    >>> tree = FileTree.read(<tree filename>)
    >>> tree.get('file2')
    'parent/child/file2'
    >>> tree.get('child')
    'parent/child'

These filenames will be returned whether the underlying file exists or not (see :py:func:`filetree.FileTree.get`).

By default the short name will be the name of the file or directory without extension (i.e., everything the first dot).
The short name can be explicitly set by including it in round brackets behind the filename,
so ``left_hippocampus_segment_from_first.nii.gz (Lhipp)`` will have the short name "Lhipp"
rather than "left_hippocampus_segment_from_first"). This allows changing of the filenames
without having to alter the short names used to refer to those filenames in the code.

Variables
^^^^^^^^^
FileTrees can have placeholders for variables such as subject id:

::

    {subject}
        T1w.nii.gz
        {hemi}_pial.surf.gii (pial)

Any part of the directory or file names contained within curly brackets will have to be filled when getting the path:

.. code-block:: python

    >>> tree = FileTree.read(<tree filename>, subject='A')
    >>> tree.get('T1w')
    'A/T1w.nii.gz
    >>> B_tree = tree.update(subject='B')
    >>> B_tree.get('T1w')
    'B/T1w.nii.gz
    >>> tree.get('pial')  # note that pial was explicitly set as the short name in the file above
    # Raises a MissingVariable error as the hemi variable is not defined

Variables can be either set during initialisation of the FileTree or by :py:func:`filetree.FileTree.update`, which
returns a new `FileTree` rather than updating the existing one.

Finally initial values for the variables can be set in the FileTree itself, for example in

::

    hemi = left

    {subject}
        T1w.nii.gz
        {hemi}_pial.surf.gii (pial)

the variable "hemi" will be "left" unless explicitly set during initialisation or updating of the `FileTree`.

Optional Variables
^^^^^^^^^^^^^^^^^^
Normally having undefined variables will lead to :py:exc:`filetree.MissingVariable` being raised.
This can be avoided by putting these variables in square brackets, indicating that they can simply
be skipped. For example for the FileTree:

::

    {subject}
        [{session}]
            T1w[_{session}].nii.gz (T1w)

.. code-block:: python

    >>> tree = FileTree.read(<tree filename>, subject='A')
    >>> tree.get('T1w')
    'A/T1w.nii.gz'
    >>> tree.update(session='test').get('T1w')
    'A/test/T1w_test.nii.gz'

Note that if any variable within the square brackets is missing, any text within those square brackets is omitted.

Extensive use of optional variables can be found in the
`FileTree of the BIDS raw data format <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/bids_raw.tree>`_.

Sub-trees
^^^^^^^^^
FileTrees can include other FileTrees within their directory structure. For example,

::

    {subject}
        topup
            b0.nii.gz
            ->topup basename=out (topup)
        eddy
            ->eddy (eddy)
            nodif_brain_mask.nii.gz
        Diffusion
            ->Diffusion (diff)
            ->dti (dti)

which might represent a diffusion MRI pipeline, which contains references to the predefined trees for the
`topup <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/topup.tree>`_,
`eddy <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/eddy.tree>`_,
`Diffusion <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/Diffusion.tree>`_, and
`dti <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/dti.tree>`_
FileTrees describing the input/output of various FSL tools.

The general format of this is:
``-><tree name> [<variable in sub-tree>=<value>, ...] (<sub-tree short name)``

The filenames defined in the sub-trees can be accessed using a "/" in the short name:

.. code-block:: python

    >>> tree = FileTree.read(<tree filename>, subject='A')
    >>> tree.get('dti/FA')
    'A/Diffusion/dti_FA.nii.gz'
    >>> tree.get('topup/fieldcoef')
    'A/topup/out_fielcoef.nii.gz

Extensive use of sub-trees can be found in
`the FileTree of the HCP pre-processed directory structure <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/HCP_directory.tree>`_,
which amongst others refers to
`the HCP surface directory format FileTree <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/HCP_Surface.tree>`_.
"""

__author__ = 'Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>'

from .filetree import FileTree, register_tree, MissingVariable
from .parse import tree_directories
