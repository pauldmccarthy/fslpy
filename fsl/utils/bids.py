#!/usr/bin/env python
#
# bids.py - Simple BIDS metadata reader.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a few functions for working with BIDS data sets.

.. autosummary::
   :nosignatures:

   BIDSFile
   isBIDSDir
   inBIDSDir
   isBIDSFile
   loadMetadata

All of the other functions in this module should not be considered part of the
public API.


.. note::  The `pybids <https://bids-standard.github.io/pybids/>`_ library is
           a more suitable choice if you are after a more robust and featured
           interface for working with BIDS datasets.
"""


import os.path   as op
import itertools as it
import              re
import              glob
import              json

import fsl.utils.memoize as memoize
import fsl.utils.path    as fslpath


class BIDSFile(object):
    """The ``BIDSFile`` class parses and stores the entities and suffix contained
    in a BIDS file. See the :func:`parseFilename` function.

    The :meth:`match` method can be used to compare two ``BIDSFile`` instances.

    The following attributes are available on a ``BIDSFile`` instance:

     - ``filename``: Absolute path to the file
     - ``entities``: Dict of ``key : value`` pairs, the entities that are
       present in the file name (e.g. ``{'sub' : '01}``)
     - ``suffix``: File suffix (e.g. ``T1w``, ``bold``, etc.)
    """


    def __init__(self, filename):
        """Create a ``BIDSFile``. """
        entities, suffix = parseFilename(filename)
        self.filename    = op.abspath(filename)
        self.entities    = entities
        self.suffix      = suffix


    def __str__(self):
        """Return a strimg representation of this ``BIDSFile``. """
        return 'BIDSFile({})'.format(self.filename)


    def __repr__(self):
        """Return a strimg representation of this ``BIDSFile``. """
        return str(self)


    def match(self, other, suffix=True):
        """Compare this ``BIDSFile`` to ``other``.

        :arg other:  ``BIDSFile`` to compare

        :arg suffix: Defaults to ``True``. If ``False``, the comparison
                     is made solely on the entity values.

        :returns:    ``True`` if ``self.suffix == other.suffix`` (unless
                     ``suffix`` is ``False``) and if all of the entities in
                     ``other`` are present in ``self``, ``False`` otherwise.
        """

        suffix   = (not suffix) or (self.suffix == other.suffix)
        entities = True

        for key, value in other.entities.items():
            entities = entities and (self.entities.get(key, None) == value)

        return suffix and entities


def parseFilename(filename):
    """Parses a BIDS-like file name. The file name must consist of zero or more
    "entities" (alpha-numeric ``name-value`` pairs), a "suffix", all separated
    by underscores, and a regular file extension. For example, the following
    file::

        sub-01_ses-01_task-stim_bold.nii.gz

    has suffix ``bold``, entities ``sub=01``, ``ses=01`` and ``task=stim``, and
    extension ``.nii.gz``.

    .. note:: This function assumes that no period (``.``) characters occur in
              the body of a BIDS filename.

    :returns: A tuple containing:
               - A dict containing the entities
               - The suffix
    """

    if not isBIDSFile(filename, strict=False):
        raise ValueError('Does not look like a BIDS '
                         'file: {}'.format(filename))

    suffix   = None
    entities = []
    filename = op.basename(filename)
    filename = fslpath.removeExt(filename, firstDot=True)
    parts    = filename.split('_')

    for part in parts[:-1]:
        entities.append(part.split('-'))

    suffix   = parts[-1]
    entities = dict(entities)

    return entities, suffix


def isBIDSDir(dirname):
    """Returns ``True`` if ``dirname`` is the root directory of a BIDS dataset.
    """
    return op.exists(op.join(dirname, 'dataset_description.json'))


def inBIDSDir(filename):
    """Returns ``True`` if ``filename`` looks like it is within a BIDS dataset
    directory, ``False`` otherwise.
    """

    dirname = op.abspath(op.dirname(filename))
    inBIDS  = False

    while True:

        if isBIDSDir(dirname):
            inBIDS = True
            break

        prevdir = dirname
        dirname = op.dirname(dirname)

        # at filesystem root
        if prevdir == dirname:
            break

    return inBIDS


def isBIDSFile(filename, strict=True):
    """Returns ``True`` if ``filename`` looks like a BIDS image or JSON file.

    :arg filename: Name of file to check
    :arg strict:   If ``True`` (the default), the file must be within a BIDS
                   dataset directory, as defined by :func:`inBIDSDir`.
    """

    name    = op.basename(filename)
    pattern = r'([a-z0-9]+-[a-z0-9]+_)*([a-z0-9])+\.(.+)'
    flags   = re.ASCII | re.IGNORECASE
    match   = re.fullmatch(pattern, name, flags) is not None

    return ((not strict) or inBIDSDir(filename)) and match


@memoize.memoize
def loadMetadataFile(filename):
    """Load ``filename`` (assumed to be JSON), returning its contents. """
    with open(filename, 'rt') as f:
        return json.load(f)


def loadMetadata(filename):
    """Load all of the metadata associated with ``filename``.

    :arg filename: Path to a data file in a BIDS dataset.
    :returns:      A dict containing all of the metadata associated with
                   ``filename``
    """

    filename  = op.realpath(op.abspath(filename))
    bfile     = BIDSFile(filename)
    dirname   = op.dirname(filename)
    prevdir   = filename
    metafiles = []
    metadata  = {}

    # Walk up the directory tree until
    # we hit the BIDS dataset root, or
    # the filesystem root
    while True:

        # Gather all json files in this
        # directory with matching entities
        # and suffix, sorted alphabetically
        # and reversed, so that earlier
        # ones take precedence
        files = reversed(sorted(glob.glob(op.join(dirname, '*.json'))))
        files = [BIDSFile(f) for f in files if isBIDSFile(f)]
        files = [f.filename  for f in files if bfile.match(f)]

        # build a list of all files
        metafiles.append(files)

        # move to the next dir up
        prevdir = dirname
        dirname = op.dirname(dirname)

        # stop when we hit the dataset or filesystem root
        if isBIDSDir(prevdir) or dirname == prevdir:
            break

    # Load in each json file, from
    # shallowest to deepest, so entries
    # in deeper files take precedence
    # over shallower ones.
    for f in it.chain(*reversed(metafiles)):

        # assuming here that every file contains a dict
        metadata.update(loadMetadataFile(f))

    return metadata
