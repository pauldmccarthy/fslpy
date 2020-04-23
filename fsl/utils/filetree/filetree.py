from pathlib import Path, PurePath
from typing import Tuple, Optional, Dict, Any, Set
from . import parse
import pickle
import json
import os.path as op
from . import utils


class MissingVariable(KeyError):
    """
    Returned when the variables of a tree or its parents do not contain a given variable
    """
    pass


class FileTree(object):
    """
    Contains the input/output filename tree

    Properties:

    - ``templates``: dictionary mapping short names to filename templates
    - ``variables``: dictionary mapping variables in the templates to specific values (variables set to None are explicitly unset)
    - ``sub_trees``: filename trees describing specific sub-directories
    - ``parent``: parent FileTree, of which this sub-tree is a sub-directory
    - ``name``: descriptive name of the tree
    """
    def __init__(self,
                 templates:    Dict[str, str],
                 variables:    Dict[str, Any],
                 sub_trees:    Dict[str, "FileTree"] = None,
                 parent:       Optional["FileTree"] = None,
                 name:         str = None):
        """
        Creates a new filename tree.
        """
        self.templates = templates
        self.variables = variables
        if sub_trees is None:
            sub_trees = {}
        self.sub_trees = sub_trees
        self._parent = parent
        self._name = name

    @property
    def parent(self, ):
        """
        Parent FileTree, of which this sub-tree is a sub-directory
        """
        return self._parent

    @property
    def name(self, ):
        """
        Name of this ``FileTree``, or ``None`` if it has no name.
        """
        return self._name

    @property
    def all_variables(self, ):
        """
        All tree variables including those inherited from the parent tree
        """
        if self.parent is None:
            return dict(self.variables)
        res = self.parent.all_variables
        res.update(self.variables)
        return res

    def get_variable(self, name: str, default=None) -> str:
        """
        Gets a variable used to fill out the template

        :param name: variable name
        :param default: default variables (if not set a MissingVariable error is raised if a variable is missing)
        :return: value of the variable
        """
        variables = self.all_variables
        if name in variables and variables[name] is not None:
            return variables[name]
        if default is None:
            raise MissingVariable('Variable {} not found in sub-tree or parents'.format(name))
        return default

    def _get_template_tree(self, short_name: str) -> Tuple["FileTree", str]:
        """
        Retrieves template text from this tree, parent tree or sub_tree

        :param short_name: filename reference name
        :return: tuple with the containing tree and the template text
        """
        if '/' in short_name:
            sub_tree, sub_name = short_name.split('/', maxsplit=1)
            if sub_tree == '..':
                if self.parent is None:
                    raise KeyError("Tried to access the parent of the top-level tree")
                return self.parent._get_template_tree(sub_name)
            return self.sub_trees[sub_tree]._get_template_tree(sub_name)
        return self, self.templates[short_name]

    def get_template(self, short_name: str) -> Tuple[str, Dict[str, str]]:
        """
        Returns the sub-tree that defines a given short name

        - '/' characters in short_name refer to sub-trees
        - '../' characters in short_name refer to parents

        For example:

        - "eddy/output" refers to the "output" in the "eddy" sub_tree (i.e. ``self.sub_trees['eddy'].templates['output']``)
        - "../other/name" refers to the "other" sub-tree of the parent tree (i.e., ``self.parent.sub_trees['other'].templates['name']``)

        :param short_name: name of the template
        :return: tuple with the template and the variables corresponding to the template
        """
        tree, text = self._get_template_tree(short_name)
        return text, tree.all_variables

    def template_variables(self, short_name: Optional[str]=None, optional=True, required=True) -> Set[str]:
        """
        Returns the variables needed to define a template

        :param short_name: name of the template (defaults to all)
        :param optional: if set to False don't include the optional variables
        :param required: if set to False don't include the required variables
        :return: set of variable names
        """
        if not optional and not required:
            return set()
        if short_name is None:
            all_vars = set()
            required_vars = set()
            for short_name in self.templates.keys():
                all_vars.update(self.template_variables(short_name))
                if required or optional:
                    required_vars.update(self.template_variables(short_name, optional=False))
            for sub_tree in self.sub_trees.values():
                all_vars.update(sub_tree.template_variables())
                if required or optional:
                    required_vars.update(sub_tree.template_variables(optional=False))
            if optional and required:
                return all_vars
            if required:
                return required_vars
            if optional:
                return all_vars.difference(required_vars)
        else:
            _, text = self._get_template_tree(short_name)
            all_vars = set(utils.find_variables(text))
            if optional and required:
                return all_vars
            opt_vars = set(utils.optional_variables(text))
            if optional:
                return opt_vars
            if required:
                return all_vars.difference(opt_vars)

    def get(self, short_name, make_dir=False) -> str:
        """
        Gets a full filename based on its short name

        :param short_name: identifier in the tree
        :param make_dir: if True make sure that the directory leading to this file exists
        :return: full filename
        """
        text, variables = self.get_template(short_name)
        res = Path(utils.resolve(text, variables))
        if make_dir:
            res.parents[0].mkdir(parents=True, exist_ok=True)
        return str(res)

    def get_all(self, short_name: str, glob_vars=()) -> Tuple[str]:
        """
        Gets all existing directory/file names matching a specific pattern

        :param short_name: short name of the path template
        :param glob_vars: sequence of undefined variables that can take any possible values when looking for matches on the disk.
            Any defined variables in `glob_vars` will be ignored.
            If glob_vars is set to 'all', all undefined variables will be used to look up matches.
        :return: sequence of paths
        """
        return tuple([self.update(**vars).get(short_name)
                      for vars in self.get_all_vars(short_name, glob_vars=glob_vars)])

    def get_all_vars(self, short_name: str, glob_vars=()) -> Tuple[Dict[str, str]]:
        """
        Gets all the parameters that generate existing filenames

        :param short_name: short name of the path template
        :param glob_vars: sequence of undefined variables that can take any possible values when looking for matches on the disk.
            Any defined variables in `glob_vars` will be ignored.
            If glob_vars is set to 'all', all undefined variables will be used to look up matches.
        :return: sequence of dictionaries with the variables settings used to generate each filename
        """
        text, variables = self.get_template(short_name)
        return utils.get_all(text, variables, glob_vars=glob_vars)

    def get_all_trees(self, short_name: str, glob_vars=(), set_parent=True) -> Tuple["FileTree"]:
        """
        Gets all the trees that generate the existing files matching the pattern

        tree.get_all(short_name) == tuple(tree.get(short_name) for tree in tree.get_all_trees(short_name))

        :param short_name: short name of the path template
        :param glob_vars: sequence of undefined variables that can take any possible values when looking for matches on the disk.
            Any defined variables in `glob_vars` will be ignored.
            If glob_vars is set to 'all', all undefined variables will be used to look up matches.
        :param set_parent: Update the variables of the top-level rather than current tree if True.
            Ony relevant if `self` is a sub-tree.
        :return: sequence of FileTrees used to generate each file on disk matching the pattern of `short_name`
        """
        return tuple(self.update(set_parent=set_parent, **vars)
                     for vars in self.get_all_vars(short_name, glob_vars=glob_vars))

    def update(self, set_parent=True, **variables) -> "FileTree":
        """
        Creates a new FileTree with updated variables

        :param set_parent: Update the variables of the top-level rather than current tree if True.
            Ony relevant if `self` is a sub-tree.
        :param variables: new values for the variables
            Setting a variable to None will cause the variable to be unset
        :return: New FileTree with same templates for directory names and filenames, but updated variables
        """
        new_tree = self.copy()
        set_tree = new_tree
        while set_parent and set_tree.parent is not None:
            set_tree = set_tree.parent
        set_tree.variables.update(variables)
        for key, value in variables.items():
            if value is None:
                del set_tree.variables[key]
        return new_tree

    def extract_variables(self, short_name: str, filename: str) -> Dict[str, str]:
        """
        Extracts the variables from the given filename

        :param short_name: short name of the path template
        :param filename: filename matching the template
        :return: variables needed to get to the given filename
            Variables with None value are optional variables in the template that were not used
        """
        text, _ = self.get_template(short_name)
        return utils.extract_variables(text, filename, self.variables)

    def save_pickle(self, filename):
        """
        Saves the Filetree to a pickle file

        :param filename: filename to store the file tree (usually ending with .pck)
        """
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

    def save_json(self, filename):
        """
        Saves the Filetree to a JSON file

        :param filename: filename to store the file tree in
        """
        def default(obj):
            if isinstance(obj, FileTree):
                res = dict(obj.__dict__)
                del res['_parent']
                return res
            return obj

        with open(filename, 'w') as f:
            json.dump(self, f, default=default, indent=2)

    @classmethod
    def load_pickle(cls, filename):
        """
        Loads the Filetree from a pickle file

        :param filename: filename produced from Filetree.save_pickle
        :return: stored Filetree
        """
        with open(filename, 'rb') as f:
            res = pickle.load(f)
        if not isinstance(res, cls):
            raise IOError("Pickle file did not contain %s object" % cls)
        return res

    @classmethod
    def load_json(cls, filename):
        """
        Loads the FileTree from a JSON file

        :param filename: filename produced by FileTree.save_json
        :return: stored FileTree
        """
        def from_dict(input_dict):
            res_tree = FileTree(
                templates=input_dict['templates'],
                variables=input_dict['variables'],
                sub_trees={name: from_dict(value) for name, value in input_dict['sub_trees'].items()},
                name=input_dict['_name'],
            )
            for sub_tree in res_tree.sub_trees.values():
                sub_tree._parent = res_tree
            return res_tree

        with open(filename, 'r') as f:
            as_dict = json.load(f)
        return from_dict(as_dict)

    def defines(self, short_names, error=False):
        """
        Checks whether templates are defined for all the `short_names`

        :param short_names: sequence of expected short names to exist in the tree
        :param error: if True raises ValueError if any `short_names` are undefined
        :return: True if all are defined, False otherwise
        :raise: ValueError if `error` is set to True and any template is missing
        """
        if isinstance(short_names, str):
            short_names = (short_names, )

        def single_test(short_name):
            try:
                self._get_template_tree(short_name)
            except KeyError:
                return True
            return False

        missing = tuple(name for name in short_names if single_test(name))

        if len(missing) > 0:
            if error:
                raise ValueError("Provided Filetree is missing template definitions for {}".format(missing))
            return False
        return True

    def on_disk(self, short_names, error=False, glob_vars=()):
        """
        Checks whether at least one file exists for every file in `short_names`

        :param short_names: list of expected short names to exist in the tree
        :param error: if True raises a helpful error when the check fails
        :param glob_vars: sequence of undefined variables that can take any possible values when looking for matches on the disk
            If `glob_vars` contains any defined variables, it will be ignored.
        :return: True if short names exist and optionally exist on disk (False otherwise)
        :raise:
            - ValueError if error is set and the tree is incomplete
            - IOError if error is set and any files are missing from the disk
        """
        self.defines(short_names, error=error)

        if isinstance(short_names, str):
            short_names = (short_names, )

        try:
            missing = tuple(name for name in short_names if len(self.get_all(name, glob_vars=glob_vars)) == 0)
        except KeyError:
            if error:
                raise
            return False
        if len(missing) > 0:
            if error:
                raise IOError("Failed to find any files on disk for {}".format(missing))
            return False
        return True

    def partial_fill(self, ) -> "FileTree":
        """
        Fills in known variables into the templates

        :return: The resulting tree will have empty `variables` dictionaries and updated templates
        """
        new_tree = self.copy()
        to_update = new_tree
        while to_update.parent is not None:
            to_update = to_update.parent
        to_update._update_partial_fill()
        return new_tree

    def _update_partial_fill(self, ):
        """
        Helper function for `partial_fill` that updates the templates in place
        """
        new_templates = {}
        for short_name in self.templates:
            template, variables = self.get_template(short_name)
            new_templates[short_name] = str(utils.Template.parse(template).fill_known(variables))
        self.templates = new_templates

        for tree in self.sub_trees.values():
            tree._update_partial_fill()
        self.variables = {}

    def copy(self, ):
        """
        Copies the FileTree

        Copies the templates, variables, sub_trees, and parent

        :return: a copy of the FileTree
        """
        return self._copy()

    def _copy(self, new_parent=None, new_sub_tree=None):
        """
        Helper function for copying a FileTree
        """
        if new_sub_tree is None:
            new_sub_tree = (None, None)
        new_copy = type(self)(
            templates=self.templates.copy(),
            variables=self.variables.copy(),
            name=self.name,
            parent=new_parent
        )
        new_copy.sub_trees = {name: new_sub_tree[1] if new_sub_tree[0] == name else tree._copy(new_parent=new_copy)
                              for name, tree in self.sub_trees.items()}
        if self.parent is not None and new_parent is None:
            for my_key, ref_tree in self.parent.sub_trees.items():
                if self is ref_tree:
                    break
            else:
                raise ValueError(f"Sub-tree {self} not found in parent tree")
            new_copy._parent = self.parent._copy(new_sub_tree=(my_key, new_copy))
        return new_copy

    @classmethod
    def read(cls, tree_name: str, directory='.', partial_fill=False, **variables) -> "FileTree":
        """
        Reads a FileTree from a specific file

        The return type is ``cls`` unless the tree_name has been previously registered.
        The return type of any sub-tree is ``FileTree`` unless the tree_name has been previously registered.

        :param tree_name: file containing the filename tree.
            Can provide the filename of a tree file or the name for a tree in the ``filetree.tree_directories``.
        :param directory: parent directory of the full tree (defaults to current directory)
        :param partial_fill: By default any known `variables` are filled into the `template` immediately
        :param variables: variable settings
        :return: dictionary from specifier to filename
        """
        if op.exists(tree_name):
            filename = tree_name
        elif op.exists(tree_name + '.tree'):
            filename = tree_name + '.tree'
        else:
            filename = parse.search_tree(tree_name)
        tree_name = op.splitext(op.basename(filename))[0]
        filename = Path(filename)
        dirname = str(filename.parent)

        templates = {}
        nspaces_level = []
        sub_trees = {}

        file_variables = {}

        with open(str(filename), 'r') as f:
            for full_line in f:
                # ignore anything behind the first #-character
                line = full_line.split('#')[0]

                if len(line.strip()) == 0:
                    continue

                if line.strip()[:2] == '->':
                    nspaces = line.index('->')

                    if len(nspaces_level) == 0:
                        sub_dir = directory
                    elif nspaces > nspaces_level[-1]:
                        sub_dir = current_filename
                    elif nspaces < nspaces_level[-1]:
                        if nspaces not in nspaces_level:
                            raise ValueError('line %s dropped to a non-existent level' % line)
                        new_level = nspaces_level.index(nspaces)
                        current_filename = current_filename.parents[len(nspaces_level) - new_level - 1] / filename
                        nspaces_level = nspaces_level[:new_level + 1]
                        sub_dir = current_filename.parents[0]
                    else:
                        sub_dir = current_filename.parents[0]

                    with parse.extra_tree_dirs([dirname]):
                        _, sub_tree, short_name = parse.read_subtree_line(line, sub_dir)
                    if short_name in sub_trees:
                        raise ValueError("Name of sub_tree {short_name} used multiple times in {tree_name}.tree".format(**locals()))

                    sub_trees[short_name] = sub_tree
                    sub_tree._name = short_name
                elif '=' in line:
                    key, value = line.split('=')
                    if len(key.split()) != 1:
                        raise ValueError("Variable assignment could not be parsed: {line}".format(**locals()))
                    file_variables[key.strip()] = value.strip()
                else:
                    nspaces, filename, short_name = parse.read_line(line)
                    if short_name in templates:
                        raise ValueError("Name of directory/file {short_name} used multiple times in {tree_name}.tree".format(**locals()))

                    if len(nspaces_level) == 0:
                        current_filename = PurePath(directory) / filename
                        nspaces_level.append(nspaces)
                    elif nspaces > nspaces_level[-1]:
                        # increase the level
                        current_filename = current_filename / filename
                        nspaces_level.append(nspaces)
                    elif nspaces < nspaces_level[-1]:
                        # decreased the level
                        if nspaces not in nspaces_level:
                            raise ValueError('line %s dropped to a non-existent level' % full_line)
                        new_level = nspaces_level.index(nspaces)
                        current_filename = current_filename.parents[len(nspaces_level) - new_level - 1] / filename
                        nspaces_level = nspaces_level[:new_level + 1]
                    else:
                        current_filename = current_filename.parents[0] / filename
                    templates[short_name] = str(current_filename)

        file_variables.update(variables)
        res = get_registered(tree_name, cls)(templates, variables=file_variables, sub_trees=sub_trees, name=tree_name)
        for tree in sub_trees.values():
            tree._parent = res
        if partial_fill:
            res = res.partial_fill()
        return res


_registered_subtypes = {}


def register_tree(name: str, tree_subtype: type):
    """
    Registers a tree_subtype under name

    Loading a tree with given name will lead to the `tree_subtype` rather than FileTree to be returned

    :param name: name of tree filename
    :param tree_subtype: tree subtype
    """
    global _registered_subtypes
    if not issubclass(tree_subtype, FileTree):
        raise ValueError("Only sub-classes of FileTree can be registered")
    _registered_subtypes[name] = tree_subtype


def get_registered(name, default=FileTree) -> type:
    """
    Get the previously registered subtype for ``name``

    :param name: name of the sub-tree
    :param default: type to return if the name has not been registered
    :return: FileTree or sub-type thereof
    """
    if name in _registered_subtypes:
        return _registered_subtypes[name]
    name = op.split(name)[1]
    if name in _registered_subtypes:
        return _registered_subtypes[name]
    while name.endswith('.tree'):
        name = name[:-5]
        if name in _registered_subtypes:
            return _registered_subtypes[name]
    return default
