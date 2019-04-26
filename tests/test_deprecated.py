#!/usr/bin/env python


import warnings
import pytest

import fsl.utils.deprecated as deprecated


# the line number of the warning is hard coded in
# the unit tests below. Don't change the line number!
def emit_warning():
    deprecated.warn('blag', vin='1.0.0', rin='2.0.0', msg='yo')

WARNING_LINE_NUMBER = 13


@deprecated.deprecated(vin='1.0.0', rin='2.0.0', msg='yo')
def depfunc():
    pass

def call_dep_func():
    depfunc()

DEPRECATED_LINE_NUMBER = 23


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
