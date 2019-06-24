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

    with tempdir.tempdir():
        data = np.random.randint(0, 255, (100, 200, 4), dtype=np.uint8)
        img  = Image.fromarray(data, mode='RGBA')

        img.save('image.png')

        bmp = fslbmp.Bitmap('image.png')

        assert bmp.name       == 'image.png'
        assert bmp.dataSource == 'image.png'
        assert bmp.shape      == (200, 100, 4)

        repr(bmp)
        hash(bmp)

        assert np.all(bmp.data == np.fliplr(data.transpose(1, 0, 2)))


@pytest.mark.piltest
def test_bitmap_asImage():
    from PIL import Image

    with tempdir.tempdir():
        d3 = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        d4 = np.random.randint(0, 255, (100, 200, 4), dtype=np.uint8)

        img3 = Image.fromarray(d3, mode='RGB')
        img4 = Image.fromarray(d4, mode='RGBA')

        img3.save('rgb.png')
        img4.save('rgba.png')

        bmp3  = fslbmp.Bitmap('rgb.png')
        bmp4  = fslbmp.Bitmap('rgba.png')

        i3 = bmp3.asImage()
        i4 = bmp4.asImage()

        assert i3.shape == (200, 100, 1)
        assert i4.shape == (200, 100, 1)
        assert i3.nvals == 3
        assert i4.nvals == 4
