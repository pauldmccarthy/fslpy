#!/usr/bin/env python
#
# test_assertions.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import            os
import os.path as op

import pytest

import fsl.utils.assertions as assertions
import fsl.utils.tempdir    as tempdir

from . import make_random_image
from . import testdir


def test_assertFileExists():


    with tempdir.tempdir():
        open('file.txt', 'wt').close()
        os.makedirs(op.join('path', 'to', 'some', 'dir'))
        open(op.join('path', 'to', 'file.txt'), 'wt').close()


        assertions.assertFileExists('file.txt')
        assertions.assertFileExists(op.join('path', 'to', 'some', 'dir'))
        assertions.assertFileExists(op.join('path', 'to', 'file.txt'))
        assertions.assertFileExists('file.txt', op.join('path'))

        with pytest.raises(AssertionError):
            assertions.assertFileExists(op.join('not', 'a', 'directory'))
        with pytest.raises(AssertionError):
            assertions.assertFileExists('notafile.txt')
        with pytest.raises(AssertionError):
            assertions.assertFileExists('file.txt', 'notafile.txt')


def test_assertIsNifti3D():
    _test_assertIsNiftiND(3)

def test_assertIsNifti4D():
    _test_assertIsNiftiND(4)

def _test_assertIsNiftiND(ndims):

    if   ndims == 3: assertFunc = assertions.assertIsNifti3D
    elif ndims == 4: assertFunc = assertions.assertIsNifti4D

    tests = [((10, ),               False),
             ((10, 10),             False),
             ((10, 10, 10),         ndims == 3),
             ((10, 10, 10, 10),     ndims == 4),
             ((10, 10, 10, 10, 10), False)]

    with tempdir.tempdir():

        for shape, expected in tests:
            img = make_random_image('test.nii', dims=shape)

            if expected:
                assertFunc(img)
                assertFunc('test.nii')
            else:
                with pytest.raises(AssertionError):
                    assertFunc(img)
                with pytest.raises(AssertionError):
                    assertFunc('test.nii')


def test_assertIsNifti():

    with tempdir.tempdir():
        analyze = make_random_image('analyze.img', imgtype=0)
        nifti1  = make_random_image('nifti1.nii',  imgtype=1)
        nifti2  = make_random_image('nifti2.nii',  imgtype=2)

        with pytest.raises(AssertionError):
            assertions.assertIsNifti(analyze)
        with pytest.raises(AssertionError):
            assertions.assertIsNifti('analyze.img')

        assertions.assertIsNifti(nifti1)
        assertions.assertIsNifti('nifti1.nii')
        assertions.assertIsNifti(nifti2)
        assertions.assertIsNifti('nifti2.nii')
        assertions.assertIsNifti(nifti1, nifti2)


def test_assertNiftiShape():
    with tempdir.tempdir():
        shape3d = (10, 11, 12)
        shape4d = (10, 11, 12, 13)

        img3d = make_random_image('3d.nii', dims=shape3d)
        img4d = make_random_image('4d.nii', dims=shape4d)

        assertions.assertNiftiShape(shape3d, img3d)
        assertions.assertNiftiShape(shape3d, '3d.nii')
        assertions.assertNiftiShape(shape4d, img4d)
        assertions.assertNiftiShape(shape4d, '4d.nii')

        assertions.assertNiftiShape(shape3d, img3d, '3d.nii')
        assertions.assertNiftiShape(shape4d, img4d, '4d.nii')

        with pytest.raises(AssertionError):
            assertions.assertNiftiShape(shape3d, img4d)
        with pytest.raises(AssertionError):
            assertions.assertNiftiShape(shape3d, '4d.nii')
        with pytest.raises(AssertionError):
            assertions.assertNiftiShape(shape4d, img3d)
        with pytest.raises(AssertionError):
            assertions.assertNiftiShape(shape4d, '3d.nii')


def test_assertIsSurfGifti():
    tests = [
        ('blah.surf.gii',    True),
        ('lh.pial.surf.gii', True),
        ('blah.func.gii',    False),
        ('blah.nii',         False),
    ]

    for test, expected in tests:

        if expected:
            assertions.assertIsSurfGifti(test)
        else:
            with pytest.raises(AssertionError):
                assertions.assertIsSurfGifti(test)


def test_assertIsFuncGifti():
    tests = [
        ('blah.func.gii',    True),
        ('lh.pial.func.gii', True),
        ('blah.surf.gii',    False),
        ('blah.nii',         False),
    ]

    for test, expected in tests:

        if expected:
            assertions.assertIsFuncGifti(test)
        else:
            with pytest.raises(AssertionError):
                assertions.assertIsFuncGifti(test)


def test_assertIsMelodicDir():

    # dirname suffix, contents, expected result
    tests = [
        ('analysis.ica', ['melodic_IC.nii.gz',  'melodic_mix', 'melodic_FTmix'], True),
        ('analysis.ica', ['melodic_oIC.nii.gz', 'melodic_mix', 'melodic_FTmix'], True),
        ('analysis.ica', [                      'melodic_mix', 'melodic_FTmix'], False),
        ('analysis.ica', ['melodic_IC.nii.gz',                 'melodic_FTmix'], False),
        ('analysis.ica', ['melodic_IC.nii.gz',  'melodic_mix'],                  False),
        ('analysis',     ['melodic_IC.nii.gz',  'melodic_mix', 'melodic_FTmix'], False),
        ('analysis',     ['melodic_oIC.nii.gz', 'melodic_mix', 'melodic_FTmix'], False),
    ]

    for dirname, paths, expected in tests:
        with testdir(paths, dirname):
            if expected:
                assertions.assertIsMelodicDir(dirname)
            else:
                with pytest.raises(AssertionError):
                    assertions.assertIsMelodicDir(dirname)
