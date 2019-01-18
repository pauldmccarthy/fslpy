#!/usr/bin/env python
#
# query.py - The FileTreeQuery class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Michiel Cottaar <michiel.cottaar@.ndcn.ox.ac.uk>
#
"""
"""


import logging
import collections

import os.path as op
from typing import Dict, Set, List


log = logging.getLogger(__name__)


class FileTreeQuery(object):

    def __init__(self, tree):
        """
        """
        self.__tree      = tree
        self.__matches   = Match.scan(tree)
        self.__variables = Match.allVariables(tree, self.__matches)


    def variables(self) -> Dict[str, Set]:
        """Return a dict of ``{variable : [values]}`` mappings.
        This dict describes all variables and their possible values in
        the tree.
        """
        return dict(self.__variables)


    def query(self, **variables) -> List[str]:
        """Return all ``Match`` objects which match the given set of
        ``variable=value`` arguments.
        """
        hits = []

        for m in self.__matches:
            if all([m.variables.get(n, None) == v
                    for n, v in variables.items()]):
                hits.append(m)

        return hits


class Match(object):
    """
    Filename matching a template in the file tree
    """

    @staticmethod
    def allVariables(tree, matches) -> Dict[str, Set]:
        """Returns a dict of ``{ variable : [values] }`` mappings
        containing all variables and their possible values present
        in the given list of ``Match`` objects.
        """
        allvars = collections.defaultdict(set)

        for m in matches:
            for var, val in m.variables.items():
                allvars[var].add(val)
        return allvars


    @staticmethod
    def scan(tree):
        """
        Scans the disk to find any matches

        :return: list of :class:`Match` objects
        """

        matches = []
        for template in tree.templates:
            for filename in tree.get_all(template, glob_vars='all'):

                if not op.isfile(filename):
                    continue

                variables = tree.extract_variables(template, filename)
                variables = {var : val
                             for var, val in variables.items()
                             if val is not None}

                matches.append(Match(filename, template, variables))

        for tree_name, sub_tree in tree.sub_trees:
            matches.extend(Match.scan(sub_tree))

        return matches


    def __init__(self, filename, short_name, variables):
        """
        Defines a new match

        :param filename: name of existing file
        :param short_name: template identifier
        :param variables: variable values
        """
        self.filename = filename
        self.short_name = short_name
        self.variables = dict(variables)


    def __repr__(self):
        return self.filename


    def __str__(self):
        return repr(self)
