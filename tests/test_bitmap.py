#!/usr/bin/env python
#
# test_bitmap.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import pytest

import fsl.utils.tempdir as tempdir
import fsl.data.bitmap   as fslbmp


@pytest.mark.piltest
def test_bitmap():

    from PIL import Image

    nchannels = (1, 3, 4)

    with tempdir.tempdir():

        for nch in nchannels:
            data = np.random.randint(0, 255, (100, 200, nch), dtype=np.uint8)
            img  = Image.fromarray(data.squeeze())

            fname = 'image.png'
            img.save(fname)

            bmp1 = fslbmp.Bitmap(fname)
            bmp2 = fslbmp.Bitmap(data)

            assert bmp1.name       == fname
            assert bmp1.dataSource == fname
            assert bmp1.shape      == (200, 100, nch)
            assert bmp2.shape      == (200, 100, nch)

            repr(bmp1)
            hash(bmp1)

            assert np.all(bmp1.data == np.fliplr(data.transpose(1, 0, 2)))
            assert np.all(bmp2.data == np.fliplr(data.transpose(1, 0, 2)))


@pytest.mark.piltest
def test_bitmap_asImage():
    from PIL import Image

    with tempdir.tempdir():
        d3 = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        d4 = np.random.randint(0, 255, (100, 200, 4), dtype=np.uint8)

        img3 = Image.fromarray(d3, mode='RGB')
        img4 = Image.fromarray(d4, mode='RGBA')
        img1 = img3.convert(mode='P')

        img3.save('rgb.png')
        img4.save('rgba.png')
        img1.save('p.png')

        bmp3 = fslbmp.Bitmap('rgb.png')
        bmp4 = fslbmp.Bitmap('rgba.png')
        bmp1 = fslbmp.Bitmap('p.png')

        i3   = bmp3.asImage()
        i4   = bmp4.asImage()
        i1   = bmp1.asImage()

        assert i3.shape == (200, 100, 1)
        assert i4.shape == (200, 100, 1)
        assert i1.shape == (200, 100, 1)
        assert i3.nvals == 3
        assert i4.nvals == 4
        assert i1.nvals == 3
