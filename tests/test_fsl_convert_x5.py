#!/usr/bin/env python


import numpy as np

import fsl.utils.tempdir as tempdir
import fsl.transform     as transform
import fsl.data.image    as fslimage

import fsl.scripts.fsl_convert_x5 as fsl_convert_x5


def random_image():
    vx, vy, vz = np.random.randint(10, 50, 3)
    dx, dy, dz = np.random.randint( 1, 10, 3)
    data       = (np.random.random((vx, vy, vz)) - 0.5) * 10
    aff        = transform.compose(
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

        xform = transform.compose(
            np.random.randint(1, 10, 3),
            np.random.randint(-100, 100, 3),
            (np.random.random(3) - 0.5) * np.pi)

        np.savetxt('src2ref.mat', xform)

        fsl_convert_x5.main('flirt -s src -r ref '
                            'src2ref.mat src2ref.x5'.split())
        expxform = transform.concat(
            ref.getAffine('fsl', 'world'),
            xform,
            src.getAffine('world', 'fsl'))
        gotxform, gotsrc, gotref = transform.readFlirtX5('src2ref.x5')
        assert np.all(np.isclose(gotxform, expxform))
        assert src.sameSpace(gotsrc)
        assert ref.sameSpace(gotref)

        fsl_convert_x5.main('flirt -s src -r ref src2ref.x5 '
                            'src2ref_copy.mat'.split())

        gotxform = transform.readFlirt('src2ref_copy.mat')
        assert np.all(np.isclose(gotxform, xform))
