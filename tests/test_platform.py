#!/usr/bin/env python
#
# test_platform.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            os
import os.path as op
import            sys
import            shutil
import            tempfile
import            pytest

import mock


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


@pytest.mark.wxtest
def test_haveGui():

    import wx

    p      = fslplatform.Platform()
    app    = wx.App()
    frame  = wx.Frame(None)
    passed = [False]
    frame.Show()

    def runtest():

        try:
            assert p.haveGui
            passed[0] = True
        finally:
            frame.Destroy()
            app.ExitMainLoop()

    wx.CallLater(500, runtest)

    app.MainLoop()

    assert passed[0]


@pytest.mark.wxtest
def test_wxatts():

    with mock.patch.dict('sys.modules', wx=None):
        p = fslplatform.Platform()
        assert not p.canHaveGui
        assert not p.haveGui
        assert p.wxFlavour  == fslplatform.WX_UNKNOWN
        assert p.wxPlatform == fslplatform.WX_UNKNOWN

    with mock.patch('wx.App.IsDisplayAvailable', return_value=False):

        p = fslplatform.Platform()
        assert not p.canHaveGui
        assert not p.haveGui
        assert p.wxFlavour  == fslplatform.WX_UNKNOWN
        assert p.wxPlatform == fslplatform.WX_UNKNOWN

    with mock.patch('wx.App.IsDisplayAvailable', return_value=True), \
         mock.patch('wx.PlatformInfo', ('gtk', 'phoenix')):

        p = fslplatform.Platform()
        assert     p.canHaveGui
        assert not p.haveGui
        assert     p.wxFlavour  == fslplatform.WX_PHOENIX
        assert     p.wxPlatform == fslplatform.WX_GTK


    # (wx.PlatformInfo, expected platform, expected flavour)
    platflavtests = [
        (('__WXMAC__',
          'wxMac',
          'unicode',
          'unicode-wchar',
          'wxOSX',
          'wxOSX-cocoa',
          'wx-assertions-on',
          'phoenix',
          'wxWidgets 3.0.4'),
         fslplatform.WX_MAC_COCOA,
         fslplatform.WX_PHOENIX),
        (('__WXMAC__',
          'wxMac',
          'unicode',
          'wxOSX',
          'wxOSX-cocoa',
          'wx-assertions-on',
          'SWIG-1.3.29'),
         fslplatform.WX_MAC_COCOA,
         fslplatform.WX_PYTHON),
        (('__WXGTK__',
          'wxGTK',
          'unicode',
          'unicode-wchar',
          'gtk2',
          'wx-assertions-on',
          'phoenix',
          'wxWidgets 3.0.4'),
         fslplatform.WX_GTK,
         fslplatform.WX_PHOENIX),
        (('__WXGTK__',
          'wxGTK',
          'unicode',
          'gtk2',
          'wx-assertions-on',
          'SWIG-1.3.29'),
         fslplatform.WX_GTK,
         fslplatform.WX_PYTHON)]

    for platinfo, expplatform, expflavour in platflavtests:
        with mock.patch('wx.PlatformInfo', platinfo):

            p = fslplatform.Platform()
            assert p.wxFlavour  == expflavour
            assert p.wxPlatform == expplatform


def test_gl():

    p = fslplatform.Platform()

    p.glVersion  = '2.1'
    p.glRenderer = 'Fake renderer'


    assert p.glVersion  == '2.1'
    assert p.glRenderer == 'Fake renderer'


def test_fsldir():

    # We have to make a dummy directory that looks like FSL
    testdir = tempfile.mkdtemp()
    fsldir  = op.join(testdir, 'fsl')

    def makeFSL():
        os.makedirs(op.join(fsldir, 'etc'))
        with open(op.join(fsldir, 'etc', 'fslversion'), 'wt') as f:
            f.write('6.0.2:7606e0d8\n')

    try:

        makeFSL()

        p         = fslplatform.Platform()
        newFSLDir = [None]

        def fsldirChanged(p, t, val):
            newFSLDir[0] = val

        p.register('callback', fsldirChanged)

        p.fsldir = fsldir

        p.deregister('callback')

        assert os.environ['FSLDIR'] == fsldir
        assert newFSLDir[0]         == fsldir
        assert p.fsldir             == fsldir
        assert p.fslVersion         == '6.0.2'

    finally:
        shutil.rmtree(testdir)


def test_detect_ssh():

    sshVars = ['SSH_CLIENT', 'SSH_TTY']
    vncVars = ['VNCDESKTOP', 'X2GO_SESSION', 'NXSESSIONID']

    for sv in sshVars:
        with mock.patch.dict('os.environ', **{ sv : '1'}):
            p = fslplatform.Platform()
            assert p.inSSHSession


    for vv in vncVars:
        with mock.patch.dict('os.environ', **{ vv : '1'}):
            p = fslplatform.Platform()
            assert p.inVNCSession

    with mock.patch('os.environ', {}):
        p = fslplatform.Platform()
        assert not p.inSSHSession
        assert not p.inVNCSession
