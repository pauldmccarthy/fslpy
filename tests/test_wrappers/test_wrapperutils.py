#!/usr/bin/env python
#
# test_wrapperutils.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            os
import            shlex
import            pathlib
import            textwrap

from unittest import mock

import pytest

import numpy as np
import nibabel as nib

import fsl.utils.tempdir         as tempdir
import fsl.utils.run             as run
import fsl.utils.assertions      as asrt
import fsl.utils.fslsub          as fslsub
import fsl.data.image            as fslimage
import fsl.wrappers.wrapperutils as wutils


from .. import mockFSLDIR, cleardir, checkdir, testdir, touch
from ..test_run import mock_submit


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
        img1   = np.asanyarray(nib.load(img1).dataobj)
        img2   = np.asanyarray(nib.load(kwargs['img2']).dataobj)
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
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # file  file  array
        result = func('img1.nii', img2='img2.nii', output=wutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # file  array file
        func('img1.nii', img2=img2, output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # file  array array
        result = func('img1.nii', img2=img2, output=wutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # array file  file
        func(img1, img2='img2.nii', output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # array file  array
        result = func(img1, img2='img2.nii', output=wutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # array array file
        func(img1, img2=img2, output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
        os.remove('output.nii')

        # array array array
        result = func(img1, img2=img2, output=wutils.LOAD)['output']
        assert np.all(np.asanyarray(result.dataobj) == expected)

        # in-memory image, file, file
        result = func(img3, img2='img2.nii', output='output.nii')
        assert np.all(np.asanyarray(nib.load('output.nii').dataobj) == expected)
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
        assert np.all(np.asanyarray(result.dataobj)[:] == expected)


def test_fileOrThing_sequence():

    @wutils.fileOrArray('arrs', 'out')
    def func(arrs, out):

        if isinstance(arrs, str):
            arrs = [arrs]

        arrs = [np.loadtxt(a) for a in arrs]
        res  = np.sum(arrs, axis=0)

        np.savetxt(out, res)

    inputs  = [np.random.randint(1, 10, (3, 3)) for i in range(4)]
    infiles = ['input{}.txt'.format(i) for i in range(len(inputs))]
    exp     = np.sum(inputs, axis=0)

    with tempdir.tempdir():

        for ifile, idata in zip(infiles, inputs):
            np.savetxt(ifile, idata)

        func(inputs, 'result.txt')
        assert np.all(np.loadtxt('result.txt') == exp)

        assert np.all(func(inputs, wutils.LOAD)['out'] == exp)

        func(inputs[0], 'result.txt')
        assert np.all(np.loadtxt('result.txt') == inputs[0])

        assert np.all(func(inputs[0], wutils.LOAD)['out'] == inputs[0])

        func(infiles, 'result.txt')
        assert np.all(np.loadtxt('result.txt') == exp)

        assert np.all(func(infiles, wutils.LOAD)['out'] == exp)

        func(infiles[0], 'result.txt')
        assert np.all(np.loadtxt('result.txt') == inputs[0])

        assert np.all(func(infiles[0], wutils.LOAD)['out'] == inputs[0])


def test_fileOrText():

    @wutils.fileOrText('input', 'output')
    def func(input, output):
        data = open(input).read()
        data = ''.join(['{}{}'.format(c, c) for c in data])
        open(output, 'wt').write(data)

    with tempdir.tempdir():

        data = 'abcdefg'
        exp  = 'aabbccddeeffgg'

        open('input.txt', 'wt').write(data)

        func(pathlib.Path('input.txt'), pathlib.Path('output.txt'))
        assert open('output.txt').read() == exp

        func('abcdefg', pathlib.Path('output.txt'))
        assert open('output.txt').read() == exp

        assert func('12345', wutils.LOAD).output == '1122334455'


def test_fileOrThing_outprefix():

    @wutils.fileOrImage('img', outprefix='output_base')
    def basefunc(img, output_base):
        img = np.asanyarray(nib.load(img).dataobj)

        out1 = nib.nifti1.Nifti1Image(img * 5,  np.eye(4))
        out2 = nib.nifti1.Nifti1Image(img * 10, np.eye(4))

        nib.save(out1, '{}_times5.nii.gz' .format(output_base))
        nib.save(out2, '{}_times10.nii.gz'.format(output_base))


    with tempdir.tempdir() as td:
        img  = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        exp1 = np.asanyarray(img.dataobj) * 5
        exp2 = np.asanyarray(img.dataobj) * 10
        nib.save(img, 'img.nii')

        basefunc('img.nii', 'myout')
        assert np.all(np.asanyarray(nib.load('myout_times5.nii.gz') .dataobj) == exp1)
        assert np.all(np.asanyarray(nib.load('myout_times10.nii.gz').dataobj) == exp2)
        cleardir(td, 'myout*')

        basefunc(img, 'myout')
        assert np.all(np.asanyarray(nib.load('myout_times5.nii.gz') .dataobj) == exp1)
        assert np.all(np.asanyarray(nib.load('myout_times10.nii.gz').dataobj) == exp2)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout_times5=wutils.LOAD)
        assert np.all(np.asanyarray(res['myout_times5'].dataobj) == exp1)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout_times10=wutils.LOAD)
        assert np.all(np.asanyarray(res['myout_times10'].dataobj) == exp2)
        cleardir(td, 'myout*')

        res = basefunc(img, 'myout', myout=wutils.LOAD)
        assert np.all(np.asanyarray(res['myout_times5'] .dataobj) == exp1)
        assert np.all(np.asanyarray(res['myout_times10'].dataobj) == exp2)
        cleardir(td, 'myout*')


def test_fileOrThing_outprefix_differentTypes():

    @wutils.fileOrImage('img', outprefix='outpref')
    def func(img, outpref):

        img  = nib.load(img)
        img  = nib.nifti1.Nifti1Image(np.asanyarray(img.dataobj) * 2, np.eye(4))
        text = '1234567890'

        nib.save(img, '{}_image.nii.gz' .format(outpref))

        with open('{}_text.txt'.format(outpref), 'wt') as f:
            f.write(text)

    with tempdir.tempdir() as td:
        img  = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        expi = np.asanyarray(img.dataobj) * 2
        expt = '1234567890'

        func(img, 'myout')
        assert np.all(np.asanyarray(nib.load('myout_image.nii.gz') .dataobj) == expi)
        with open('myout_text.txt', 'rt') as f:
            assert f.read().strip() == expt
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout_image=wutils.LOAD)
        assert list(res.keys()) == ['myout_image']
        assert np.all(np.asanyarray(res['myout_image'].dataobj) == expi)
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout=wutils.LOAD)
        assert list(res.keys()) == ['myout_image']
        assert np.all(np.asanyarray(res['myout_image'].dataobj) == expi)
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout_text=wutils.LOAD)
        assert list(res.keys()) == []
        cleardir(td, 'myout*')


def test_fileOrThing_outprefix_directory():

    import logging
    logging.basicConfig()
    logging.getLogger('fsl.wrappers').setLevel(logging.DEBUG)

    @wutils.fileOrImage('img', outprefix='outpref')
    def func(img, outpref):
        img  = nib.load(img)
        img2 = nib.nifti1.Nifti1Image(np.asanyarray(img.dataobj) * 2, np.eye(4))
        img4 = nib.nifti1.Nifti1Image(np.asanyarray(img.dataobj) * 4, np.eye(4))

        outdir = op.abspath('{}_imgs'.format(outpref))

        os.mkdir(outdir)

        nib.save(img2, op.join(outdir, 'img2.nii.gz'))
        nib.save(img4, op.join(outdir, 'img4.nii.gz'))

    with tempdir.tempdir() as td:
        img  = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        exp2 = np.asanyarray(img.dataobj) * 2
        exp4 = np.asanyarray(img.dataobj) * 4

        res = func(img, 'myout')
        assert len(res) == 0
        checkdir(td,
                 op.join('myout_imgs', 'img2.nii.gz'),
                 op.join('myout_imgs', 'img4.nii.gz'))
        cleardir(td, 'myout*')

        res = func(img, 'myout', myout_imgs=wutils.LOAD)
        assert len(res) == 2
        assert np.all(np.asanyarray(res[op.join('myout_imgs', 'img2')].dataobj) == exp2)
        assert np.all(np.asanyarray(res[op.join('myout_imgs', 'img4')].dataobj) == exp4)

        res = func(img, 'myout', **{op.join('myout_imgs', 'img2') : wutils.LOAD})
        assert len(res) == 1
        assert np.all(np.asanyarray(res[op.join('myout_imgs', 'img2')].dataobj) == exp2)

        res = func(img, 'myout', **{op.join('myout_imgs', 'img') : wutils.LOAD})
        assert len(res) == 2
        assert np.all(np.asanyarray(res[op.join('myout_imgs', 'img2')].dataobj) == exp2)
        assert np.all(np.asanyarray(res[op.join('myout_imgs', 'img4')].dataobj) == exp4)

        os.mkdir('foo')
        res = func(img, op.join('foo', 'myout'))
        assert len(res) == 0
        checkdir(td,
                 op.join('foo', 'myout_imgs', 'img2.nii.gz'),
                 op.join('foo', 'myout_imgs', 'img4.nii.gz'))
        cleardir(td, 'foo')

        os.mkdir('foo')
        res = func(img, op.join('foo', 'myout'), **{op.join('foo', 'myout') : wutils.LOAD})
        assert len(res) == 2
        assert np.all(np.asanyarray(res[op.join('foo', 'myout_imgs', 'img2')].dataobj) == exp2)
        assert np.all(np.asanyarray(res[op.join('foo', 'myout_imgs', 'img4')].dataobj) == exp4)



def test_fileOrThing_results():
    @wutils.fileOrArray('input', 'regular_output', outprefix='outpref')
    def func(input, regular_output, outpref):

        input = np.loadtxt(input)

        regout   = input * 2
        prefouts = []
        for i in range(3, 6):
            prefouts.append(input * i)

        np.savetxt(regular_output, regout)
        for i, o in enumerate(prefouts):
            np.savetxt('{}_{}.txt'.format(outpref, i), o)

        return ('return', 'value')

    input  = np.random.randint(1, 10, (3, 3))
    infile = 'input.txt'
    exp    = [input * i for i in range(2, 6)]

    with tempdir.tempdir():

        np.savetxt(infile, input)

        result = func('input.txt', 'regout.txt', 'outpref')
        assert len(result) == 0
        assert result.stdout == ('return', 'value')
        assert (np.loadtxt('regout.txt') == exp[0]).all()
        for i in range(3):
            assert (np.loadtxt('outpref_{}.txt'.format(i)) == exp[i+1]).all()

        result = func(input, 'regout.txt', 'outpref')
        assert len(result) == 0
        assert result.stdout == ('return', 'value')
        assert (np.loadtxt('regout.txt') == exp[0]).all()
        for i in range(3):
            assert (np.loadtxt('outpref_{}.txt'.format(i)) == exp[i+1]).all()

        result = func(input, wutils.LOAD, 'outpref')
        assert len(result) == 1
        assert result.stdout == ('return', 'value')
        assert (result .regular_output == exp[0]).all()
        assert (result['regular_output'] == exp[0]).all()
        for i in range(3):
            assert (np.loadtxt('outpref_{}.txt'.format(i)) == exp[i+1]).all()

        # todo outpref
        result = func(input, wutils.LOAD, wutils.LOAD)
        assert len(result) == 4
        assert result.stdout == ('return', 'value')
        assert (result .regular_output == exp[0]).all()
        assert (result['regular_output'] == exp[0]).all()

        assert (result .outpref_0   == exp[1]).all()
        assert (result['outpref_0'] == exp[1]).all()
        assert (result .outpref_1   == exp[2]).all()
        assert (result['outpref_1'] == exp[2]).all()
        assert (result .outpref_2   == exp[3]).all()
        assert (result['outpref_2'] == exp[3]).all()

        for i in range(3):
            assert (np.loadtxt('outpref_{}.txt'.format(i)) == exp[i+1]).all()

        result = func(input, wutils.LOAD, wutils.LOAD)
        assert len(result) == 4


def test_FileOrThing_invalid_identifiers():
    # unlikely to ever happen, but let's test arguments with
    # names that are not valid python identifiers
    @wutils.fileOrArray('in val', '2out')
    def func(**kwargs):

        infile  = kwargs['in val']
        outfile = kwargs['2out']

        input = np.loadtxt(infile)
        np.savetxt(outfile, input * 2)

        return ('return', 'value')

    input  = np.random.randint(1, 10, (3, 3))
    infile = 'input.txt'
    exp    = input * 2

    with tempdir.tempdir():

        np.savetxt(infile, input)

        res = func(**{'in val' : infile, '2out' : 'output.txt'})
        assert res.stdout == ('return', 'value')
        assert (np.loadtxt('output.txt') == exp).all()

        res = func(**{'in val' : input, '2out' : 'output.txt'})
        assert res.stdout == ('return', 'value')
        assert (np.loadtxt('output.txt') == exp).all()

        res = func(**{'in val' : input, '2out' : wutils.LOAD})
        assert res.stdout == ('return', 'value')
        assert (res['2out'] == exp).all()



def test_chained_fileOrImageAndArray():
    @wutils.fileOrImage('image', 'outimage')
    @wutils.fileOrArray('array', 'outarray')
    def func(image, array, outimage, outarray):
        image = nib.load(image)
        array = np.loadtxt(array)

        outimg = nib.nifti1.Nifti1Image(np.asanyarray(image.dataobj) * 2, np.eye(4))

        np.savetxt(outarray, array * 2)
        outimg.to_filename(outimage)

    image = nib.nifti1.Nifti1Image(np.array([[1,  2], [ 3,  4]]), np.eye(4))
    array = np.array([[5, 6, 7, 8]])

    expimg = nib.nifti1.Nifti1Image(np.asanyarray(image.dataobj) * 2, np.eye(4))
    exparr = array * 2

    with tempdir.tempdir():

        nib.save(image, 'image.nii')
        np.savetxt('array.txt', array)

        func('image.nii', 'array.txt', 'outimg.nii', 'outarr.txt')
        assert np.all(np.asanyarray(nib.load('outimg.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('outarr.txt') == exparr)

        func('image.nii', array, 'outimg.nii', 'outarr.txt')
        assert np.all(np.asanyarray(nib.load('outimg.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('outarr.txt') == exparr)

        func( image, 'array.txt', 'outimg.nii', 'outarr.txt')
        assert np.all(np.asanyarray(nib.load('outimg.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('outarr.txt') == exparr)

        func( image, array, 'outimg.nii', 'outarr.txt')
        assert np.all(np.asanyarray(nib.load('outimg.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('outarr.txt') == exparr)

        res = func(image, array, wutils.LOAD, 'outarr.txt')
        assert np.all(np.asanyarray(res['outimage'].dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('outarr.txt') == exparr)

        res = func(image, array, 'outimg.nii', wutils.LOAD)
        assert np.all(np.asanyarray(nib.load('outimg.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(res['outarray'] == exparr)

        res = func(image, array, wutils.LOAD, wutils.LOAD)
        assert np.all(np.asanyarray(res['outimage'].dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(res['outarray'] == exparr)


def test_fileOrThing_chained_outprefix():

    import logging
    logging.basicConfig()
    logging.getLogger('fsl.wrappers').setLevel(logging.DEBUG)

    @wutils.fileOrImage('image', 'outimage', outprefix='out')
    @wutils.fileOrArray('array', 'outarray', outprefix='out')
    def func(image, array, out, **kwa):

        image = nib.load(image)
        array = np.loadtxt(array)

        outimg = nib.nifti1.Nifti1Image(np.asanyarray(image.dataobj) * 2, np.eye(4))
        outarr = array * 2

        np.savetxt('{}_array.txt'.format(out), outarr)
        outimg.to_filename('{}_image.nii'.format(out))

    image = nib.nifti1.Nifti1Image(np.array([[1,  2], [ 3,  4]]), np.eye(4))
    array = np.array([[5, 6, 7, 8]])

    expimg = nib.nifti1.Nifti1Image(np.asanyarray(image.dataobj) * 2, np.eye(4))
    exparr = array * 2

    with tempdir.tempdir():

        func(image, array, 'myout')
        assert np.all(np.asanyarray(nib.load('myout_image.nii').dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(np.loadtxt('myout_array.txt') == exparr)

        res = func(image, array, wutils.LOAD)
        assert np.all(np.asanyarray(res['out_image'].dataobj) == np.asanyarray(expimg.dataobj))
        assert np.all(res['out_array'] == exparr)


def test_fileOrThing_submit_cmdonly():

    @wutils.fileOrImage('input', 'output')
    def func(input, output, submit=False, cmdonly=False):

        if submit:
            return 'submitted!'
        if cmdonly:
            return 'cmdonly!'

        img = nib.load(input)
        img = nib.nifti1.Nifti1Image(np.asanyarray(img.dataobj) * 2, np.eye(4))

        nib.save(img, output)

    with tempdir.tempdir() as td:
        img = nib.nifti1.Nifti1Image(np.array([[1, 2], [3, 4]]), np.eye(4))
        exp = np.asanyarray(img.dataobj) * 2
        nib.save(img, 'input.nii.gz')

        result = func(img, wutils.LOAD)
        assert np.all(np.asanyarray(result['output'].dataobj) == exp)

        assert func('input.nii.gz', 'output.nii.gz', submit=True)  == 'submitted!'
        assert func('input.nii.gz', 'output.nii.gz', cmdonly=True) == 'cmdonly!'

        with pytest.raises(ValueError):
            func(img, wutils.LOAD, submit=True)
        with pytest.raises(ValueError):
            func(img, 'output.nii.gz', submit=True)
        with pytest.raises(ValueError):
            func('input.nii.gz', wutils.LOAD, submit=True)


def test_cmdwrapper():
    @wutils.cmdwrapper
    def func(a, b):
        return ['func', str(a), str(b)]

    with run.dryrun():
        assert func(1, 2)[0] == 'func 1 2'

    assert func(1, 2, cmdonly=True) == ['func', '1', '2']


def test_fslwrapper():
    @wutils.fslwrapper
    def func(a, b):
        return ['func', str(a), str(b)]

    with mockFSLDIR(bin=('func',)) as fsldir:
        expected = '{} 1 2'.format(op.join(fsldir, 'bin', 'func'))
        with run.dryrun():
            assert func(1, 2)[0] == expected

        assert func(1, 2, cmdonly=True) == list(shlex.split(expected))


_test_script = textwrap.dedent("""
#!/usr/bin/env bash
echo "test_script running: $1 $2"
exit 0
""").strip()


def _test_script_func(a, b):
    return ['test_script', str(a), str(b)]


@pytest.mark.unixtest
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

        assert jid == '12345'

        stdout, stderr = fslsub.output('12345')

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == ''


@pytest.mark.unixtest
def test_fslwrapper_submit():

    test_func = wutils.fslwrapper(_test_script_func)

    with mockFSLDIR() as fsldir, \
         mock.patch('fsl.utils.fslsub.submit', mock_submit):

        test_file = op.join(fsldir, 'bin', 'test_script')

        with open(test_file, 'wt') as f:
            f.write(_test_script)
        os.chmod(test_file, 0o755)

        jid = test_func(1, 2, submit=True)

        assert jid == '12345'

        stdout, stderr = fslsub.output('12345')

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == ''

        kwargs = {'name' : 'abcde', 'ram' : '4GB'}

        jid = test_func(1, 2, submit=kwargs)

        assert jid == '12345'

        stdout, stderr = fslsub.output('12345')

        experr = '\n'.join(['{}: {}'.format(k, kwargs[k])
                            for k in sorted(kwargs.keys())])

        assert stdout.strip() == 'test_script running: 1 2'
        assert stderr.strip() == experr


@pytest.mark.unixtest
def test_cmdwrapper_fileorthing_cmdonly():

    test_func = wutils.fileOrImage('a')(wutils.cmdwrapper(_test_script_func))
    newpath   = op.pathsep.join(('.', os.environ['PATH']))
    with tempdir.tempdir(), \
         mock.patch.dict(os.environ, {'PATH' : newpath}):

        with open('test_script', 'wt') as f:
            f.write(_test_script)
        os.chmod('test_script', 0o755)

        ran = test_func('1', '2')
        cmd = test_func('1', '2', cmdonly=True)
        assert ran.stdout[0].strip() == 'test_script running: 1 2'
        assert cmd                   == ['test_script', '1', '2']


def test_cmdwrapper_cmdonly_assert():

    @wutils.cmdwrapper
    def func():
        asrt.assertFileExists('file')
        return ['echo', 'hello']

    with tempdir.tempdir():
        with pytest.raises(AssertionError):
            func()
        touch('file')
        assert func()[0].strip() == 'hello'
        os.remove('file')
        assert func(cmdonly=True) == ['echo', 'hello']
