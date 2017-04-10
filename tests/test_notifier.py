#!/usr/bin/env python
#
# test_notifier.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import pytest

import fsl.utils.notifier as notifier


def test_normal_usage():

    class Thing(notifier.Notifier):
        pass

    t = Thing()

    default_called = []
    topic_called   = []

    def default_callback(thing, topic, value):
        default_called.append((thing, topic, value))
    
    def topic_callback(thing, topic, value):
        topic_called.append((thing, topic, value)) 

    t.register('default_callback', default_callback)
    t.register('topic_callback',   topic_callback, topic='topic')

    with pytest.raises(notifier.Registered):
        t.register('default_callback', default_callback)
    with pytest.raises(notifier.Registered):
        t.register('topic_callback',   topic_callback, topic='topic') 

    t.notify()
    t.notify(value='value')
    t.notify(topic='topic')
    t.notify(topic='topic', value='value')

    # Invalid names are ignored when deregistering
    t.deregister('default_callback')
    t.deregister('default_callback')
    t.deregister('topic_callback', topic='topic')
    t.deregister('topic_callback', topic='topic')

    t.notify()
    t.notify(value='value')
    t.notify(topic='topic')
    t.notify(topic='topic', value='value') 

    assert len(default_called) == 4
    assert len(topic_called)   == 2

    assert default_called[0] == (t,  None,    None)
    assert default_called[1] == (t,  None,   'value')
    assert default_called[2] == (t, 'topic',  None)
    assert default_called[3] == (t, 'topic', 'value')
    assert topic_called[  0] == (t, 'topic',  None)
    assert topic_called[  1] == (t, 'topic', 'value')


def test_enable_disable():
    
    class Thing(notifier.Notifier):
        pass

    t = Thing()
    
    default_called = [0]
    topic_called   = [0]

    def default_callback(*a):
        default_called[0] += 1
    
    def topic_callback(*a):
        topic_called[0] += 1

    t.register('default_callback', default_callback)
    t.register('topic_callback',   topic_callback, topic='topic')
    
    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 2
    assert topic_called[  0] == 1

    t.disable('default_callback')
    assert     t.isEnabled('topic_callback', topic='topic')
    assert not t.isEnabled('default_callback')
    t.notify()
    t.notify(topic='topic')
    t.enable('default_callback')
    assert default_called[0] == 2
    assert topic_called[  0] == 2 

    t.disable('topic_callback', topic='topic')
    assert not t.isEnabled('topic_callback', topic='topic')
    assert     t.isEnabled('default_callback')
    t.notify()
    t.notify(topic='topic')
    t.enable('topic_callback', topic='topic')
    assert default_called[0] == 4
    assert topic_called[  0] == 2

    assert t.isEnabled('topic_callback', topic='topic')
    assert t.isEnabled('default_callback') 
    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 6
    assert topic_called[  0] == 3

    t.disableAll()
    assert not t.isAllEnabled()
    t.notify()
    t.notify(topic='topic')
    t.enableAll()
    assert default_called[0] == 6
    assert topic_called[  0] == 3 

    t.disableAll('topic')
    assert not t.isAllEnabled('topic')
    t.notify()
    t.notify(topic='topic')
    t.enableAll()
    assert default_called[0] == 8
    assert topic_called[  0] == 3 


def test_skip():
    
    class Thing(notifier.Notifier):
        pass

    t = Thing()

    default_called = [0]
    topic_called   = [0]

    def default_callback(*a):
        default_called[0] += 1
    
    def topic_callback(*a):
        topic_called[0] += 1
 
    t.register('default_callback', default_callback)
    t.register('topic_callback',   topic_callback, topic='topic')
    
    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 2
    assert topic_called[  0] == 1

    with t.skip('default_callback'):
        t.notify()
        t.notify(topic='topic')
        
    assert default_called[0] == 2
    assert topic_called[  0] == 2

    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 4
    assert topic_called[  0] == 3 

    with t.skip('topic_callback', 'topic'):
        t.notify()
        t.notify(topic='topic')
    assert default_called[0] == 6
    assert topic_called[  0] == 3

    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 8
    assert topic_called[  0] == 4 
 
    with t.skipAll():
        t.notify()
        t.notify(topic='topic')
    assert default_called[0] == 8
    assert topic_called[  0] == 4
    
    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 10
    assert topic_called[  0] == 5

 
    with t.skipAll('topic'):
        t.notify()
        t.notify(topic='topic')
    assert default_called[0] == 12
    assert topic_called[  0] == 5
    
    t.notify()
    t.notify(topic='topic')
    assert default_called[0] == 14
    assert topic_called[  0] == 6
