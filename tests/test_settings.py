#!/usr/bin/env python
#
# test_settings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.utils.settings as settings



def test_strToBool():

    assert settings.strToBool('FALSE') is False
    assert settings.strToBool('False') is False
    assert settings.strToBool('false') is False
    assert settings.strToBool( False)  is False
    assert settings.strToBool('TRUE')  is True
    assert settings.strToBool('True')  is True
    assert settings.strToBool('true')  is True
    assert settings.strToBool( True)   is True


def _do_wx_settings_test(func):

    import wx 

    passed = [False]
    app    = wx.App()
    frame  = wx.Frame(None)

    def wrap():
        try:
            func()
            passed[0] = True
        finally:
            frame.Destroy()
            app.ExitMainLoop()
    
    frame.Show()

    wx.CallLater(500, wrap)

    app.MainLoop()
    assert passed[0]


def  test_readwrite(): _do_wx_settings_test(_test_readwrite)
def _test_readwrite():

    tests = [('string_setting', 'string_value'),
             ('int_setting',     123),
             ('float_setting',   123.0),
             ('bool_setting1',   True),
             ('bool_setting2',   True),
             ('tuple_setting',  (1, 2, 'blah')),
             ('list_setting',   [1, 2, 'blah'])]

    for k, v in tests:
        settings.write(k, v)
        assert settings.read(k) == str(v)

    assert settings.read('non-existent')            is None
    assert settings.read('non-existent', 'default') == 'default'


def  test_readdefault(): _do_wx_settings_test(_test_readdefault)
def _test_readdefault():
    assert settings.read('non-existent')            is None
    assert settings.read('non-existent', 'default') == 'default' 


def  test_delete(): _do_wx_settings_test(_test_delete)
def _test_delete():

    settings.delete('non-existent')
    assert settings.read('non-existent') is None

    settings.write('my_setting', 'abcdef')
    assert settings.read('my_setting') == 'abcdef'
    settings.delete('my_setting')
    assert settings.read('my_setting') is None


def  test_clear(): _do_wx_settings_test(_test_clear)
def _test_clear():

    tests = [('setting1', '1'),
             ('setting2', '2'),
             ('setting3', '3')]

    for k, v in tests:
        settings.write(k, v)

    for k, v in tests:
        assert settings.read(k) == v

    settings.clear()

    for k, v in tests:
        assert settings.read(k) is None
