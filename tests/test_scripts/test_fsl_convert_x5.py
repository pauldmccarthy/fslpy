#!/usr/bin/env python


import os.path as op

import numpy as np

import fsl.utils.tempdir    as tempdir
import fsl.transform.affine as affine
import fsl.transform.flirt  as flirt
import fsl.transform.fnirt  as fnirt
import fsl.transform.x5     as x5
import fsl.data.image       as fslimage

import fsl.scripts.fsl_convert_x5 as fsl_convert_x5



def random_image():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)
    data       = (np.random.random((vx, vy, vz)) - 0.5) * 10
    aff        = affine.compose(
        (dx, dy, dz),
        np.random.randint(1, 100, 3),
        np.random.random(3) * np.pi / 2)

    return fslimage.Image(data, xform=aff)



def test_convert_flirt():
    with tempdir.tempdir():
        src = random_image()
        ref = random_image()
        src.save('src')
        ref.save('ref')

        xform = affine.compose(
            np.random.randint(1, 10, 3),
            np.random.randint(-100, 100, 3),
            (np.random.random(3) - 0.5) * np.pi)

        np.savetxt('src2ref.mat', xform)

        fsl_convert_x5.main('flirt -s src -r ref '
                            'src2ref.mat src2ref.x5'.split())
        expxform = affine.concat(
            ref.getAffine('fsl', 'world'),
            xform,
            src.getAffine('world', 'fsl'))
        gotxform, gotsrc, gotref = x5.readLinearX5('src2ref.x5')
        assert np.all(np.isclose(gotxform, expxform))
        assert src.sameSpace(gotsrc)
        assert ref.sameSpace(gotref)

        fsl_convert_x5.main('flirt src2ref.x5 src2ref_copy.mat'.split())

        gotxform = flirt.readFlirt('src2ref_copy.mat')
        assert np.all(np.isclose(gotxform, xform))


def test_convert_fnirt_displacement_field():

    datadir = op.join(op.dirname(__file__), '..',
                      'test_transform', 'testdata', 'nonlinear')
    srcfile = op.join(datadir, 'src.nii.gz')
    reffile = op.join(datadir, 'ref.nii.gz')
    dffile  = op.join(datadir, 'displacementfield.nii.gz')

    with tempdir.tempdir():

        # nii -> x5
        fsl_convert_x5.main('fnirt -s {} -r {} {} disp.x5'.format(
            srcfile, reffile, dffile).split())

        # x5 -> nii
        fsl_convert_x5.main('fnirt disp.x5 disp.nii.gz'.split())

        src   = fslimage.Image(srcfile)
        ref   = fslimage.Image(reffile)
        df    = fnirt.readFnirt(dffile, src, ref)
        dfnii = fnirt.readFnirt('disp.nii.gz', src, ref)

        assert dfnii.src.sameSpace(src)
        assert dfnii.ref.sameSpace(ref)
        assert dfnii.srcSpace == df.srcSpace
        assert dfnii.refSpace == df.refSpace
        assert dfnii.displacementType == df.displacementType
        assert np.all(np.isclose(dfnii.data, df.data))


def test_convert_fnirt_coefficient_field():

    datadir = op.join(op.dirname(__file__), '..',
                      'test_transform', 'testdata', 'nonlinear')
    srcfile = op.join(datadir, 'src.nii.gz')
    reffile = op.join(datadir, 'ref.nii.gz')
    cffile  = op.join(datadir, 'coefficientfield.nii.gz')

    with tempdir.tempdir():

        # nii -> x5
        fsl_convert_x5.main('fnirt -s {} -r {} {} coef.x5'.format(
            srcfile, reffile, cffile).split())

        # x5 -> nii
        fsl_convert_x5.main('fnirt coef.x5 coef.nii.gz'.split())

        src   = fslimage.Image(srcfile)
        ref   = fslimage.Image(reffile)
        cf    = fnirt.readFnirt(cffile, src, ref)
        cfnii = fnirt.readFnirt('coef.nii.gz', src, ref)

        assert cfnii.src.sameSpace(src)
        assert cfnii.ref.sameSpace(ref)
        assert cfnii.srcSpace    == cf.srcSpace
        assert cfnii.refSpace    == cf.refSpace
        assert cfnii.knotSpacing == cf.knotSpacing

        assert np.all(np.isclose(cfnii.fieldToRefMat, cf.fieldToRefMat))
        assert np.all(np.isclose(cfnii.srcToRefMat,   cf.srcToRefMat))
        assert np.all(np.isclose(cfnii.data,          cf.data))
