"""mc_filetree - Easy format to define intput/output files in a python pipeline"""

__author__ = 'Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>'

from .filetree import FileTree, register_tree, MissingVariable
from .parse import tree_directories
