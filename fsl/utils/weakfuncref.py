#!/usr/bin/env python
#
# weakfuncref.py - The WeakFunctionRef class
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`WeakFunctionRef` class. """


import types
import weakref
import inspect


class WeakFunctionRef:
    """Class which encapsulates a :mod:`weakref` to a function or method.

    This class is used by :class:`.Notifier` instances to reference
    listeners which have been registered to be notified of property value
    or attribute changes.
    """


    def __init__(self, func):
        """Create a new ``WeakFunctionRef`` to encapsulate the given
        function or bound/unbound method.
        """

        # Bound method
        if inspect.ismethod(func):

            boundMeth = func.__func__
            boundSelf = func.__self__

            # We can't take a weakref of the method
            # object, so we have to weakref the object
            # and the unbound class function. The
            # function method will search for and
            # return the bound method, though.
            self.obj  = weakref.ref(boundSelf)
            self.func = weakref.ref(boundMeth)

            self.objType  = type(boundSelf).__name__
            self.funcName =      boundMeth .__name__

        # Unbound/class method or function
        else:

            self.obj      = None
            self.objType  = None
            self.func     = weakref.ref(func)
            self.funcName = func.__name__


    def __str__(self):
        """Return a string representation of the function."""

        selftype = type(self).__name__
        func     = self.function()

        if self.obj is None:
            s = '{}: {}'   .format(selftype, self.funcName)
        else:
            s = '{}: {}.{}'.format(selftype, self.objType, self.funcName)

        if func is None: return '{} <dead>'.format(s)
        else:            return s


    def __repr__(self):
        """Return a string representation of the function."""
        return self.__str__()



    def __findPrivateMethod(self):
        """Finds and returns the bound method associated with the encapsulated
        function.
        """

        obj      = self.obj()
        func     = self.func()
        methName = self.funcName

        # Find all attributes on the object which end with
        # the method name - there will be more than one of
        # these if the object has base classes which have
        # private methods of the same name.
        attNames = dir(obj)
        attNames = [a for a in attNames if a.endswith(methName)]

        # Find the attribute with the correct name, which
        # is a method, and has the correct function.
        for name in attNames:

            att = getattr(obj, name)

            if isinstance(att, types.MethodType) and att.__func__ is func:
                return att

        return None


    def __call__(self):
        """See :meth:``function``. """
        return self.function()


    def function(self):
        """Return a reference to the encapsulated function or method,
        or ``None`` if the function has been garbage collected.
        """

        # Unbound/class method or function
        if self.obj is None:
            return self.func()

        # The instance owning the method has been destroyed
        if self.obj() is None or self.func() is None:
            return None

        obj = self.obj()

        # Return the bound method object
        try: return getattr(obj, self.funcName)

        # If the function is a bound private method,
        # its name on the instance will have been
        # mangled, so we need to search for it
        except AttributeError: return self.__findPrivateMethod()
