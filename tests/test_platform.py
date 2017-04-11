#!/usr/bin/env python
#
# test_platform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            os
import os.path as op
import            shutil
import            tempfile


import fsl.utils.platform as fslplatform


def test_atts():
    
    p = fslplatform.platform
    p.os
    p.frozen
    p.haveGui
    p.canHaveGui
    p.inSSHSession
    p.wxPlatform
    p.wxFlavour
    p.fsldir
    p.fslVersion
    p.glVersion
    p.glRenderer
    p.glIsSoftwareRenderer


def test_gui():

    import wx
    
    p      = fslplatform.platform
    app    = wx.App()
    frame  = wx.Frame(None)
    passed = [False]
    frame.Show()

    def runtest():

        try:

            p.haveGui
            p.wxPlatform
            p.wxFlavour
            passed[0] = True
        finally:
            frame.Destroy()
            app.ExitMainLoop()

    wx.CallLater(500, runtest)

    app.MainLoop()

    assert passed[0]


def test_gl():
    
    p = fslplatform.platform
    
    p.glVersion  = '2.1'
    p.glRenderer = 'Fake renderer'

    
def test_fsldir():

    # We have to make a dummy directory that looks like FSL
    testdir = tempfile.mkdtemp()
    fsldir  = op.join(testdir, 'fsl')

    def makeFSL():
        os.makedirs(op.join(fsldir, 'etc'))
        with open(op.join(fsldir, 'etc', 'fslversion'), 'wt') as f:
            f.write('Dummy FSL\n')

    try:

        makeFSL()

        p         = fslplatform.platform
        newFSLDir = [None]

        def fsldirChanged(p, t, val):
            newFSLDir[0] = val

        p.register('callback', fsldirChanged)

        p.fsldir = fsldir

        p.deregister('callback')

        assert os.environ['FSLDIR'] == fsldir
        assert newFSLDir[0]         == fsldir
        assert p.fsldir             == fsldir
        assert p.fslVersion         == 'Dummy FSL'

    finally:
        shutil.rmtree(testdir)

    
def test_IsWidgetAlive():

    import wx

    passed = [False]
    app    = wx.App()
    frame  = wx.Frame(None)
    btn    = wx.Button(frame)
    frame.Show()

    def runtest():

        try:

            passed[0] = fslplatform.isWidgetAlive(btn)

            btn.Destroy()
        
            passed[0] = passed[0] and (not fslplatform.isWidgetAlive(btn))
        finally:
            frame.Destroy()
            app.ExitMainLoop()

    wx.CallLater(500, runtest)
    app.MainLoop()

    assert passed[0]
