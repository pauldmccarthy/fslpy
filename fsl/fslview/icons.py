#!/usr/bin/env python
#
# icons.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
import os.path as op
import glob

import wx


_bitmapPath = op.join(op.dirname(__file__), 'icons')


def findImageFile(iconId, size):

    path      = op.join(_bitmapPath, '{}_*png'.format(iconId))
    files     = glob.glob(path)
    fileNames = map(op.basename, files)
    filePrefs = [op.splitext(f)[0] for f in fileNames]
    sizes     = map(int, [fp.split('_')[1] for fp in filePrefs])

    if len(sizes) == 0:
        raise ValueError('Invalid icon ID: {}'.format(iconId))

    sizeDiffs = map(abs, [s - size for s in sizes])
    idx       = sizeDiffs.index(min(sizeDiffs))

    return files[idx], sizes[idx]


def _resizeImage(image, size):
    
    w, h = image.GetSize().Get()

    if w >= h:
        h = size * h / float(w)
        w = size
    else:
        w = size * (w / float(h)) 
        h = size

    image.Rescale(w, h, wx.IMAGE_QUALITY_BICUBIC)
    return image


def loadImage(iconId, size=None):

    filename, fSize = findImageFile(iconId, size)
    img             = wx.Image(filename)

    if fSize != size: return _resizeImage(img, size)
    else:             return img


def loadBitmap(iconId, size=None):
    return wx.BitmapFromImage(loadImage(iconId, size))
