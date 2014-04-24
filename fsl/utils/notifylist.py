#!/usr/bin/env python
#
# notifylist.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import collections
import logging
import unittest

log = logging.getLogger(__name__)

class NotifyList(object):
    """
    """

    def __init__(self, items=None, validateFunc=None):
        """
        """
        
        if items        is None: items = []
        if validateFunc is None: validateFunc = lambda v: v
        
        if not isinstance(items, collections.Iterable):
            raise TypeError('items must be a sequence')

        map(validateFunc, items)

        self._validate  = validateFunc
        self._items     = items
        self._listeners = []

        
    def __len__     (self):        return self._items.__len__()
    def __getitem__ (self, key):   return self._items.__getitem__(key)
    def __iter__    (self):        return self._items.__iter__()
    def __contains__(self, item):  return self._items.__contains__(item)
    def __eq__      (self, other): return self._items.__eq__(other)
    def __str__     (self):        return self._items.__str__()
    def __repr__    (self):        return self._items.__repr__()

        
    def append(self, item):
        self._validate(item)

        log.debug('Item appended: {}'.format(item))
        self._items.append(item)
        self._notify()

        
    def pop(self, index=-1):
        
        item = self._items.pop(index)
        log.debug('Item popped: {} (index {})'.format(item, index))
        self._notify()
        return item

        
    def insert(self, index, item):
        self._validate(item)
        self._items.insert(index, item)
        log.debug('Item inserted: {} (index {})'.format(item, index))
        self._notify()


    def extend(self, items):
        map(self._validate, items)
        self._items.extend(items)
        log.debug('List extended: {}'.format(', '.join([str(i) for i in item])))
        self._notify()


    def move(self, from_, to):
        """
        Move the item from 'from_' to 'to'. 
        """

        item = self._items.pop(from_)
        self._items.insert(to, item)
        log.debug('Item moved: {} (from: {} to: {})'.format(item, from_, to))
        self._notify()

        
    def addListener   (self, listener): self._listeners.append(listener)
    def removeListener(self, listener): self._listeners.remove(listener)
    def _notify       (self):
        for listener in self._listeners:
            try:
                listener(self)
            except e:
                log.debug('Listener raised exception: {}'.format(e.message))
 

class TestNotifyList(unittest.TestCase):

    def setUp(self):
        self.listlen = 5
        self.thelist = NotifyList(range(self.listlen))

    def test_move(self):

        for i in range(self.listlen):
            for j in range(self.listlen):

                self.setUp()
                self.thelist.move(i, j)

                demo = range(self.listlen)

                val = demo.pop(i)
                demo.insert(j, val)

                print '{} -> {}: {} <-> {}'.format(i, j, self.thelist, demo)
        
                self.assertEqual(self.thelist, demo)
