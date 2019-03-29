import re
import itertools
import glob
from . import filetree


def resolve(template, variables):
    """
    Resolves the template given a set of variables

    :param template: template
    :param variables: mapping of variable names to values
    :return: cleaned string
    """
    filled = fill_known(template, variables)
    filename = resolve_optionals(filled)
    remaining = find_variables(filename)
    if len(remaining) > 0:
        raise filetree.MissingVariable('Variables %s not defined' % set(remaining))
    return filename


def get_all(template, variables, glob_vars=()):
    """
    Gets all variables matching the templates given the variables

    :param template: template
    :param variables: (incomplete) mapping of variable names to values
    :param glob_vars: sequence of undefined variables that can take any possible values when looking for matches on the disk
        If `glob_vars` contains any defined variables, it will be ignored.
    :return: sequence of filenames
    """
    filled = fill_known(template, variables)
    remaining = set(find_variables(filled))
    optional = optional_variables(filled)
    res = set()
    if glob_vars == 'all':
        glob_vars = remaining
    glob_vars = set(glob_vars).difference(variables.keys())

    undefined_vars = remaining.difference(glob_vars).difference(optional)
    if len(undefined_vars) > 0:
        raise KeyError("Required variables {} were not defined".format(undefined_vars))

    for keep in itertools.product(*[(True, False) for _ in optional.intersection(glob_vars)]):
        sub_variables = {var: '*' for k, var in zip(keep, optional) if k}
        for var in remaining.difference(optional).intersection(glob_vars):
            sub_variables[var] = '*'
        sub_filled = fill_known(filled, sub_variables)

        pattern = resolve_optionals(sub_filled)
        assert len(find_variables(pattern)) == 0

        for filename in glob.glob(pattern):
            try:
                extract_variables(filled, filename)
            except ValueError:
                continue
            res.add(filename)
    return sorted(res)


def fill_known(template, variables):
    """
    Fills in the known variables filling the other variables with {<variable_name>}

    :param template: template
    :param variables: mapping of variable names to values (ignoring any None)
    :return: cleaned string
    """
    prev = ''
    while prev != template:
        prev = template
        settings = {}
        for name in set(find_variables(template)):
            if name in variables and variables[name] is not None:
                settings[name] = variables[name]
            else:
                settings[name] = '{' + name + '}'
        template = template.format(**settings)
    return template


def resolve_optionals(text):
    """
    Resolves the optional sections

    :param text: template after filling in the known variables
    :return: cleaned string
    """
    def resolve_single_optional(part):
        if len(part) == 0:
            return part
        if part[0] != '[' or part[-1] != ']':
            return part
        elif len(find_variables(part)) == 0:
            return part[1:-1]
        else:
            return ''

    res = [resolve_single_optional(text) for text in re.split('(\[.*?\])', text)]
    return ''.join(res)


def find_variables(template):
    """
    Finds all the variables in the template

    :param template: full template
    :return: sequence of variables
    """
    return tuple(var.split(':')[0] for var in re.findall("\{(.*?)\}", template))


def optional_variables(template):
    """
    Finds the variables that can be skipped

    :param template: full template
    :return: set of variables that are only present in optional parts of the string
    """
    include = set()
    exclude = set()
    for text in re.split('(\[.*?\])', template):
        if len(text) == 0:
            continue
        variables = find_variables(text)
        if text[0] == '[' and text[-1] == ']':
            include.update(variables)
        else:
            exclude.update(variables)
    return include.difference(exclude)


def extract_variables(template, filename, known_vars=None):
    """
    Extracts the variable values from the filename

    :param template: template matching the given filename
    :param filename: filename
    :param known_vars: already known variables
    :return: dictionary from variable names to string representations (unused variables set to None)
    """
    if known_vars is None:
        known_vars = {}
    template = fill_known(template, known_vars)
    while '//' in filename:
        filename = filename.replace('//', '/')
    remaining = set(find_variables(template))
    optional = optional_variables(template)
    for keep in itertools.product(*[(True, False) for _ in optional]):
        sub_re = resolve_optionals(fill_known(
                template,
                dict(
                        **{var: '(\S+)' for k, var in zip(keep, optional) if k},
                        **{var: '(\S+)' for var in remaining.difference(optional)}
                )
        ))
        while '//' in sub_re:
            sub_re = sub_re.replace('//', '/')
        sub_re = sub_re.replace('.', '\.')
        if re.match(sub_re, filename) is None:
            continue

        extracted_value = {}
        kept_vars = [var for var in find_variables(template)
                     if var not in optional or keep[list(optional).index(var)]]
        for var, value in zip(kept_vars, re.match(sub_re, filename).groups()):
            if var in extracted_value:
                if value != extracted_value[var]:
                    raise ValueError('Multiple values found for {}'.format(var))
            else:
                extracted_value[var] = value
        if any('/' in value for value in extracted_value.values()):
            continue
        for name in find_variables(template):
            if name not in extracted_value:
                extracted_value[name] = None
        extracted_value.update(known_vars)
        return extracted_value
    raise ValueError("{} did not match {}".format(filename, template))
