#!/usr/bin/env python
#
# fslmaths.py - Wrapper for fslmaths.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
#
"""This module provides the :class:`fslmaths` class, which acts as a wrapper
for the ``fslmaths`` command-line tool.
"""


from . import wrapperutils as wutils


class fslmaths(object):
    """Perform mathematical manipulation of images.

    ``fslmaths`` is unlike the other FSL wrapper tools in that it provides an
    object-oriented method-chaining interface, which is hopefully easier to
    use than constructing a ``fslmaths`` command-line call. For example, the
    following call to the ``fslmaths`` wrapper function::

        fslmaths('input.nii').thr(0.25).mul(-1).run('output.nii')

    will be translated into the following command-line call::

        fslmaths input.nii -thr 0.25 -mul -1 output.nii

    The ``fslmaths`` wrapper function can also be used with in-memory
    images. If no output file name is passed to the :meth:`run` method, the
    result is loaded into memory and returned as a ``nibabel`` image.  For
    example::

        import nibabel as nib
        input  = nib.load('input.nii')
        output = fslmaths(input).thr(0.25).mul(-1).run()
    """

    def __init__(self, input):
        """Constructor."""
        self.__input = input
        self.__args  = []

    def abs(self):
        """Absolute value."""
        self.__args.append("-abs")
        return self

    def bin(self):
        """Use (current image>0) to binarise."""
        self.__args.append("-bin")
        return self

    def binv(self):
        """Binarise and invert (binarisation and logical inversion)."""
        self.__args.append("-binv")
        return self

    def recip(self):
        """Reciprocal (1/current image)."""
        self.__args.append("-recip")
        return self

    def Tmean(self):
        """Mean across time."""
        self.__args.append("-Tmean")
        return self

    def Tstd(self):
        """Standard deviation across time."""
        self.__args.append("-Tstd")
        return self

    def Tmin(self):
        """Min across time."""
        self.__args.append("-Tmin")
        return self

    def Tmax(self):
        """Max across time."""
        self.__args.append("-Tmax")
        return self

    def fillh(self):
        """fill holes in a binary mask (holes are internal - i.e. do not touch
        the edge of the FOV)."""
        self.__args.append("-fillh")
        return self

    def ero(self, repeat=1):
        """Erode by zeroing non-zero voxels when zero voxels in kernel."""
        for i in range(repeat):
            self.__args.append("-ero")
        return self

    def dilM(self, repeat=1):
        """Mean Dilation of non-zero voxels."""
        for i in range(repeat):
            self.__args.append("-dilM")
        return self

    def dilF(self, repeat=1):
        """Maximum filtering of all voxels."""
        for i in range(repeat):
            self.__args.append("-dilF")
        return self

    def smooth(self, sigma):
        """Spatial smoothing - mean filtering using a gauss kernel of sigma mm"""
        self.__args.extend(("-s", sigma))
        return self

    def add(self, image):
        """Add input to current image."""
        self.__args.extend(("-add", image))
        return self

    def sub(self, image):
        """Subtract image from current image."""
        self.__args.extend(("-sub", image))
        return self

    def mul(self, image):
        """Multiply current image by image."""
        self.__args.extend(("-mul", image))
        return self

    def div(self, image):
        """Divide current image by image."""
        self.__args.extend(("-div", image))
        return self

    def mas(self, image):
        """Use image (>0) to mask current image."""
        self.__args.extend(("-mas", image))
        return self

    def rem(self, image):
        """Divide current image by following image and take remainder."""
        self.__args.extend(("-rem", image))
        return self

    def thr(self, image):
        """use image number to threshold current image (zero < image)."""
        self.__args.extend(("-thr", image))
        return self

    def uthr(self, image):
        """use image number to upper-threshold current image (zero
        anything above the number)."""
        self.__args.extend(("-uthr", image))
        return self

    def inm(self, image):
        """Intensity normalisation (per 3D volume mean)"""
        self.__args.extend(("-inm", image))
        return self

    def bptf(self, hp_sigma, lp_sigma):
        """Bandpass temporal filtering; nonlinear highpass and Gaussian linear
        lowpass (with sigmas in volumes, not seconds); set either sigma<0 to
        skip that filter."""
        self.__args.extend(("-bptf", hp_sigma, lp_sigma))
        return self

    def run(self, output=None):
        """Save output of operations to image. Set ``output`` to a filename to have
        the result saved to file, or omit ``output`` entirely to have the
        result returned as a ``nibabel`` image.
        """

        cmd = ['fslmaths', self.__input] + self.__args

        if output is None:
            output = wutils.LOAD

        cmd   += [output]
        result = self.__run(*cmd)

        # if output is LOADed, there
        # will only be one entry in
        # the result dict.
        if output == wutils.LOAD: return list(result.values())[0]
        else:                     return result

    @wutils.fileOrImage()
    @wutils.fslwrapper
    def __run(self, *cmd):
        """Run the given ``fslmaths`` command. """
        return [str(c) for c in cmd]
