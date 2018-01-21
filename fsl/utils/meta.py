#!/usr/bin/env python
#
# meta.py - The Meta class/mixin.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Meta` class. """


import collections


class Meta(object):
    """The ``Meta`` class is intended to be used as a mixin for other classes. It
    is simply a wrapper for a dictionary of key-value pairs.

    It has a handful of methods allowing you to add and access additional
    metadata associated with an object.

    .. autosummary::
       :nosignatures:

       metaKeys
       metaValues
       metaItems
       getMeta
       setMeta
    """

    def __new__(cls, *args, **kwargs):
        """Initialises a ``Meta`` instance. """

        new        = super(Meta, cls).__new__(cls)
        new.__meta = collections.OrderedDict()

        return new


    def metaKeys(self):
        """Returns the keys contained in the metadata dictionary
        (``dict.keys``).
        """
        return self.__meta.keys()


    def metaValues(self):
        """Returns the values contained in the metadata dictionary
        (``dict.values``).
        """
        return self.__meta.values()


    def metaItems(self):
        """Returns the items contained in the metadata dictionary
        (``dict.items``).
        """
        return self.__meta.items()


    def getMeta(self, *args, **kwargs):
        """Returns the metadata value with the specified key (``dict.get``).
        """
        return self.__meta.get(*args, **kwargs)


    def setMeta(self, *args, **kwargs):
        """Add some metadata with the specified key (``dict.__setitem__``).
        """
        self.__meta.__setitem__(*args, **kwargs)
