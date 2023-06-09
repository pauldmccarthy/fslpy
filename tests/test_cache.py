#!/usr/bin/env python
#
# test_cache.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import time
import pytest

import fsl.utils.cache as cache


def test_dropOldest():
    sz = 10
    c  = cache.Cache(maxsize=sz)

    # Fill the cache
    for i in range(sz):
        c.put(i, str(i))

        assert len(c) == i + 1

    # Add an item for an existing key -
    # no items should be dropped
    c.put(0, 'New value!')
    assert c.get(0) == 'New value!'
    for i in range(1, sz):
        assert c.get(i) == str(i)

    # Add some more items - the first
    # items should be dropped
    for i in range(sz, sz + 5):
        c.put(i, str(i))

        assert len(c) == sz

    # Check that they've been dropped
    for i in range(5):
        with pytest.raises(KeyError):
            c.get(i)

    # Check that the new items are there
    for i in range(5, sz + 5):
        assert c.get(i) == str(i)


def test_clear():
    sz = 10
    c  = cache.Cache(maxsize=sz)

    # Put some items in
    for i in range(sz):
        c.put(i, str(i))

    # Make sure they're there
    for i in range(sz):
        assert c.get(i) == str(i)

    # Drop them all
    c.clear()

    # Make sure they've been dropped
    assert len(c) == 0

    for i in range(sz):
        with pytest.raises(KeyError):
            c.get(i)


def test_getitem_setitem():
    c = cache.Cache()
    c['abc'] = 123
    assert c.get('abc') == 123
    c.put(123, 'abc')
    assert c[123] == 'abc'

    with pytest.raises(KeyError):
        c['notakey']


def test_getdefault():
    c = cache.Cache()

    assert c.get('non_existent',         'default') == 'default'
    assert c.get('non_existent', default='default') == 'default'

    with pytest.raises(KeyError):
        c.get('non_existent')

    with pytest.raises(ValueError):
        c.get('non_existent', 'default',        'badarg')
        c.get('non_existent', 'default', badarg='badarg')
        c.get('non_existent', 'badarg', default='default')
        c.get('non_existent', default='default', badarg='badarg')


def test_expiry():
    c = cache.Cache()

    # Put some items in, with short expiry times
    c.put(0, '0', expiry=1)
    c.put(1, '1', expiry=1)

    # Make sure we can get them
    assert c.get(0) == '0'
    assert c.get(1) == '1'

    # Wait until they should have expired
    time.sleep(1.1)

    # Check that the cache has expired
    with pytest.raises(cache.Expired):
        c.get(0)

    with pytest.raises(cache.Expired):
        c.get(1)

    assert c.get(1, default='default') == 'default'

    # And that the cache is empty
    assert len(c) == 0


def test_lru():
    c = cache.Cache(maxsize=3, lru=True)

    c[0] = '0'
    c[1] = '1'
    c[2] = '2'
    c[3] = '3'

    # normal behaviour - first inserted
    # is dropped
    with pytest.raises(KeyError):
        assert c.get(0)

    # lru behaviour - oldest accessed is
    # dropped
    c[1]
    c[4] = '4'
    with pytest.raises(KeyError):
        c[2]

    c[1]
    c[3]
    c[4]
    assert len(c) == 3



def test_accessors():
    c = cache.Cache(maxsize=3)

    c[0] = '0'
    c[1] = '1'
    c[2] = '2'
    c[3] = '3'

    assert list(c.keys())   == [ 1,        2,        3]
    assert list(c.values()) == ['1',      '2',      '3']
    assert list(c.items())  == [(1, '1'), (2, '2'), (3, '3')]

    assert 0 not in c
    assert 1     in c
    assert 2     in c
    assert 3     in c
