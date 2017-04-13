#!/usr/bin/env python
#
# test_async.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import time
import threading
import random

import pytest

import fsl.utils.async as async
from fsl.utils.platform import platform as fslplatform


def _run_with_wx(func, *args, **kwargs):

    propagateRaise = kwargs.pop('propagateRaise', True)
    startingDelay  = kwargs.pop('startingDelay',  500)
    finishingDelay = kwargs.pop('finishingDelay', 500)
    
    import wx 

    result = [None]
    raised = [None]
    app    = wx.App()
    frame  = wx.Frame(None)
    
    def wrap():

        try:
            result[0] = func(*args, **kwargs)

        except Exception as e:
            print(e)
            raised[0] = e

        finally:
            def finish():
                frame.Destroy()
                app.ExitMainLoop() 
            wx.CallLater(finishingDelay, finish)
    
    frame.Show()

    wx.CallLater(startingDelay, wrap)

    app.MainLoop()
    async.idleReset()

    if raised[0] and propagateRaise:
        raise raised[0]
        
    return result[0]


def _wait_for_idle_loop_to_clear():

    if fslplatform.haveGui:
        import wx
        idleDone = [False]

        def busywait():
            idleDone[0] = True

        async.idle(busywait)

        while not idleDone[0]:
            wx.Yield()


def  test_run_with_gui():    _run_with_wx(_test_run)
def  test_run_without_gui(): _test_run()
def _test_run():

    taskRun        = [False]
    onFinishCalled = [False]
    onErrorCalled  = [False]

    def task():
        taskRun[0] = True

    def errtask():
        taskRun[0] = True 
        raise Exception('Task crashed!')

    def onFinish():
        onFinishCalled[0] = True

    def onError(e):
        onErrorCalled[0] = True

    t = async.run(task)

    if t is not None:
        t.join()

    assert taskRun[0]

    taskRun[0] = False

    t = async.run(task, onFinish, onError)

    if t is not None:
        t.join()

    _wait_for_idle_loop_to_clear()

    taskRun[       0] = False
    onFinishCalled[0] = False
    
    t = async.run(errtask, onFinish, onError)

    if t is not None:
        t.join()

    _wait_for_idle_loop_to_clear()

    assert     taskRun[       0]
    assert not onFinishCalled[0]
    assert     onErrorCalled[ 0]


def test_idle():

    called = [False]

    def task(arg, kwarg1=None):
        called[0] = arg == 1 and kwarg1 == 2

    def errtask(arg, kwarg1=None):
        raise Exception('Task crashed!')

    assert async.getIdleTimeout() > 0

    # Run directly
    async.idle(task, 1, kwarg1=2, name='direct')
    assert called[0]

    called[0] = False

    # Run on wx idle loop
    _run_with_wx(async.idle, task, 1, kwarg1=2)
    assert called[0]

    # Run a crashing task directly
    with pytest.raises(Exception):
        async.idle(errtask)

    # Run a crashing task on idle loop - error should not propagate
    _run_with_wx(async.idle, errtask)


def test_inidle():

    called = [False]
    name   = 'mytask'

    def task():
        called[0] = True

    def queuetask():

        async.idle(task, after=0.01, name=name)
        assert async.inIdle(name)

    _run_with_wx(queuetask)

    assert called[0]


def test_cancelidle():

    called = [False]
    name   = 'mytask'

    def task():
        called[0] = True

    def queuetask():

        async.idle(task, after=0.01, name=name)
        async.cancelIdle(name)

    _run_with_wx(queuetask)

    assert not called[0]


def test_idle_skipIfQueued():

    task1called = [False]
    task2called = [False]
    name        = 'mytask'

    def task1():
        task1called[0] = True

    def task2():
        task2called[0] = True

    def queuetask():

        async.idle(task1, after=0.01, name=name)
        async.idle(task2, after=0.01, name=name, skipIfQueued=True)

    _run_with_wx(queuetask)

    assert     task1called[0]
    assert not task2called[0]


def test_idle_dropIfQueued():

    task1called = [False]
    task2called = [False]
    name        = 'mytask'

    def task1():
        task1called[0] = True

    def task2():
        task2called[0] = True

    def queuetask():

        async.idle(task1, after=0.01, name=name)
        async.idle(task2, after=0.01, name=name, dropIfQueued=True)

    _run_with_wx(queuetask)

    assert not task1called[0]
    assert     task2called[0]


def test_idle_alwaysQueue():

    called = [False]

    def task():
        called[0] = True

    def nop():
        pass

    async.idle(task, alwaysQueue=True)

    # We need to queue another task
    # for the first task to be executed
    _run_with_wx(async.idle, nop)

    assert called[0]


def test_idle_timeout():

    called = [False]

    def task():
        called[0] = True

    _run_with_wx(async.idle, task, timeout=0.0000000000000001)

    assert not called[0]



def test_idleWhen():

    called      = [False]
    timesPolled = [0]

    def condition():
        timesPolled[0] += 1
        return timesPolled[0] == 50

    def task():
        called[0] = True

    async.setIdleTimeout(1)

    _run_with_wx(async.idleWhen, task, condition, pollTime=0.001)

    assert called[0]
    assert timesPolled[0] == 50


def  test_wait_with_gui(): _run_with_wx(_test_wait, finishingDelay=1100)
def  test_wait_without_gui(): _test_wait()
def _test_wait():

    ntasks = 10

    def threadtask(num):
        time.sleep(random.random())
        threadtaskscalled[num] = True

    def waittask():
        waittaskcalled[0] = True

    for wait_direct in [False, True]:
        threadtaskscalled = [False] * ntasks
        waittaskcalled    = [False]

        threads = [threading.Thread(target=threadtask, args=(n,))
                   for n in range(ntasks)]

        for t in threads:
            t.start()

        t = async.wait(threads, waittask, wait_direct=wait_direct)

        if t is not None:
            t.join()
        
        _wait_for_idle_loop_to_clear()

        assert all(threadtaskscalled)
        assert waittaskcalled[0]


def test_TaskThread():

    called = [False]

    def task():
        called[0] = True

    tt = async.TaskThread()
    tt.start()

    tt.enqueue(task)

    time.sleep(0.5)

    tt.stop()
    tt.join()

    assert called[0]


def test_TaskThread_onFinish():

    taskCalled     = [False]
    onFinishCalled = [False]

    def task():
        taskCalled[0] = True

    def onFinish():
        onFinishCalled[0] = True 

    tt = async.TaskThread()
    tt.start()

    tt.enqueue(task, onFinish=onFinish)

    time.sleep(0.5)

    tt.stop()
    tt.join()

    assert taskCalled[0]
    assert onFinishCalled[0]


def test_TaskThread_isQueued():

    called = [False]

    def busyTask():
        time.sleep(0.5)

    def realTask():
        called[0] = True

    tt = async.TaskThread()
    tt.start()

    tt.enqueue(busyTask)
    tt.enqueue(realTask, taskName='realTask')

    time.sleep(0.25)

    queued = tt.isQueued('realTask')

    time.sleep(0.3)

    tt.stop()
    tt.join() 

    assert queued
    assert called[0]


def test_TaskThread_dequeue():

    called = [False]

    def busyTask():
        time.sleep(0.5)

    def realTask():
        called[0] = True

    tt = async.TaskThread()
    tt.start()

    tt.enqueue(busyTask)
    tt.enqueue(realTask, taskName='realTask')

    time.sleep(0.25)

    tt.dequeue('realTask')

    time.sleep(0.3)

    tt.stop()
    tt.join() 

    assert not called[0]


def test_TaskThread_TaskVeto():

    taskCalled     = [False]
    onFinishCalled = [False]

    def task():
        taskCalled[0] = True
        raise async.TaskThreadVeto()

    def onFinish():
        onFinishCalled[0] = True

    tt = async.TaskThread()
    tt.start()

    tt.enqueue(task, onFinish=onFinish)

    time.sleep(0.5)

    tt.stop()
    tt.join() 

    assert     taskCalled[0]
    assert not onFinishCalled[0]


def test_mutex():

    class Thing(object):

        @async.mutex
        def method1(self):
            time.sleep(0.5)

        @async.mutex
        def method2(self):
            time.sleep(0.5)

    t = [Thing()]

    times = {
        'thread1start' : 0,
        'thread1end'   : 0,
        'thread2start' : 0,
        'thread2end'   : 0,
    }


    def thread1():
        times['thread1start'] = time.time()
        t[0].method1()
        times['thread1end'] = time.time()

    def thread2():
        times['thread2start'] = time.time()
        t[0].method2()
        times['thread2start'] = time.time()

    for i in range(10):
        
        times = {
            'thread1start' : 0,
            'thread1end'   : 0,
            'thread2start' : 0,
            'thread2end'   : 0,
        }

        t1 = threading.Thread(target=thread1)
        t2 = threading.Thread(target=thread2)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert times['thread2start'] > times['thread1end']
