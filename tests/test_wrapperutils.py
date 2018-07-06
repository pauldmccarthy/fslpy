#!/usr/bin/env python
#
# test_wrapperutils.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            os
import            shlex
import            textwrap

try: from unittest import mock
except ImportError: import mock

import pytest

import numpy as np
import nibabel as nib

import fsl.utils.tempdir         as tempdir
import fsl.utils.run             as run
import fsl.utils.fslsub          as fslsub
import fsl.data.image            as fslimage
import fsl.wrappers.wrapperutils as wutils


from . import mockFSLDIR, cleardir
from .test_run import mock_submit


def test_applyArgStyle():

    kwargs = {
        'name'  : 'val',
        'name2' : ['val1', 'val2'],
    }

    # these combinations of style+valsep should
    # raise an error
    with pytest.raises(ValueError):
        wutils.applyArgStyle(style='-=',  valsep=' ', **kwargs)
    with pytest.raises(ValueError):
        wutils.applyArgStyle(style='--=', valsep=' ', **kwargs)

    # unsupported style/valsep
    with pytest.raises(ValueError):
        wutils.applyArgStyle('?', **kwargs)
    with pytest.raises(ValueError):
        wutils.applyArgStyle('-', valsep='b', **kwargs)

    # style, valsep, expected_result.
    # Order of arguments is not guaranteed
    tests = [
        ('-',   ' ', [' -name  val', '-name2   val1 val2']),
        ('-',   '"', [' -name  val', '-name2  "val1 val2"']),
        ('-',   ',', [' -name  val', '-name2   val1,val2']),

        ('--',  ' ', ['--name  val', '--name2  val1 val2']),
        ('--',  '"', ['--name  val', '--name2 "val1 val2"']),
        ('--',  ',', ['--name  val', '--name2  val1,val2']),

        ('-=',  '"', [' -name=val', '-name2="val1 val2"']),
        ('-=',  ',', [' -name=val', '-name2=val1,val2']),

        ('--=', '"', ['--name=val', '--name2="val1 val2"']),
        ('--=', ',', ['--name=val', '--name2=val1,val2']),
    ]

    for style, valsep, exp in tests:
        exp    = [shlex.split(e) for e in exp]
        result = wutils.applyArgStyle(style, valsep=valsep, **kwargs)

        assert result in (exp[0] + exp[1], exp[1] + exp[0])


def test_applyArgStyle_argmap():

    kwargs = {
        'name1' : 'val1',
        'name2' : 'val2',
    }

    argmap = {
        'name1' : 'n',
        'name2' : 'm',
    }

    # order not guaranteed
    exp = [shlex.split('-n val1 -m val2'),
           shlex.split('-m val2 -n val1')]

    assert wutils.applyArgStyle('-', argmap=argmap, **kwargs) in exp


def test_applyArgStyle_valmap():

    valmap = {
        'a' : wutils.SHOW_IF_TRUE,
        'b' : wutils.HIDE_IF_TRUE,
    }

    # kwargs, expected
    tests = [
        ({                          }, ['']),
        ({ 'a' : False,             }, ['']),
        ({ 'a' : True,              }, ['-a']),
        ({              'b' : False }, ['-b']),
        ({              'b' : True  }, ['']),
        ({ 'a' : False, 'b' : True  }, ['']),
        ({ 'a' : True,  'b' : True  }, ['-a']),
        ({ 'a' : False, 'b' : False }, ['-b']),
        ({ 'a' : False, 'b' : True  }, ['']),
        ({ 'a' : True,  'b' : False }, ['-a -b', '-b -a']),
        ({ 'a' : True,  'b' : True  }, ['-a']),
    ]

    for kwargs, expected in tests:
        expected = [shlex.split(e) for e in expected]
        assert wutils.applyArgStyle('-', valmap=valmap, **kwargs) in expected


def test_applyArgStyle_argmap_valmap():

    argmap = {'a1' : 'a', 'a2' : 'b'}
    valmap = {
        'a' : wutils.SHOW_IF_TRUE,
        'b' : wutils.HIDE_IF_TRUE,
    }

    # kwargs, expected
    tests = [
        ({                            }, ['']),
        ({ 'a1' : False,              }, ['']),
        ({ 'a1' : True,               }, ['-a']),
        ({               'a2' : False }, ['-b']),
        ({               'a2' : True  }, ['']),
        ({ 'a1' : False, 'a2' : True  }, ['']),
        ({ 'a1' : True,  'a2' : True  }, ['-a']),
        ({ 'a1' : False, 'a2' : False }, ['-b']),
        ({ 'a1' : False, 'a2' : True  }, ['']),
        ({ 'a1' : True,  'a2' : False }, ['-a -b', '-b -a']),
        ({ 'a1' : True,  'a2' : True  }, ['-a']),
    ]

    for kwargs, expected in tests:
        expected = [shlex.split(e) for e in expected]
        assert wutils.applyArgStyle(
            '-', argmap=argmap, valmap=valmap, **kwargs) in expected


def test_namedPositionals():
    def func1(): pass
    def func2(a, b, c): pass
    def func3(a, b, c, d=None, e=None): pass
    def func4(*args): pass
    def func5(*args, **kwargs): pass
    def func6(a, b, *args): pass
    def func7(a, b, *args, **kwargs): pass

    tests = [
        (func1, [],        []),
        (func2, [1, 2, 3], ['a', 'b', 'c']),
        (func3, [1, 2, 3], ['a', 'b', 'c']),
        (func4, [1, 2, 3], ['args0', 'args1', 'args2']),
        (func5, [1, 2, 3], ['args0', 'args1', 'args2']),
        (func6, [1, 2, 3], ['a', 'b', 'args0']),
        (func7, [1, 2, 3], ['a', 'b', 'args0']),
    ]

    for func, args, expected in tests:
        result = wutils.namedPositionals(func, args)
        assert list(result) == list(expected)


def test_fileOrArray():

    @wutils.fileOrArray('arr1', 'other', 'output')
    def func(arr1, **kwargs):
        arr1  = np.loadtxt(arr1)
        other = np.loadtxt(kwargs['other'])
        np.savetxt(kwargs['output'], (arr1 * other))

    with tempdir.tempdir():

        arr1     = np.array([[1,  2], [ 3,  4]])
        other    = np.array([[5,  6], [ 7,  8]])
        expected = np.array([[5, 12], [21, 32]])
        np.savetxt('arr1.txt',  arr1)
        np.savetxt('other.txt', other)

        # file  file  file
        func('arr1.txt', other='other.txt', output='output.txt')
        assert np.all(np.loadtxt('output.txt') == expected)
        os.remove('output.txt')

        # file  file  array
        result = func('arr1.txt', other='other.txt', output=wutils.LOAD)['output']
        assert np.all(result == expected)

        # file  array file
        func('arr1.txt', other=other, output='output.txt')
        assert np.all(np.loadtxt('output.txt') == expected)
        os.remove('output.txt')

        # file  array array
        result = func('arr1.txt', other=other, output=wutils.LOAD)['output']
        assert np.all(result == expected)

        # array file  file
        func(arr1, other='other.txt', output='output.txt')
        assert np.all(np.loadtxt('output.txt') == expected)
        os.remove('output.txt')

        # array file  array
        result = func(arr1, other='other.txt', output=wutils.LOAD)['output']
        assert np.all(result == expected)

        # array array file
        func(arr1, other=other, output='output.txt')
        assert np.all(np.loadtxt('output.txt') == expected)
        os.remove('output.txt')

        # array array array
        result = func(arr1, other=other, output=wutils.LOAD)['output']
        assert np.all(result == expected)


def test_fileOrImage():

    @wutils.fileOrImage('img1', 'img2', 'output')
    def func(img1, **kwargs):
        img1   = nib.load(img1).get_data()
        img2   = nib.load(kwargs['img2']).get_data()
        output = nib.nifti1.Nifti1Image(img1 * img2, np.eye(4))
        nib.save(output, kwargs['output'])

    with tempdir.tempdir():

        img1     = nib.nifti1.Nifti1Image(np.array([[1,  2], [ 3,  4]]), np.eye(4))
        img2     = nib.nifti1.Nifti1Image(np.array([[5,  6], [ 7,  8]]), np.eye(4))
        img3     = nib.nifti1.Nifti1Image(np.array([[1,  2], [ 3,  4]]), np.eye(4))
        expected = np.array([[5, 12], [21, 32]])
        nib.save(img1, 'img1.nii')
        nib.save(img2, 'img2.nii')

        # file  file  file
        func('img1.nii', img2='img2.nii', output='output.nii')
        assert np.all(nib.load('output.nii').get_data() == expected)
        os.remove('output.nii')

        # file  file  array
        result = func('img1.nii', img2='img2.nii', output=wutils.LOAD)['output']
        assert np.all(result.get_data() == expected)

        # file  array file
        func('img1.nii', img2=img2, output='output.nii')
        assert np.all(nib.load('output.nii').get_data() == expected)
        os.remove('output.nii')

        # file  array array
        result = func('img1.nii', img2=img2, output=wutils.LOAD)['output']
        assert np.all(result.get_data() == expected)

        # array file  file
        func(img1, img2='img2.nii', output='output.nii')
        assert np.all(nib.load('output.nii').get_data() == expected)
        os.remove('output.nii')

        # array file  array
        result = func(img1, img2='img2.nii', output=wutils.LOAD)['output']
        assert np.all(result.get_data() == expected)

        # array array file
        func(img1, img2=img2, output='output.nii')
        assert np.all(nib.load('output.nii').get_data() == expected)
        os.remove('output.nii')

        # array array array
        result = func(img1, img2=img2, output=wutils.LOAD)['output']
        assert np.all(result.get_data() == expected)

        # in-memory image, file, file
        result = func(img3, img2='img2.nii', output='output.nii')
        assert np.all(nib.load('output.nii').get_data() == expected)
        os.remove('output.nii')

        # fslimage, file, load
        result = func(fslimage.Image(img1), img2='img2.nii',
                      output=wutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # fslimage, fslimage, load
        result = func(fslimage.Image(img1), img2=fslimage.Image(img2),
                      output=wutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # fslimage, nib.image, load
        result = func(fslimage.Image(img1), img2=img2,
                      output=wutils.LOAD)['output']
        assert isinstance(result, fslimage.Image)
        assert np.all(result[:].squeeze() == expected)

        # nib.image, nib.image, load
        result = func(img1, img2=img2, output=wutils.LOAD)['output']
        assert isinstance(result, nib.nifti1.Nifti1Image)
        assert np.all(result.get_data()[:] == expected)


def test_fileOrImage_outprefix():

    import logging
    logging.basicConfig()
    logging.getLogger('fsl.wrappers').setLevel(logging.DEBUG)

    @wutils.fileOrImage('img', outprefix='output_base')
    def basefunc(img, output_base):
        img = nib.load(img).get_data()

        out1 = nib.nifti1.Nifti1Image(img * 5,  np.eye(4))
        out2 = nib.nifti1.Nifti1Image(img * 10, np.eye(4))

        nib.save(out1, '{}_times5.nii.gz' .format(output_base))
        nib.save(out2, '{}_times10.nii.gz'.format(output_base))

    with tempdir.tempdir() as td:
        img  = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        exp1 = img.get_data() * 5
        exp2 = img.get_data() * 10
        nib.save(img, 'img.nii')

        basefunc('img.nii', 'myout')
        assert np.all(nib.load('myout_times5.nii.gz') .get_data() == exp1)
        assert np.all(nib.load('myout_times10.nii.gz').get_data() == exp2)
        cleardir(td, 'myout*')

        basefunc(img, 'myout')
        assert np.all(nib.load('myout_times5.nii.gz') .get_data() == exp1)
        assert np.all(nib.load('myout_times10.nii.gz').get_data() == exp2)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout_times5=wutils.LOAD)
        assert np.all(res['myout_times5'].get_data() == exp1)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout_times10=wutils.LOAD)
        assert np.all(res['myout_times10'].get_data() == exp2)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout=wutils.LOAD)
        assert np.all(res['myout_times5'] .get_data() == exp1)
        assert np.all(res['myout_times10'].get_data() == exp2)
        cleardir(td, 'myout*')


def test_fileOrImage_outprefix_differentTypes():

    @wutils.fileOrImage('img', outprefix='outpref')
    def func(img, outpref):

        img  = nib.load(img)
        img  = nib.nifti1.Nifti1Image(img.get_data() * 2, np.eye(4))
        text = '1234567890'

        nib.save(img, '{}_image.nii.gz' .format(outpref))

        with open('{}_text.txt'.format(outpref), 'wt') as f:
            f.write(text)

    with tempdir.tempdir() as td:
        img  = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        expi = img.get_data() * 2
        expt = '1234567890'

        func(img, 'myout')
        assert np.all(nib.load('myout_image.nii.gz') .get_data() == expi)
        with open('myout_text.txt', 'rt') as f:
            assert f.read().strip() == expt
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout_image=wutils.LOAD)
        assert list(res.keys()) == ['myout_image']
        assert np.all(res['myout_image'].get_data() == expi)
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout=wutils.LOAD)
        assert list(res.keys()) == ['myout_image']
        assert np.all(res['myout_image'].get_data() == expi)
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout_text=wutils.LOAD)
        assert list(res.keys()) == []
        cleardir(td, 'myout*')




# test directory





def test_chained_fileOrImageAndArray():
    @wutils.fileOrImage('image')
    @wutils.fileOrArray('array')
    def func(image, array):
        nib.load(image)
        np.loadtxt(array)

    image = nib.nifti1.Nifti1Image(np.array([[1,  2], [ 3,  4]]), np.eye(4))
    array = np.array([[5, 6, 7, 8]])

    with tempdir.tempdir():

        nib.save(image, 'image.nii')
        np.savetxt('array.txt', array)

        func('image.nii', 'array.txt')
        func('image.nii',  array)
        func( image,      'array.txt')
        func( image,       array)


def test_cmdwrapper():
    @wutils.cmdwrapper
    def func(a, b):
        return ['func', str(a), str(b)]

    with run.dryrun():
        assert func(1, 2)[0] == 'func 1 2'


def test_fslwrapper():
    @wutils.fslwrapper
    def func(a, b):
        return ['func', str(a), str(b)]

    with run.dryrun(), mockFSLDIR() as fsldir:
        expected = '{} 1 2'.format(op.join(fsldir, 'bin', 'func'))
        assert func(1, 2)[0] == expected


_test_script = textwrap.dedent("""
#!/usr/bin/env bash
echo "test_script running: $1 $2"
exit 0
""").strip()


def _test_script_func(a, b):
    return ['test_script', str(a), str(b)]


def test_cmdwrapper_submit():

    test_func = wutils.cmdwrapper(_test_script_func)
    newpath = op.pathsep.join(('.', os.environ['PATH']))

    with tempdir.tempdir(), \
         mock.patch('fsl.utils.fslsub.submit', mock_submit), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        with open('test_script', 'wt') as f:
            f.write(_test_script)
        os.chmod('test_script', 0o755)

        jid = test_func(1, 2, submit=True)

        assert jid == ('12345',)

        stdout, stderr = fslsub.output('12345')

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == ''


def test_fslwrapper_submit():

    test_func = wutils.fslwrapper(_test_script_func)

    with mockFSLDIR() as fsldir, \
         mock.patch('fsl.utils.fslsub.submit', mock_submit):

        test_file = op.join(fsldir, 'bin', 'test_script')

        with open(test_file, 'wt') as f:
            f.write(_test_script)
        os.chmod(test_file, 0o755)

        jid = test_func(1, 2, submit=True)

        assert jid == ('12345',)

        stdout, stderr = fslsub.output('12345')

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == ''

        kwargs = {'name' : 'abcde', 'ram' : '4GB'}

        jid = test_func(1, 2, submit=kwargs)

        assert jid == ('12345',)

        stdout, stderr = fslsub.output('12345')

        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())])

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == experr
