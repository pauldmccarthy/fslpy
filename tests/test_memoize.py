#!/usr/bin/env python
#
# test_memoize.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import collections
import six

import numpy as np

import fsl.utils.memoize as memoize


def test_memoize():

    timesCalled = [0]

    def thefunc(*args, **kwargs):
        timesCalled[0] += 1

        if   len(args) + len(kwargs) == 0: return 0
        elif len(args)               == 1: return args[0]         * 5
        else:                              return kwargs['value'] * 5

    memoized = memoize.memoize(thefunc)

    # No args
    for i in range(5):
        assert memoized() == 0
        assert timesCalled[0] == 1

    # Positional args
    for i in range(3):
        for i in range(5):
            assert memoized(i) == i * 5
        assert timesCalled[0] == 6

    # Keyword arg
    for i in range(3):
        for i in range(5):
            assert memoized(value=i) == i * 5
        assert timesCalled[0] == 6

    # Unicode arg
    s = six.u('\u25B2')
    assert memoized(s) == s * 5
    assert timesCalled[0] == 7
    assert memoized(s) == s * 5
    assert timesCalled[0] == 7


def test_memoize_create():

    timesCalled = {
        'without_brackets' : 0,
        'with_brackets'    : 0
    }

    @memoize.memoize
    def without_brackets():
        timesCalled['without_brackets'] += 1
        return 5

    @memoize.memoize()
    def with_brackets():
        timesCalled['with_brackets'] += 1
        return 10


    for i in range(10):
        assert without_brackets()              == 5
        assert with_brackets()                 == 10
        assert timesCalled['without_brackets'] == 1
        assert timesCalled['with_brackets']    == 1


def test_memoize_invalidate():

    timesCalled = collections.defaultdict(lambda: 0)

    @memoize.memoize
    def func(arg):
        timesCalled[arg] += 1
        return arg * 5


    for i in range(5):
        assert func(5)         == 25
        assert func(10)        == 50
        assert timesCalled[5]  == 1
        assert timesCalled[10] == 1

    func.invalidate()

    for i in range(5):
        assert func(5)         == 25
        assert func(10)        == 50
        assert timesCalled[5]  == 2
        assert timesCalled[10] == 2

    func.invalidate(5)
    for i in range(5):
        assert func(5)         == 25
        assert func(10)        == 50
        assert timesCalled[5]  == 3
        assert timesCalled[10] == 2

    func.invalidate(10)
    for i in range(5):
        assert func(5)         == 25
        assert func(10)        == 50
        assert timesCalled[5]  == 3
        assert timesCalled[10] == 3




def test_memoizeMD5():
    timesCalled = [0]

    def thefunc(*args, **kwargs):
        timesCalled[0] += 1
        if   len(args) + len(kwargs) == 0: return 0
        elif len(args)               == 1: return args[0]         * 5
        else:                              return kwargs['value'] * 5

    memoized = memoize.memoizeMD5(thefunc)

    # No args
    for i in range(5):
        assert memoized() == 0
        assert timesCalled[0] == 1

    # Positional args
    for i in range(3):
        for i in range(5):
            assert memoized(i) == i * 5
        assert timesCalled[0] == 6

    # Keyword arg
    for i in range(3):
        for i in range(5):
            assert memoized(value=i) == i * 5
        assert timesCalled[0] == 6

    # Unicode arg (and return value)
    s = six.u('\u25B2')
    assert memoized(s) == s * 5
    assert timesCalled[0] == 7
    assert memoized(s) == s * 5
    assert timesCalled[0] == 7


def test_skipUnchanged():
    """
    """

    timesCalled = collections.defaultdict(lambda: 0)

    def setter(name, value):
        timesCalled[name] = timesCalled[name] + 1

    wrapped = memoize.skipUnchanged(setter)

    wrapped('key1', 11)
    wrapped('key2', 12)
    wrapped('key3', 13)

    assert timesCalled['key1'] == 1
    assert timesCalled['key2'] == 1
    assert timesCalled['key3'] == 1

    wrapped('key1', 11)
    wrapped('key2', 12)
    wrapped('key3', 13)

    assert timesCalled['key1'] == 1
    assert timesCalled['key2'] == 1
    assert timesCalled['key3'] == 1

    wrapped('key1', 14)
    wrapped('key2', 15)
    wrapped('key3', 16)

    assert timesCalled['key1'] == 2
    assert timesCalled['key2'] == 2
    assert timesCalled['key3'] == 2

    wrapped('key1', 14)
    wrapped('key2', 15)
    wrapped('key3', 16)

    assert timesCalled['key1'] == 2
    assert timesCalled['key2'] == 2
    assert timesCalled['key3'] == 2

    wrapped('key1', 11)
    wrapped('key2', 12)
    wrapped('key3', 13)

    assert timesCalled['key1'] == 3
    assert timesCalled['key2'] == 3
    assert timesCalled['key3'] == 3

    wrapped('key1', np.array([11, 12]))
    wrapped('key2', np.array([13, 14]))
    wrapped('key3', np.array([15, 16]))

    assert timesCalled['key1'] == 4
    assert timesCalled['key2'] == 4
    assert timesCalled['key3'] == 4

    wrapped('key1', np.array([12, 11]))
    wrapped('key2', np.array([14, 13]))
    wrapped('key3', np.array([16, 15]))

    assert timesCalled['key1'] == 5
    assert timesCalled['key2'] == 5
    assert timesCalled['key3'] == 5

    wrapped('key1', np.array([12, 11]))
    wrapped('key2', np.array([14, 13]))
    wrapped('key3', np.array([16, 15]))

    assert timesCalled['key1'] == 5
    assert timesCalled['key2'] == 5
    assert timesCalled['key3'] == 5

    # Regression - zero
    # sized numpy arrays
    # could previously be
    # tested incorrectly
    # because e.g.
    #
    # np.all(np.zeros((0, 3)), np.ones((1, 3))
    #
    # evaluates to True
    wrapped('key4', np.zeros((0, 4)))
    assert timesCalled['key4'] == 1
    wrapped('key4', np.zeros((1, 4)))
    assert timesCalled['key4'] == 2




def test_Instanceify():

    class Container(object):

        def __init__(self):
            self.setter1Called = 0
            self.setter2Called = 0
            self.func1Called   = 0
            self.func2Called   = 0

        @memoize.Instanceify(memoize.skipUnchanged)
        def setter1(self, name, value):
            self.setter1Called += 1

        @memoize.Instanceify(memoize.skipUnchanged)
        def setter2(self, name, value):
            self.setter2Called += 1

        @memoize.Instanceify(memoize.memoize)
        def func1(self, arg):
            self.func1Called += 1
            return arg * 2

        @memoize.Instanceify(memoize.memoize)
        def func2(self, arg):
            self.func2Called += 1
            return arg * 4

        def check(self, s1c, s2c, f1c, f2c):
            assert self.setter1Called == s1c
            assert self.setter2Called == s2c
            assert self.func1Called   == f1c
            assert self.func2Called   == f2c

    c1 = Container()
    c2 = Container()

    # Call setter1 on one instance,
    # make sure that the call counter
    # only changes on that instance
    for i in range(3):
        c1.setter1('blob', 120)
        c1.check(1, 0, 0, 0)
        c2.check(0, 0, 0, 0)

    for i in range(3):
        c1.setter1('blob', 150)
        c1.check(2, 0, 0, 0)
        c2.check(0, 0, 0, 0)

    for i in range(3):
        c1.setter1('flob', 200)
        c1.check(3, 0, 0, 0)
        c2.check(0, 0, 0, 0)

    for i in range(3):
        c1.setter1('flob', 180)
        c1.check(4, 0, 0, 0)
        c2.check(0, 0, 0, 0)

    for i in range(3):
        c2.setter1('blob', 120)
        c1.check(4, 0, 0, 0)
        c2.check(1, 0, 0, 0)

    for i in range(3):
        c2.setter1('blob', 150)
        c1.check(4, 0, 0, 0)
        c2.check(2, 0, 0, 0)

    for i in range(3):
        c2.setter1('flob', 200)
        c1.check(4, 0, 0, 0)
        c2.check(3, 0, 0, 0)

    for i in range(3):
        c2.setter1('flob', 180)
        c1.check(4, 0, 0, 0)
        c2.check(4, 0, 0, 0)

    # Call setter2 on one instance,
    # ...
    for i in range(3):
        c1.setter2('blob', 120)
        c1.check(4, 1, 0, 0)
        c2.check(4, 0, 0, 0)

    for i in range(3):
        c1.setter2('blob', 150)
        c1.check(4, 2, 0, 0)
        c2.check(4, 0, 0, 0)

    for i in range(3):
        c1.setter2('flob', 200)
        c1.check(4, 3, 0, 0)
        c2.check(4, 0, 0, 0)

    for i in range(3):
        c1.setter2('flob', 180)
        c1.check(4, 4, 0, 0)
        c2.check(4, 0, 0, 0)

    for i in range(3):
        c2.setter2('blob', 120)
        c1.check(4, 4, 0, 0)
        c2.check(4, 1, 0, 0)

    for i in range(3):
        c2.setter2('blob', 150)
        c1.check(4, 4, 0, 0)
        c2.check(4, 2, 0, 0)

    for i in range(3):
        c2.setter2('flob', 200)
        c1.check(4, 4, 0, 0)
        c2.check(4, 3, 0, 0)

    for i in range(3):
        c2.setter2('flob', 180)
        c1.check(4, 4, 0, 0)
        c2.check(4, 4, 0, 0)

    # Call func1 on one instance,
    # ...
    for i in range(3):
        assert c1.func1(123) == 246
        c1.check(4, 4, 1, 0)
        c2.check(4, 4, 0, 0)

    for i in range(3):
        assert c1.func1(456) == 912
        c1.check(4, 4, 2, 0)
        c2.check(4, 4, 0, 0)

    for i in range(3):
        assert c2.func1(123) == 246
        c1.check(4, 4, 2, 0)
        c2.check(4, 4, 1, 0)

    for i in range(3):
        assert c2.func1(456) == 912
        c1.check(4, 4, 2, 0)
        c2.check(4, 4, 2, 0)

    # Call func2 on one instance,
    # ...
    for i in range(3):
        assert c1.func2(123) == 492
        c1.check(4, 4, 2, 1)
        c2.check(4, 4, 2, 0)

    for i in range(3):
        assert c1.func2(456) == 1824

    for i in range(3):
        assert c2.func2(123) == 492
        c1.check(4, 4, 2, 2)
        c2.check(4, 4, 2, 1)

    for i in range(3):
        assert c2.func2(456) == 1824
        c1.check(4, 4, 2, 2)
        c2.check(4, 4, 2, 2)
