#!/usr/bin/env python


import warnings
import pytest

import fsl.utils.deprecated as deprecated


# these  get updated in the relevant functions
WARNING_LINE_NUMBER = None
DEPRECATED_LINE_NUMBER = None

def _linenum(pattern):
    with open(__file__, 'rt') as f:
        for i, line in enumerate(f.readlines(), 1):
            if pattern in line:
                return i
    return -1


def emit_warning():
    deprecated.warn('blag', vin='1.0.0', rin='2.0.0', msg='yo')
    global WARNING_LINE_NUMBER
    WARNING_LINE_NUMBER = _linenum('deprecated.warn(\'blag\'')


@deprecated.deprecated(vin='1.0.0', rin='2.0.0', msg='yo')
def depfunc():
    pass

def call_dep_func():
    depfunc()  # mark
    global DEPRECATED_LINE_NUMBER
    DEPRECATED_LINE_NUMBER = _linenum('depfunc()  # mark')


def _check_warning(w, name, lineno):
    assert issubclass(w.category, DeprecationWarning)
    assert '{} is deprecated'.format(name) in str(w.message)
    assert 'test_deprecated.py' in str(w.filename)
    assert w.lineno == lineno

def test_warn():
    deprecated.resetWarningCache()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        emit_warning()
        assert len(w) == 1
        _check_warning(w[0], 'blag', WARNING_LINE_NUMBER)

    # warning should only be emitted once
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        emit_warning()
        assert len(w) == 0


def test_deprecated():
    deprecated.resetWarningCache()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        call_dep_func()
        assert len(w) == 1
        _check_warning(w[0], 'depfunc', DEPRECATED_LINE_NUMBER)

    # warning should only be emitted once
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always')
        call_dep_func()
        assert len(w) == 0
