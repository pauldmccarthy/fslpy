#!/usr/bin/env python
#
# query.py - The FileTreeQuery class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Michiel Cottaar <michiel.cottaar@.ndcn.ox.ac.uk>
#
"""This module contains the :class:`FileTreeQuery` class, which can be used to
search for files in a directory described by a `.FileTree`. A
``FileTreeQuery`` object returns :class:`Match` objects which each represent a
file that is described by the ``FileTree``, and which is present in the
directory.

The following utility functions, used by the ``FileTreeQuery`` class, are also
defined in this module:

.. autosummary::
   :nosignatures:

   scan
   allVariables
"""


import logging
import collections

import os.path as op
from typing import Dict, List, Tuple

import numpy as np

from . import FileTree


log = logging.getLogger(__name__)


class FileTreeQuery(object):
    """The ``FileTreeQuery`` class uses a :class:`.FileTree` to search
    a directory for files which match a specific query.

    A ``FileTreeQuery`` scans the contents of a directory which is described
    by a :class:`.FileTree`, and identifies all file types (a.k.a. *templates*
    or *short names*) that are present, and the values of variables within each
    short name that are present. The :meth:`query` method can be used to
    retrieve files which match a specific short name, and variable values.

    The :meth:`query` method returns a multi-dimensional ``numpy.array``
    which contains :class:`Match` objects, where each dimension one
    represents variable for the short name in question.

    Example usage::

        >>> from fsl.utils.filetree import FileTree, FileTreeQuery

        >>> tree  = FileTree.read('bids_raw', './my_bids_data')
        >>> query = FileTreeQuery(tree)

        >>> query.axes('anat_image')
        ['acq', 'ext', 'modality', 'participant', 'rec', 'run_index',
         'session']

        >>> query.variables('anat_image')
        {'acq': [None],
         'ext': ['.nii.gz'],
         'modality': ['T1w', 'T2w'],
         'participant': ['01', '02', '03'],
         'rec': [None],
         'run_index': [None, '01', '02', '03'],
         'session': [None]}

        >>> query.query('anat_image', participant='01')
        array([[[[[[[Match(./my_bids_data/sub-01/anat/sub-01_T1w.nii.gz)],
                    [nan],
                    [nan],
                    [nan]]]],

                 [[[[Match(./my_bids_data/sub-01/anat/sub-01_T2w.nii.gz)],
                    [nan],
                    [nan],
                    [nan]]]]]]], dtype=object)
    """


    def __init__(self, tree):
        """Create a ``FileTreeQuery``. The contents of the tree directory are
        scanned via the :func:`scan` function, which may take some time for
        large data sets.

        :arg tree: The :class:`.FileTree` object
        """

        # Find all files present in the directory
        # (as Match objects), and find all variables,
        # plus their values, and all short names,
        # that are present in the directory.
        matches                = scan(tree)
        allvars, shortnamevars = allVariables(tree, matches)

        # Now we are going to build a series of ND
        # arrays to store Match objects. We create
        # one array for each short name. Each axis
        # in an array corresponds to a variable
        # present in files of that short name type,
        # and each position along an axis corresponds
        # to one value of that variable.
        #
        # These arrays will be used to store and
        # retrieve Match objects - given a short
        # name and a set of variable values, we
        # can quickly find the corresponding Match
        # object (or objects).

        # matcharrays contains {shortname : ndarray}
        # mappings, and varidxs contains
        # {shortname : {varvalue : index}} mappings
        matcharrays = {}
        varidxs     = {}

        for shortname in shortnamevars.keys():

            snvars    = shortnamevars[shortname]
            snvarlens = [len(allvars[v]) for v in snvars]

            # An ND array for this short
            # name. Each element is a
            # Match object, or nan.
            matcharray    = np.zeros(snvarlens, dtype=np.object)
            matcharray[:] = np.nan

            # indices into the match array
            # for each variable value
            snvaridxs = {}
            for v in snvars:
                snvaridxs[v] = {n : i for i, n in enumerate(allvars[v])}

            matcharrays[shortname] = matcharray
            varidxs[    shortname] = snvaridxs

        # Populate the match arrays
        for match in matches:
            snvars    = shortnamevars[match.short_name]
            snvaridxs = varidxs[      match.short_name]
            snarr     = matcharrays[  match.short_name]
            idx       = []
            for var in snvars:

                val = match.variables[var]
                idx.append(snvaridxs[var][val])

            snarr[tuple(idx)] = match

        self.__allvars       = allvars
        self.__shortnamevars = shortnamevars
        self.__matches       = matches
        self.__matcharrays   = matcharrays
        self.__varidxs       = varidxs


    def axes(self, short_name) -> List[str]:
        """Returns a list containing the names of variables present in files
        of the given ``short_name`` type, in the same order of the axes of
        :class:`Match` arrays that are returned by the :meth:`query` method.
        """
        return self.__shortnamevars[short_name]


    def variables(self, short_name=None) -> Dict[str, List]:
        """Return a dict of ``{variable : [values]}`` mappings.
        This dict describes all variables and their possible values in
        the tree.

        If a ``short_name`` is specified, only variables which are present in
        files of that ``short_name`` type are returned.
        """
        if short_name is None:
            return {var : list(vals) for var, vals in self.__allvars.items()}
        else:
            varnames = self.__shortnamevars[short_name]
            return {var : list(self.__allvars[var]) for var in varnames}


    @property
    def short_names(self) -> List[str]:
        """Returns a list containing all short names of the ``FileTree`` that
        are present in the directory.
        """
        return list(self.__shortnamevars.keys())


    def query(self, short_name, asarray=False, **variables):
        """Search for files of the given ``short_name``, which match
        the specified ``variables``. All hits are returned for variables
        that are unspecified.

        :arg short_name:  Short name of files to search for.

        :arg asarray: If ``True``, the relevant :class:`Match` objects are
                      returned in a in a ND ``numpy.array`` where each
                      dimension corresponds to a variable for the
                      ``short_name`` in question (as returned by
                      :meth:`axes`). Otherwise (the default), they are
                      returned in a list.

        All other arguments are assumed to be ``variable=value`` pairs,
        used to restrict which matches are returned. All values are returned
        for variables that are not specified, or variables which are given a
        value of ``'*'``.

        :returns: A list  of ``Match`` objects, (or a ``numpy.array`` if
                  ``asarray=True``).
        """

        varnames    = list(variables.keys())
        allvarnames = self.__shortnamevars[short_name]
        varidxs     = self.__varidxs[    short_name]
        matcharray  = self.__matcharrays[short_name]
        slc         = []

        for var in allvarnames:

            if var in varnames: val = variables[var]
            else:               val = '*'

            # We're using np.newaxis to retain
            # the full dimensionality of the
            # array, so that the axis labels
            # returned by the axes() method
            # are valid.
            if val == '*': slc.append(slice(None))
            else:          slc.extend([np.newaxis, varidxs[var][val]])

        result = matcharray[tuple(slc)]

        if asarray: return result
        else:       return [m for m in result.flat if isinstance(m, Match)]


class Match(object):
    """A ``Match`` object represents a file with a name matching a template in
    a ``FileTree``.  The :func:`scan` function and :meth:`FileTree.query`
    method both return ``Match`` objects.
    """


    def __init__(self, filename, short_name, variables):
        """Create a ``Match`` object. All arguments are added as attributes.

        :arg filename:   name of existing file
        :arg short_name: template identifier
        :arg variables:  Dictionary of ``{variable : value}`` mappings
                         containing all variables present in the file name.
        """
        self.__filename   = filename
        self.__short_name = short_name
        self.__variables  = dict(variables)


    @property
    def filename(self):
        return self.__filename


    @property
    def short_name(self):
        return self.__short_name


    @property
    def variables(self):
        return dict(self.__variables)


    def __eq__(self, other):
        return (isinstance(other, Match)            and
                self.filename   == other.filename   and
                self.short_name == other.short_name and
                self.variables  == other.variables)


    def __lt__(self, other):
        return isinstance(other, Match) and self.filename < other.filename


    def __le__(self, other):
        return isinstance(other, Match) and self.filename <= other.filename


    def __repr__(self):
        """Returns a string representation of this ``Match``. """
        return 'Match({})'.format(self.filename)


    def __str__(self):
        """Returns a string representation of this ``Match``. """
        return repr(self)


def scan(tree : FileTree) -> List[Match]:
    """Scans the directory of the given ``FileTree`` to find all files which
    match a tree template.

    :return: list of :class:`Match` objects
    """

    matches = []
    for template in tree.templates:
        for filename in tree.get_all(template, glob_vars='all'):

            if not op.isfile(filename):
                continue

            variables = dict(tree.extract_variables(template, filename))

            matches.append(Match(filename, template, variables))

    for tree_name, sub_tree in tree.sub_trees.items():
        matches.extend(scan(sub_tree))

    return matches


def allVariables(
        tree    : FileTree,
        matches : List[Match]) -> Tuple[Dict[str, List], Dict[str, List]]:
    """Identifies the ``FileTree`` variables which are actually represented
    in files in the directory.

    :arg filetree: The ``FileTree`` object
    :arg matches:  list of ``Match`` objects (e.g. as returned by :func:`scan`)

    :returns: a tuple containing two dicts:

               - A dict of ``{ variable : [values] }`` mappings containing all
                 variables and their possible values present in the given list
                 of ``Match`` objects.

               - A dict of ``{ short_name : [variables] }`` mappings,
                 containing the variables which are relevant to each short
                 name.
    """
    allvars       = collections.defaultdict(set)
    allshortnames = collections.defaultdict(set)

    for m in matches:
        for var, val in m.variables.items():
            allvars[      var]         .add(val)
            allshortnames[m.short_name].add(var)

    # allow us to compare None with strings
    def key(v):
        if v is None: return ''
        else:         return v

    allvars       = {var : list(sorted(vals, key=key))
                     for var, vals in allvars.items()}
    allshortnames = {sn  : list(sorted(vars))
                     for sn, vars in allshortnames.items()}

    return allvars, allshortnames
