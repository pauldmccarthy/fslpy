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


log = logging.getLogger(__name__)


class FileTreeQuery(object):
    """The ``FileTreeQuery`` class uses a :class:`.FileTree` to search
    a directory for files which match a specific query.


    """


    def __init__(self, tree):
        """Create a ``FileTreeQuery``.

        :arg tree: The ``FileTree`` object
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
            return dict(self.__allvars)
        else:
            varnames = self.__shortnamevars[short_name]
            return {var : self.__allvars[var] for var in varnames}


    @property
    def short_names(self) -> List[str]:
        """Returns a list containing all short names of the ``FileTree`` that
        are present in the directory.
        """
        return list(self.__shortnamevars.keys())


    def query(self, short_name, **variables):
        """Search for files of the given ``short_name``, which match
        the specified ``variables``. All hits are returned for variables
        that are unspecified.

        :arg short_name: Short name of files to search for.

        All other arguments are assumed to be ``variable=value`` pairs,
        used to restrict which matches are returned. All values are returned
        for variables that are not specified, or variables which are given a
        value of ``'*'``.

        :returns: A ``numpy.array`` of ``Match`` objects, with axes
                  corresponding to the labels returned by the :meth:`axes`
                  method.
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

        return matcharray[tuple(slc)]


def scan(tree):
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

    for tree_name, sub_tree in tree.sub_trees:
        matches.extend(Match.scan(sub_tree))

    return matches


def allVariables(tree, matches) -> Tuple[Dict[str, List], Dict[str, List]]:
    """Identifies the ``FileTree`` variables which are actually represented
    in files in the directory.

    :arg filetree: The ``FileTree``object
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


class Match(object):
    """A ``Match`` object represents a file with a name matching a template in
    a ``FileTree``.
    """


    def __init__(self, filename, short_name, variables):
        """Create a ``Match`` object. All arguments are added as attributes.

        :arg filename:   name of existing file
        :arg short_name: template identifier
        :arg variables:  Dictionary of ``{variable : value}`` mappings
                         containing all variables present in the file name.
        """
        self.filename   = filename
        self.short_name = short_name
        self.variables  = dict(variables)


    def __repr__(self):
        """Returns a string representation of this ``Match``. """
        return 'Match({})'.format(self.filename)


    def __str__(self):
        """Returns a string representation of this ``Match``. """
        return repr(self)
