#!/usr/bin/env python
#
# test_wrapperutils.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import shlex

import pytest

import fsl.wrappers.wrapperutils as wutils


def test_applyArgStyle():

    kwargs = {
        'name'  : 'val',
        'name2' : ['val1', 'val2'],
    }

    # these combinations of style+valsep should
    # raise an error
    with pytest.raises(ValueError):
        wutils.applyArgStyle(style='-=',  valsep=' ', **kwargs)
    with pytest.raises(ValueError):
        wutils.applyArgStyle(style='--=', valsep=' ', **kwargs)

    # unsupported style/valsep
    with pytest.raises(ValueError):
        wutils.applyArgStyle('?', **kwargs)
    with pytest.raises(ValueError):
        wutils.applyArgStyle('-', valsep='b', **kwargs)

    # style, valsep, expected_result.
    # Order of arguments is not guaranteed
    tests = [
        ('-',   ' ', [' -name  val', '-name2   val1 val2']),
        ('-',   '"', [' -name  val', '-name2  "val1 val2"']),
        ('-',   ',', [' -name  val', '-name2   val1,val2']),

        ('--',  ' ', ['--name  val', '--name2  val1 val2']),
        ('--',  '"', ['--name  val', '--name2 "val1 val2"']),
        ('--',  ',', ['--name  val', '--name2  val1,val2']),

        ('-=',  '"', [' -name=val', '-name2="val1 val2"']),
        ('-=',  ',', [' -name=val', '-name2=val1,val2']),

        ('--=', '"', ['--name=val', '--name2="val1 val2"']),
        ('--=', ',', ['--name=val', '--name2=val1,val2']),
    ]

    for style, valsep, exp in tests:
        exp    = [shlex.split(e) for e in exp]
        result = wutils.applyArgStyle(style, valsep=valsep, **kwargs)

        assert result in (exp[0] + exp[1], exp[1] + exp[0])


def test_applyArgStyle_argmap():

    kwargs = {
        'name1' : 'val1',
        'name2' : 'val2',
    }

    argmap = {
        'name1' : 'n',
        'name2' : 'm',
    }

    # order not guaranteed
    exp = [shlex.split('-n val1 -m val2'),
           shlex.split('-m val2 -n val1')]

    assert wutils.applyArgStyle('-', argmap=argmap, **kwargs) in exp


def test_applyArgStyle_valmap():

    valmap = {
        'a' : wutils.SHOW_IF_TRUE,
        'b' : wutils.HIDE_IF_TRUE,
    }

    # kwargs, expected
    tests = [
        ({                          }, ['']),
        ({ 'a' : False,             }, ['']),
        ({ 'a' : True,              }, ['-a']),
        ({              'b' : False }, ['-b']),
        ({              'b' : True  }, ['']),
        ({ 'a' : False, 'b' : True  }, ['']),
        ({ 'a' : True,  'b' : True  }, ['-a']),
        ({ 'a' : False, 'b' : False }, ['-b']),
        ({ 'a' : False, 'b' : True  }, ['']),
        ({ 'a' : True,  'b' : False }, ['-a -b', '-b -a']),
        ({ 'a' : True,  'b' : True  }, ['-a']),
    ]

    for kwargs, expected in tests:
        expected = [shlex.split(e) for e in expected]
        assert wutils.applyArgStyle('-', valmap=valmap, **kwargs) in expected


def test_applyArgStyle_argmap_valmap():

    argmap = {'a1' : 'a', 'a2' : 'b'}
    valmap = {
        'a' : wutils.SHOW_IF_TRUE,
        'b' : wutils.HIDE_IF_TRUE,
    }

    # kwargs, expected
    tests = [
        ({                            }, ['']),
        ({ 'a1' : False,              }, ['']),
        ({ 'a1' : True,               }, ['-a']),
        ({               'a2' : False }, ['-b']),
        ({               'a2' : True  }, ['']),
        ({ 'a1' : False, 'a2' : True  }, ['']),
        ({ 'a1' : True,  'a2' : True  }, ['-a']),
        ({ 'a1' : False, 'a2' : False }, ['-b']),
        ({ 'a1' : False, 'a2' : True  }, ['']),
        ({ 'a1' : True,  'a2' : False }, ['-a -b', '-b -a']),
        ({ 'a1' : True,  'a2' : True  }, ['-a']),
    ]

    for kwargs, expected in tests:
        expected = [shlex.split(e) for e in expected]
        assert wutils.applyArgStyle(
            '-', argmap=argmap, valmap=valmap, **kwargs) in expected


def test_namedPositionals():
    def func1(): pass
    def func2(a, b, c): pass
    def func3(a, b, c, d=None, e=None): pass
    def func4(*args): pass
    def func5(*args, **kwargs): pass
    def func6(a, b, *args): pass
    def func7(a, b, *args, **kwargs): pass

    tests = [
        (func1, [],        []),
        (func2, [1, 2, 3], ['a', 'b', 'c']),
        (func3, [1, 2, 3], ['a', 'b', 'c']),
        (func4, [1, 2, 3], ['args0', 'args1', 'args2']),
        (func5, [1, 2, 3], ['args0', 'args1', 'args2']),
        (func6, [1, 2, 3], ['a', 'b', 'args0']),
        (func7, [1, 2, 3], ['a', 'b', 'args0']),
    ]

    for func, args, expected in tests:
        result = wutils.namedPositionals(func, args)
        assert list(result) == list(expected)

# TODO
#  - test _FileOrImage LOAD tuple order
