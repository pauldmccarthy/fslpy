#!/usr/bin/env python
#
# test_weakfuncref.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.utils.weakfuncref as weakfuncref


def make_weakfuncref_that_will_get_gcd():

    def thefunc():
        pass

    return weakfuncref.WeakFunctionRef(thefunc)

def make_weakfuncref_method_that_will_get_gcd():

    class Thing(object):
        def method(self):
            pass

    return weakfuncref.WeakFunctionRef(Thing.method)


def test_weakfuncref_call():

    def func():
        pass

    non_gcd_func = weakfuncref.WeakFunctionRef(func)
    gcd_func     = make_weakfuncref_that_will_get_gcd()

    assert gcd_func()     is None
    assert non_gcd_func() is func


def test_weakfuncref_function():

    def func():
        pass

    non_gcd_func = weakfuncref.WeakFunctionRef(func)
    gcd_func     = make_weakfuncref_that_will_get_gcd()

    assert gcd_func.function()     is None
    assert non_gcd_func.function() is func


def test_weakfuncref_method():

    class Thing(object):
        def method(self):
            return 'existent!'

        def __priv_method(self):
            return 'existent!'

        @classmethod
        def clsmethod(clsself):
            return 'existent!'


    t = Thing()

    gcd_methref = make_weakfuncref_that_will_get_gcd()
    methref     = weakfuncref.WeakFunctionRef(t.method)
    privmethref = weakfuncref.WeakFunctionRef(t._Thing__priv_method)
    clsmethref  = weakfuncref.WeakFunctionRef(t.clsmethod)

    assert gcd_methref.function()   is None
    assert privmethref.function()() == 'existent!'
    assert methref    .function()() == 'existent!'
    assert clsmethref .function()() == 'existent!'

    print(gcd_methref)
    print(methref)

    t = None

    assert methref    .function()   is None
    assert privmethref.function()   is None
    assert clsmethref .function()() == 'existent!'
