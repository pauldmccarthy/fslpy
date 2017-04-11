#!/usr/bin/env python
#
# test_typedict.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import itertools as it
import pytest

import fsl.utils.typedict as typedict


def test_create():
    
    td = typedict.TypeDict()


    assert len(td)          == 0
    assert len(td.keys())   == 0
    assert len(td.values()) == 0
    assert len(td.items())  == 0

    keys   = [0,
              1,
              2,
              'a',
              'b',
              'c',
              'a.b',
              'a.b.c',
              ('a', 'c'),
              ('a',  0)]
    values = list(range(len(keys)))
    
    td = typedict.TypeDict(        dict(zip(keys, values)))
    td = typedict.TypeDict(initial=dict(zip(keys, values)))

    print(     td)
    print(repr(td))

    tknkeys = [td.tokenifyKey(k) for k in keys]

    assert len(td)                   == len(keys)
    assert list(sorted(td.keys()))   == list(sorted(tknkeys))
    assert list(sorted(td.values())) == list(sorted(values))
    assert list(sorted(td.items()))  == list(sorted(zip(tknkeys, values)))

    for k, v in zip(keys, values):
        assert td[k] == v

    with pytest.raises(KeyError):
        td['non-existent']

    assert td.get('non-existent') is None
    assert td.get('non-existent', 'default') == 'default'


def test_class_keys():

    class A(object):
        pass

    class B(object):
        pass

    class C(object):
        pass

    td = typedict.TypeDict()

    a  = A()
    b  = B()
    c  = C()

    # TypeDict [currently] does not allow value
    # assignment with classes/instances as keys -
    # we must use the class name, encoded as a
    # string, when assigning.
    keycomponents = ['A', 'B', 'C', 'att1', 'att2', 'att3']
    keys          = list(it.chain(it.permutations(keycomponents, 1),
                                  it.permutations(keycomponents, 2),
                                  it.permutations(keycomponents, 3),
                                  it.permutations(keycomponents, 4),
                                  it.permutations(keycomponents, 5),
                                  it.permutations(keycomponents, 6)))

    for val, key in enumerate(keys):
        if len(key) == 1: td[key[0]] = val
        else:             td[key]    = val

    for val, key in enumerate(keys):

        # Keys can be passed as tuples
        assert td[key] == val

        # Or as dot-separated strings
        assert td['.'.join(key)] == val

        # But when accessing items,
        # we can use either class names,
        # classes, or instances.
        for toReplace in it.chain(it.combinations(['A', 'B', 'C'], 1),
                                  it.combinations(['A', 'B', 'C'], 2),
                                  it.combinations(['A', 'B', 'C'], 3)):

            clsrep  = {'A' : A, 'B' : B, 'C' : C}
            instrep = {'A' : a, 'B' : b, 'C' : c}

            # use class instead of name
            repkey = [clsrep[k] if k in toReplace else k for k in key]
            assert td[repkey] == val

            # use instance instead of name
            repkey = [instrep[k] if k in toReplace else k for k in key]
            assert td[repkey] == val


def test_class_hierarchy():

    class A(object):
        pass

    class B(A):
        pass

    td = typedict.TypeDict()
    td['A.a'] = 'A.a'
    td['A.b'] = 'A.b'
    td['A.c'] = 'A.c'
    td['A.d'] = 'A.d'
    td['B.a'] = 'B.a'
    td['B.b'] = 'B.b'
    td['B.1'] = 'B.1'
    td['B.2'] = 'B.2'

    a = A()
    b = B()
    
    assert td[A, 'a'] == 'A.a'
    assert td[A, 'b'] == 'A.b'
    assert td[A, 'c'] == 'A.c'
    assert td[A, 'd'] == 'A.d'
    
    assert td['A.a']  == 'A.a'
    assert td['A.b']  == 'A.b'
    assert td['A.c']  == 'A.c'
    assert td['A.d']  == 'A.d'
    
    assert td.get((A, 'a')) == 'A.a'
    assert td.get((A, 'b')) == 'A.b'
    assert td.get((A, 'c')) == 'A.c'
    assert td.get((A, 'd')) == 'A.d' 
    
    assert td.get((A, 'a'), allhits=True) == ['A.a']
    assert td.get((A, 'b'), allhits=True) == ['A.b']
    assert td.get((A, 'c'), allhits=True) == ['A.c']
    assert td.get((A, 'd'), allhits=True) == ['A.d']
    
    assert td.get((a, 'a'), allhits=True) == ['A.a']
    assert td.get((a, 'b'), allhits=True) == ['A.b']
    assert td.get((a, 'c'), allhits=True) == ['A.c']
    assert td.get((a, 'd'), allhits=True) == ['A.d']

    assert td[B, 'a'] == 'B.a'
    assert td[B, 'b'] == 'B.b'
    assert td[B, '1'] == 'B.1'
    assert td[B, '2'] == 'B.2'
    
    assert td['B.a']  == 'B.a'
    assert td['B.b']  == 'B.b'
    assert td['B.1']  == 'B.1'
    assert td['B.2']  == 'B.2'
    
    assert td.get('B.a') == 'B.a'
    assert td.get('B.b') == 'B.b'
    assert td.get('B.1') == 'B.1'
    assert td.get('B.2') == 'B.2'

    assert td.get((B, 'a')) == 'B.a'
    assert td.get((B, 'b')) == 'B.b'
    assert td.get((B, '1')) == 'B.1'
    assert td.get((B, '2')) == 'B.2'
    assert td.get((b, 'a')) == 'B.a'
    assert td.get((b, 'b')) == 'B.b'
    assert td.get((b, '1')) == 'B.1'
    assert td.get((b, '2')) == 'B.2'

    with pytest.raises(KeyError):
        td['B.c']
    with pytest.raises(KeyError):
        td['B.d']

    assert td[B, 'c'] == 'A.c'
    assert td[B, 'd'] == 'A.d'
    assert td[b, 'c'] == 'A.c'
    assert td[b, 'd'] == 'A.d' 
    
    assert td.get('B.a',    allhits=True) == ['B.a']
    assert td.get('B.b',    allhits=True) == ['B.b']
    assert td.get('B.1',    allhits=True) == ['B.1']
    assert td.get('B.2',    allhits=True) == ['B.2'] 
    assert td.get((B, 'a'), allhits=True) == ['B.a', 'A.a']
    assert td.get((B, 'b'), allhits=True) == ['B.b', 'A.b']
    assert td.get((B, '1'), allhits=True) == ['B.1']
    assert td.get((B, '2'), allhits=True) == ['B.2']
    assert td.get((B, 'c'), allhits=True) == ['A.c']
    assert td.get((B, 'd'), allhits=True) == ['A.d'] 
    
    assert td.get((b, 'a'), allhits=True) == ['B.a', 'A.a']
    assert td.get((b, 'b'), allhits=True) == ['B.b', 'A.b']
    assert td.get((b, '1'), allhits=True) == ['B.1']
    assert td.get((b, '2'), allhits=True) == ['B.2']
    assert td.get((b, 'c'), allhits=True) == ['A.c']

    assert td.get((B, 'a'), allhits=False, bykey=True) == 'B.a'
    assert td.get((B, 'b'), allhits=False, bykey=True) == 'B.b'
    assert td.get((B, '1'), allhits=False, bykey=True) == 'B.1'
    assert td.get((B, '2'), allhits=False, bykey=True) == 'B.2'
    
    assert td.get((B, 'a'), allhits=True,  bykey=True) == {('A', 'a') : 'A.a',
                                                           ('B', 'a') : 'B.a'}
    assert td.get((B, 'b'), allhits=True,  bykey=True) == {('A', 'b') : 'A.b',
                                                           ('B', 'b') : 'B.b'}
    assert td.get((B, '1'), allhits=True,  bykey=True) == {('B', '1') : 'B.1'}
    assert td.get((B, '2'), allhits=True,  bykey=True) == {('B', '2') : 'B.2'}
    assert td.get((B, 'c'), allhits=True,  bykey=True) == {('A', 'c') : 'A.c'}
    assert td.get((B, 'd'), allhits=True,  bykey=True) == {('A', 'd') : 'A.d'} 
    
    assert td.get((b, 'a'), allhits=True,  bykey=True) == {('A', 'a') : 'A.a',
                                                           ('B', 'a') : 'B.a'}
    assert td.get((b, 'b'), allhits=True,  bykey=True) == {('A', 'b') : 'A.b',
                                                           ('B', 'b') : 'B.b'}
    assert td.get((b, '1'), allhits=True,  bykey=True) == {('B', '1') : 'B.1'}
    assert td.get((b, '2'), allhits=True,  bykey=True) == {('B', '2') : 'B.2'}
    assert td.get((b, 'c'), allhits=True,  bykey=True) == {('A', 'c') : 'A.c'}
    assert td.get((b, 'd'), allhits=True,  bykey=True) == {('A', 'd') : 'A.d'} 
    
    assert td.get((A, 'a'), allhits=True,  bykey=True) == {('A', 'a') : 'A.a'}
    assert td.get((A, 'b'), allhits=True,  bykey=True) == {('A', 'b') : 'A.b'}
    assert td.get((A, 'c'), allhits=True,  bykey=True) == {('A', 'c') : 'A.c'}
    assert td.get((A, 'd'), allhits=True,  bykey=True) == {('A', 'd') : 'A.d'} 
