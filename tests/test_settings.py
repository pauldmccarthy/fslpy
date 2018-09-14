#!/usr/bin/env python
#
# test_settings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            pickle
import            textwrap
import            tempfile

# python 3
try:
    import unittest.mock as mock
# python 2
except:
    import mock

import pytest

import tests
import fsl.utils.settings as settings
import fsl.utils.tempdir  as tempdir


def test_initialise():

    # Assuming that initialise()
    # has not yet been called
    assert settings.read('nothing') is None
    assert settings.read('nothing', 'default') == 'default'
    settings.write('nothing', 'nothing')
    settings.delete('nothing')
    assert settings.readFile('nothing') is None
    settings.writeFile('nothing', 'nothing')
    settings.deleteFile('nothing')
    assert settings.filePath() is None
    assert settings.readAll() == {}
    assert settings.listFiles() == []
    settings.clear()

    with tests.testdir() as testdir:

        settings.initialise(cfgid='test', cfgdir=testdir, writeOnExit=False)

        assert settings.settings.configID  == 'test'
        assert settings.settings.configDir == testdir

        settings.write('setting', 'value')

        assert settings.read('setting') == 'value'
        assert settings.read('nothing') is None


def test_init_configDir():

    # config dir on linux
    with tests.testdir() as testdir, \
          mock.patch('fsl.utils.settings.platform.system', return_value='linux'),  \
          mock.patch('fsl.utils.settings.op.expanduser',   return_value=testdir):

        expected = op.join(testdir, '.config', 'test')

        s = settings.Settings(cfgid='test', writeOnExit=False)

        assert s.configDir == expected

    # config dir on linux  with XDG_CONFIG_DIR set
    with tests.testdir() as testdir, \
          mock.patch('fsl.utils.settings.platform.system', return_value='linux'):

        oldval = os.environ.get('XDG_CONFIG_HOME', None)

        os.environ['XDG_CONFIG_HOME'] = testdir

        expected = op.join(testdir, 'test')

        s = settings.Settings(cfgid='test', writeOnExit=False)

        assert s.configDir == expected

        if oldval is None:
            os.environ.pop('XDG_CONFIG_HOME')
        else:
            os.environ['XDG_CONFIG_HOME'] = oldval

    # config dir on any other platform
    with tests.testdir() as testdir, \
          mock.patch('fsl.utils.settings.platform.system', return_value='notlinux'), \
          mock.patch('fsl.utils.settings.op.expanduser',   return_value=testdir):

        expected = op.join(testdir, '.test')

        s = settings.Settings(cfgid='test', writeOnExit=False)

        assert s.configDir == expected

def test_init_configDir_tempdir():

    atexit_funcs = []

    def mock_atexit_register(func, *args, **kwargs):
        atexit_funcs.append((func, args, kwargs))

    with mock.patch('fsl.utils.settings.atexit.register', mock_atexit_register), \
         mock.patch('fsl.utils.settings.os.makedirs', side_effect=OSError):

        s      = settings.Settings('test', writeOnExit=False)
        cfgdir = s.configDir

        assert cfgdir.startswith(tempfile.gettempdir())
        assert op.exists(cfgdir)

        assert len(atexit_funcs) == 1

        f, a, kwa = atexit_funcs[0]
        f(*a, **kwa)

        assert not op.exists(cfgdir)



def test_init_writeOnExit():

    atexit_funcs = []

    def mock_atexit_register(func, *args, **kwargs):
        atexit_funcs.append((func, args, kwargs))

    testdata = {
        'setting1' : 123,
        'setting2' : 'Blahblah',
        'setting3' : [1, 2, ('three', 4)]
    }

    with tests.testdir() as testdir, \
         mock.patch('fsl.utils.settings.atexit.register', mock_atexit_register):

        s = settings.Settings('test', cfgdir=testdir)

        for k, v in testdata.items():
            s.write(k, v)

        assert len(atexit_funcs) == 1

        f, a, kwa = atexit_funcs[0]
        f(*a, **kwa)

        with open(op.join(testdir, 'config.pkl'), 'rb') as f:
            readback = pickle.load(f)
            assert testdata == readback

def test_init_not_writeOnExit():


    atexit_funcs = []

    def mock_atexit_register(func, *args, **kwargs):
        atexit_funcs.append((func, args, kwargs))

    with tests.testdir() as testdir, \
         mock.patch('fsl.utils.settings.atexit.register', mock_atexit_register):

        s = settings.Settings('test', cfgdir=testdir, writeOnExit=False)

        assert len(atexit_funcs) == 0




def test_readConfigFile():

    with tests.testdir() as testdir:

        testdata = {
            'setting1' : 123,
            'setting2' : 'Blahblah',
            'setting3' : [1, 2, ('three', 4)]
        }

        with open(op.join(testdir, 'config.pkl'), 'wb') as f:
            pickle.dump(testdata, f)

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        for k, v in testdata.items():
            assert s.read(k) == v


def test_readwrite():

    testcases = [('string_setting', 'string_value'),
                 ('int_setting',     123),
                 ('float_setting',   123.0),
                 ('bool_setting1',   True),
                 ('bool_setting2',   True),
                 ('tuple_setting',  (1, 2, 'blah')),
                 ('list_setting',   [1, 2, 'blah'])]

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        for k, v in testcases:
            s.write(k, v)
            assert s.read(k) == v

        assert s.read('non-existent')            is None
        assert s.read('non-existent', 'default') == 'default'


def test_readdefault():

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        assert s.read('non-existent')            is None
        assert s.read('non-existent', 'default') == 'default'


def test_delete():

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        s.delete('non-existent')
        assert s.read('non-existent') is None

        s.write('my_setting', 'abcdef')
        assert s.read('my_setting') == 'abcdef'
        s.delete('my_setting')
        assert s.read('my_setting') is None



def test_readwriteFile_text():

    contents = textwrap.dedent("""
    Test file 1
    This is a test
    """).strip()

    with tests.testdir() as testdir:
        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        with s.writeFile('testfile/contents.txt', 't') as f:
            f.write(contents)

        assert s.readFile('testfile/contents.txt', 't') == contents
        assert s.readFile('notafile',              't') is None


def test_readwriteFile_binary():

    contents = b'\x00\x10\x20\x30\x40\x50\x6a'

    with tests.testdir() as testdir:
        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        with s.writeFile('testfile/contents.bin', 'b') as f:
            f.write(contents)

        assert s.readFile('testfile/contents.bin', 'b') == contents
        assert s.readFile('notafile',              'b') is None


def test_deleteFile():

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        s.deleteFile('non-existent')
        assert s.readFile('non-existent') is None

        path     = 'path/to/file.txt'
        contents = 'abcdef'

        with s.writeFile(path) as f:
            f.write(contents)

        assert s.readFile(path) == contents

        s.deleteFile(path)
        assert s.read(path) is None


def test_readall():

    testsettings = [('namespace1.setting1', '1'),
                    ('namespace1.setting2', '2'),
                    ('namespace1.setting3', '3'),
                    ('namespace2.setting1', '4'),
                    ('namespace2.setting2', '5'),
                    ('namespace2.setting3', '6')]

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        assert s.readAll() == {}

        for k, v in testsettings:
            s.write(k, v)

        assert s.readAll() == dict(testsettings)

        ns1 = [(k, v) for k, v in testsettings if k.startswith('namespace1')]
        ns2 = [(k, v) for k, v in testsettings if k.startswith('namespace2')]

        assert s.readAll('namespace1.*') == dict(ns1)
        assert s.readAll('namespace2.*') == dict(ns2)
        assert s.readAll('*setting*')    == dict(testsettings)


def test_listFiles():

    ns1files  = ['namespace1/setting1.txt',
                 'namespace1/setting2.txt',
                 'namespace1/setting3.txt']
    ns2files  = ['namespace2/setting1.txt',
                 'namespace2/setting2.txt',
                 'namespace2/setting3.txt']

    ns1files = [op.join(*f.split('/')) for f in ns1files]
    ns2files = [op.join(*f.split('/')) for f in ns2files]

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        assert s.listFiles() == []

        for fn in ns1files + ns2files:
            with s.writeFile(fn) as f:
                f.write(fn)

        assert list(sorted(s.listFiles())) == list(sorted(ns1files + ns2files))

        assert list(sorted(s.listFiles(op.join('namespace1', '*')))) == list(sorted(ns1files))
        assert list(sorted(s.listFiles(op.join('namespace2', '*')))) == list(sorted(ns2files))
        assert list(sorted(s.listFiles(op.join('namespace?', '*')))) == list(sorted(ns1files + ns2files))
        assert list(sorted(s.listFiles('*.txt')))        == list(sorted(ns1files + ns2files))
        assert list(sorted(s.listFiles(op.join('*', 'setting1.txt')))) == list(sorted([ns1files[0]] + [ns2files[0]]))


def test_filePath():

    testfiles  = ['file1.txt',
                  'dir1/file2.txt',
                  'dir1/dir2/file3.txt']
    testfiles = [op.join(*f.split('/')) for f in testfiles]

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        assert s.filePath('nofile') == op.join(testdir, 'nofile')

        for fn in testfiles:
            with s.writeFile(fn) as f:
                f.write(fn)

        assert s.filePath('nofile') == op.join(testdir, 'nofile')

        for f in testfiles:
            assert s.filePath(f) == op.join(testdir, f)


def test_clear():

    testsettings = [('setting1', '1'),
                    ('setting2', '2'),
                    ('setting3', '3')]
    testfiles     = [('path/to/file1.txt',         'testfile1 contents'),
                     ('path/to/another/file2.txt', 'testfile2 contents'),
                     ('file3.txt',                 'testfile3 contents')]

    # TODO File

    with tests.testdir() as testdir:

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        for k, v in testsettings:
            s.write(k, v)

        for p, c in testfiles:
            with s.writeFile(p) as f:
                f.write(c)

        for k, v in testsettings:
            assert s.read(k) == v

        for p, c in testfiles:
            assert s.readFile(p) == c

        s.clear()

        for k, v in testsettings:
            assert s.read(k) is None

        for p, c in testfiles:
            assert s.readFile(p) is None


def test_writeConfigFile():

    with tests.testdir() as testdir:

        testdata = {
            'setting1' : 123,
            'setting2' : 'Blahblah',
            'setting3' : [1, 2, ('three', 4)]
        }

        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

        for k, v in testdata.items():
            s.write(k, v)

        for k, v in testdata.items():
            assert s.read(k) == v

        s.writeConfigFile()

        with open(op.join(testdir, 'config.pkl'), 'rb') as f:
            readback = pickle.load(f)
            assert testdata == readback

        # should fail gracefuly
        # if write is not possible
        s = settings.Settings(cfgid='test', cfgdir=testdir, writeOnExit=False)

    # testdir has been removed,
    # but call should not crash
    s.writeConfigFile()




def test_set():

    with tempdir.tempdir(changeto=False) as td1,\
         tempdir.tempdir(changeto=False) as td2:

        s1 = settings.Settings(cfgdir=td1, writeOnExit=False)
        s2 = settings.Settings(cfgdir=td2, writeOnExit=False)

        settings.set(s1)
        with settings.writeFile('file1') as f:
            f.write('hi!')
        assert os.listdir(td1) == ['file1']
        assert os.listdir(td2) == []

        settings.set(s2)
        with settings.writeFile('file2') as f:
            f.write('hi!')
        assert os.listdir(td1) == ['file1']
        assert os.listdir(td2) == ['file2']

        settings.set(s1)
        with settings.writeFile('file3') as f:
            f.write('hi!')
        assert sorted(os.listdir(td1)) == ['file1', 'file3']
        assert        os.listdir(td2)  == ['file2']

        settings.set(s2)
        with settings.writeFile('file4') as f:
            f.write('hi!')
        assert sorted(os.listdir(td1)) == ['file1', 'file3']
        assert sorted(os.listdir(td2)) == ['file2', 'file4']


def test_use():

    with tempdir.tempdir(changeto=False) as td1,\
         tempdir.tempdir(changeto=False) as td2:

        s1 = settings.Settings(cfgdir=td1, writeOnExit=False)
        s2 = settings.Settings(cfgdir=td2, writeOnExit=False)

        with settings.use(s1):
            with settings.writeFile('file1') as f:
                f.write('hi!')

        assert os.listdir(td1) == ['file1']
        assert os.listdir(td2) == []

        with settings.use(s2):
            with settings.writeFile('file2') as f:
                f.write('hi!')

        settings.set(s1)
        with settings.writeFile('file3') as f:
                f.write('hi!')

        with settings.use(s2):
            with settings.writeFile('file4') as f:
                f.write('hi!')

        assert sorted(os.listdir(td1)) == ['file1', 'file3']
        assert sorted(os.listdir(td2)) == ['file2', 'file4']

        # should go back to s1
        with settings.writeFile('file5') as f:
            f.write('hi!')

        assert sorted(os.listdir(td1)) == ['file1', 'file3', 'file5']
        assert sorted(os.listdir(td2)) == ['file2', 'file4']

        try:
            with settings.use(s2):
                raise Exception('hur')
        except Exception:
            pass

        # should go back to s1
        with settings.writeFile('file6') as f:
            f.write('hi!')

        assert sorted(os.listdir(td1)) == ['file1', 'file3', 'file5', 'file6']
        assert sorted(os.listdir(td2)) == ['file2', 'file4']
