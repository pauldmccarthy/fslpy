#!/usr/bin/env python
#
# fslmaths.py - Wrapper for fslmaths.
#
# Author: Sean Fitzgibbon <sean.fitzgibbon@ndcn.ox.ac.uk>
#
"""This module provides the :class:`fslmaths` class, which acts as a wrapper
for the ``fslmaths`` command-line tool.
"""


import fsl.utils.run as run


class fslmaths(object):
    """Perform mathematical manipulation of images."""

    def __init__(self, input):
        """Constructor."""
        self.inputImage = input
        self.outputImage = None
        self.operations = []

    def abs(self):
        """Absolute value."""
        self.operations.append("-abs")
        return self

    def bin(self):
        """Use (current image>0) to binarise."""
        self.operations.append("-bin")
        return self

    def binv(self):
        """Binarise and invert (binarisation and logical inversion)."""
        self.operations.append("-binv")
        return self

    def recip(self):
        """Reciprocal (1/current image)."""
        self.operations.append("-recip")
        return self

    def Tmean(self):
        """Mean across time."""
        self.operations.append("-Tmean")
        return self

    def Tstd(self):
        """Standard deviation across time."""
        self.operations.append("-Tstd")
        return self

    def Tmin(self):
        """Min across time."""
        self.operations.append("-Tmin")
        return self

    def Tmax(self):
        """Max across time."""
        self.operations.append("-Tmax")
        return self

    def fillh(self):
        """fill holes in a binary mask (holes are internal - i.e. do not touch
        the edge of the FOV)."""
        self.operations.append("-fillh")
        return self

    def ero(self, repeat=1):
        """Erode by zeroing non-zero voxels when zero voxels in kernel."""
        for i in range(repeat):
            self.operations.append("-ero")
        return self

    def dilM(self, repeat=1):
        """Mean Dilation of non-zero voxels."""
        for i in range(repeat):
            self.operations.append("-dilM")
        return self

    def dilF(self, repeat=1):
        """Maximum filtering of all voxels."""
        for i in range(repeat):
            self.operations.append("-dilF")
        return self

    def add(self, input):
        """Add input to current image."""
        self.operations.append("-add {0}".format(input))
        return self

    def sub(self, input):
        """Subtract input from current image."""
        self.operations.append("-sub {0}".format(input))
        return self

    def mul(self, input):
        """Multiply current image by input."""
        self.operations.append("-mul {0}".format(input))
        return self

    def div(self, input):
        """Divide current image by input."""
        self.operations.append("-div {0}".format(input))
        return self

    def mas(self, image):
        """Use image (>0) to mask current image."""
        self.operations.append("-mas {0}".format(image))
        return self

    def rem(self, input):
        """Divide current image by following input and take remainder."""
        self.operations.append("-rem {0}".format(input))
        return self

    def thr(self, input):
        """use input number to threshold current image (zero < input)."""
        self.operations.append("-thr {0}".format(input))
        return self

    def uthr(self, input):
        """use input number to upper-threshold current image (zero
        anything above the number)."""
        self.operations.append("-uthr {0}".format(input))
        return self

    def inm(self, input):
        """Intensity normalisation (per 3D volume mean)"""
        self.operations.append("-inm {0}".format(input))
        return self

    def bptf(self, hp_sigma, lp_sigma):
        """Bandpass temporal filtering; nonlinear highpass and Gaussian linear
        lowpass (with sigmas in volumes, not seconds); set either sigma<0 to
        skip that filter."""
        self.operations.append("-bptf {0} {1}".format(hp_sigma, lp_sigma))
        return self

    def toString(self):
        """Generate fslmaths command string."""
        cmd = "fslmaths {0} ".format(self.inputImage)
        for oper in self.operations:
            cmd = cmd + oper + " "
        cmd = cmd + self.outputImage
        return cmd

    def run(self, output=None):
        """Save output of operations to image."""
        if output:
            self.outputImage = output
        else:
            self.outputImage = self.inputImage

        run.runfsl(self.toString())

        return self.outputImage
