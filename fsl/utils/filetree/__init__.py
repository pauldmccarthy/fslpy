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

    # Any text following a #-character can be used for comments
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

Example pipeline
----------------
A very simple pipeline to run BET on every subject can start with a FileTree like
::

    {subject}
        T1w.nii.gz
        T1w_brain.nii.gz (bet_output)
        T1w_brain_mask.nii.gz (bet_mask)


Assuming that the input T1w's already exist, we can then simply run BET for every subject using:

.. code-block:: python

    from fsl.utils.filetree import FileTree
    from fsl.wrappers.bet import bet
    tree = FileTree.read(<tree filename>)

    # Iterates over set of variables that correspond to each T1-weighted image file matching the template
    for T1w_tree in tree.get_all_trees('T1w', glob_vars='all'):
        # get retrieves the filenames based on the current set of variables
        # make_dir=True ensures that the output directory containing the "bet_output" actually exists
        bet(input=T1w_tree.get('T1w'), output=T1w_tree.get('bet_output', make_dir=True), mask=True)

Useful tips
-----------

Changing directory structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If later on in our input files change, because for some subjects we added a second session, we could keep our script
and simply update the FileTree:
::

    {subject}
        [ses-{session}]
            T1w.nii.gz
            T1w_brain.nii.gz (bet_output)
            T1w_brain_mask.nii.gz (bet_mask)

Note the square brackets around the session sub-directory. This indicates that this sub-directory is optional and
will only be present if the "session" variable is defined (see `Optional variables`_).

This means that with the script run with this updated tree will run bet on each T1-weighted image even for a directory
structure like:
::

    subjectA/
        T1w.nii.gz
    subjectB/
        ses-01/
            T1w.nii.gz
        ses-02/
            T1w.nii.gz

If we get told off that our script is writing the output to the same directory as our input data,
altering this behaviour is again as simple as altering the FileTree to something like:
::

    raw_data
        {subject} (input_subject_dir)
            [ses-{session}] (input_session_dir)
                T1w.nii.gz
    processed_data
        {subject} (output_subject_dir)
            [ses-{session}] (output_session_dir)
                bet
                    {subject}[_{session}]_T1w_brain.nii.gz (bet_output)
                    {subject}[_{session}]_T1w_brain_mask.nii.gz (bet_mask)

Note that we also encoded the subject and session ID in the output filename.
We also have to explicitly assign short names to the subject and session directories,
even though we don't explicitly reference these in the script.
The reason for this is that each directory and filename template must have a unique short name and
in this case the default short names (respectively, "{subject}" and "[ses-{session}]") would not have been unique.

Output "basenames"
^^^^^^^^^^^^^^^^^^

Some tools like FSL's FAST produce many output files. Rather than entering all
of these files in our FileTree by hand you can include them all at once by including `Sub-trees`_:

::

    raw_data
        {subject} (input_subject_dir)
            [ses-{session}] (input_session_dir)
                T1w.nii.gz
    processed_data
        {subject} (output_subject_dir)
            [ses-{session}] (output_session_dir)
                bet
                    {subject}[_{session}]_T1w_brain.nii.gz (bet_output)
                    {subject}[_{session}]_T1w_brain_mask.nii.gz (bet_mask)
                fast
                    ->fast basename={subject}[_{session}] (segment)

Here we chose to set the "basename" of the FAST output to a combination of the subject and if available session ID.

Within the script we can generate the fast output by running

.. code-block:: python

    from fsl.wrappers.fast import fast
    fast(imgs=[T1w_tree.get('T1w')], out=T1w_tree.get('segment/basename'))

The output files will be available as `T1w_tree.get('segment/<variable name>')`, where `<variable name>` is one
of the short variable names defined in the
`FAST FileTree <https://git.fmrib.ox.ac.uk/fsl/fslpy/blob/master/fsl/utils/filetree/trees/fast.tree>`_.

Running a pipeline on a subset of participants/sessions/runs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Suppose you want to run your pipeline on a subset of your data while testing. 
You may want to do this if your data has a a hierarchy of variables (e.g. participant, session, run) as in the example below.

::

    sub-001
        ses-01
            sub-001_ses-01_run-1.feat
            sub-001_ses-01_run-2.feat
        ses-02
            sub-{participant}_ses-{session}_run-{run}.feat (feat_dir)
            ...
    sub-002
    sub-003
    ...

You can update the FileTree with one or more variables before calling `get_all_trees` as follows:

.. code-block:: python

    for participant in ("001", "002"):
        for t in tree.update(participant=participant, run="1").get_all_trees("feat_dir", glob_vars="all"):
            my_pipeline(t)

This code will iterate over all sessions that have a run="1" for participants "001" and "002".
"""

__author__ = 'Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>'

from .filetree import FileTree, register_tree, MissingVariable
from .parse import tree_directories, list_all_trees
from .query import FileTreeQuery
