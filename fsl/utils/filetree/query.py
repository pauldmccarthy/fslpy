#!/usr/bin/env python
#
# query.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
# Author: Michiel Cottaar <michiel.cottaar@.ndcn.ox.ac.uk>
#


import logging
import collections
from   typing import Dict, Set, List


log = logging.getLogger(__name__)


class FileTreeQuery(object):

    def __init__(self, tree):
        """
        """
        self.__tree      = tree
        self.__matches   = self.__tree.scan()
        self.__variables = Match.allVariables(self.__tree, self.__matches)


    def variables(self) -> Dict[str, Set]:
        """Return a dict of ``{variable : [values]}`` mappings.
        This dict describes all variables and their possible values in
        the tree.
        """
        return dict(self.__variables)


    def query(self, **variables) -> List[str]:
        """
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
    def allVariables(tree, matches) -> Dict(str, Set):
        """
        """
        allvars = collections.defaultdict(set)

        for m in matches:
            for var, val in m.variables.items():
                allvars[var].update(val)
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
                variables = tree.extract_variables(template, filename)
                match = Match(filename, template, variables)
                matches.append(match)
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
