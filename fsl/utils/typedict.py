#!/usr/bin/env python
#
# typedict.py - Provides the TypeDict class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


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


    def __str__( self): return self.__dict.__str__()
    def __repr__(self): return self.__dict.__repr__()
    def keys(    self): return self.__dict.keys()
    def values(  self): return self.__dict.values()
    def items(   self): return self.__dict.items()

    def __setitem__(self, key, value):
        self.__dict[self.__tokenifyKey(key)] = value


    def __tokenifyKey(self, key):
        
        if isinstance(key, basestring) and '.' in key:
            return tuple(key.split('.'))

        return key

        
    def get(self, key, default=None, allhits=False, bykey=False):
        """Retrieve the value associated with the given key. If
        no value is present, return the specified ``default`` value,
        which itself defaults to ``None``.

        If the specified key contains a class or instance, and the
        ``allhits`` argument evaluates to ``True``, the entire class
        hierarchy is searched, and all values present for the class,
        and any base class, are returned as a sequence.

        If ``allhits`` is ``True`` and the ``bykey`` parameter is also
        set to ``True``, a dictionary is returned rather than a sequence,
        where the dictionary contents are the subset of this dictionary,
        containing the keys which equated to the given key, and their
        corresponding values.
        """

        try:             return self.__getitem__(key, allhits, bykey)
        except KeyError: return default

        
    def __getitem__(self, key, allhits=False, bykey=False):
        
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

        key  = newKey

        keys = []
        hits = []
            
        while True:

            # If the key was not a tuple turn
            # it back into a single element key
            # for the lookup
            if len(key) == 1: lKey = key[0]
            else:             lKey = tuple(key)

            val = self.__dict.get(lKey, None)

            # We've found a value for the key
            if val is not None:

                # If allhits is false, just return the value
                if not allhits: return val

                # Otherwise, accumulate the value, and keep
                # searching
                else:
                    hits.append(val)
                    if bykey:
                        keys.append(lKey)

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

                    if len(newKey) == 1: newKey = newKey[0]
                    else:                newKey = tuple(newKey)

                    try:
                        newVal = self.__getitem__(newKey, allhits, bykey)
                    except KeyError:
                        continue

                    if not allhits:
                        return newVal
                    else:
                        if bykey:
                            newKeys, newVals = zip(*newVal.items())
                            keys.extend(newKeys)
                            hits.extend(newVals)
                        else:
                            hits.extend(newVal)

            # No value for any base classes either
            if len(hits) == 0:
                raise KeyError(origKey)

            # if bykey is true, return a dict
            # containing the values and their
            # corresponding keys
            if bykey:
                return dict(zip(keys, hits))

            # otherwise just return the
            # list of matched values
            else:
                return hits
