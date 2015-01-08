#!/usr/bin/env python
#
# typedict.py - Provides the TypeDict class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


class TypeDict(object):
    """A custom dictionary which allows classes or class instances to be used
    as keys for value lookups, but internally transforms any class/instance
    keys into strings. Tuple keys are supported. Value assignment with
    class/instance keys is not supported.

    If a class/instance is passed in as a key, and there is no value
    associated with that class, a search is performed on all of the base
    classes of that class to see if any values are present for them.
    """

    def __init__(self, initial=None):
        
        if initial is None:
            initial = {}
        
        self.__dict = {}

        for k, v in initial.items():
            self[k] = v


    def __setitem__(self, key, value):
        self.__dict[self.__tokenifyKey(key)] = value


    def __tokenifyKey(self, key):
        
        if isinstance(key, basestring) and '.' in key:
            return tuple(key.split('.'))

        return key

        
    def get(self, key, default):
        try:             return self.__getitem__(key)
        except KeyError: return default

        
    def __getitem__(self, key):
        
        origKey = key
        key     = self.__tokenifyKey(key)
        bases   = []

        # Make the code a bit easier by
        # treating non-tuple keys as tuples
        if not isinstance(key, tuple):
            key = tuple([key])

        newKey = []

        # Transform any class/instance elements into
        # their string representation (the class name)
        for elem in key:
            
            if isinstance(elem, type):
                newKey.append(elem.__name__)
                bases .append(elem.__bases__)
                
            elif not isinstance(elem, (str, int)):
                newKey.append(elem.__class__.__name__)
                bases .append(elem.__class__.__bases__)
                
            else:
                newKey.append(elem)
                bases .append(None)

        key = newKey
            
        while True:

            # If the key was not a tuple turn
            # it back into a single element key
            # for the lookup
            if len(key) == 1: lKey = key[0]
            else:             lKey = tuple(key)

            val = self.__dict.get(lKey, None)
            
            if val is not None:
                return val

            # No more base classes to search for - there
            # really is no value associated with this key
            elif all([b is None for b in bases]):
                raise KeyError(key)

            # Search through the base classes to see
            # if a value is present for one of them
            for i, (elem, elemBases) in enumerate(zip(key, bases)):
                if elemBases is None:
                    continue

                # test each of the base classes 
                # of the current tuple element
                for elemBase in elemBases:

                    newKey    = list(key)
                    newKey[i] = elemBase

                    try:
                        return self.__getitem__(tuple(newKey))
                    except KeyError:
                        continue

            # No value for any base classes either
            raise KeyError(origKey)