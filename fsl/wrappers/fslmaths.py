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


class fslmaths:
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

    def __init__(self, input, dt=None):
        """Constructor."""
        self.__input = input
        self.__args  = []

        if dt is not None:
            self.__args.extend(('-dt',  dt))

    def addargs(func):
        """Decorator used by fslmaths methods. Allows them to just return
        a list of arguments to add to the command invocation.
        """
        def wrapper(self, *args, **kwargs):
            args = func(self, *args, **kwargs)
            self.__args.extend(args)
            return self
        return wrapper

    # Binary operations

    @addargs
    def add(self, image):
        """Add input to current image."""
        return ['-add', image]

    @addargs
    def sub(self, image):
        """Subtract image from current image."""
        return ["-sub", image]

    @addargs
    def mul(self, image):
        """Multiply current image by image."""
        return ["-mul", image]

    @addargs
    def div(self, image):
        """Divide current image by image."""
        return ["-div", image]

    @addargs
    def rem(self, image):
        """Divide current image by following image and take remainder."""
        return ["-rem", image]

    @addargs
    def mas(self, image):
        """Use image (>0) to mask current image."""
        return ["-mas", image]

    @addargs
    def thr(self, image):
        """threshold below the following number (zero anything below the
        number)"""
        return ["-thr", image]

    @addargs
    def thrp(self, perc):
        """threshold below the following percentage (0-100) of ROBUST RANGE"""
        return ["-thrp", perc]

    @addargs
    def thrP(self, perc):
        """threshold below the following percentage (0-100) of the positive
        voxels' ROBUST RANGE"""
        return ["-thrP", perc]

    @addargs
    def uthr(self, image):
        """use image number to upper-threshold current image (zero
        anything above the number)."""
        return ["-uthr", image]

    @addargs
    def uthrp(self, perc):
        """upper-threshold above the following percentage (0-100) of the
        ROBUST RANGE"""
        return ["-uthrp", perc]

    @addargs
    def uthrP(self, perc):
        """upper-threshold above the following percentage (0-100) of the
        positive voxels' ROBUST RANGE"""
        return ["-uthrP", perc]

    @addargs
    def max(self, image):
        """take maximum of following input and current image."""
        return ["-max", image]

    @addargs
    def min(self, image):
        """take minimum of following input and current image."""
        return ["-min", image]

    @addargs
    def seed(self, seed):
        """seed random number generator with following number"""
        return ['-seed', seed]

    @addargs
    def restart(self, image):
        """replace the current image with input for future processing
        operations"""
        return ['-restart', image]

    @addargs
    def save(self, filename):
        """save the current working image to the input filename"""
        return ['-save', filename]

    # Basic unary operations

    @addargs
    def exp(self):
        """exponential"""
        return ["-exp"]

    @addargs
    def log(self):
        """Natural logarithm."""
        return ["-log"]

    @addargs
    def sin(self):
        """sine function"""
        return ["-sin"]

    @addargs
    def cos(self):
        """cosine function"""
        return ["-cos"]

    @addargs
    def tan(self):
        """tangent function"""
        return ["-tan"]

    @addargs
    def asin(self):
        """arc sine function"""
        return ["-asin"]

    @addargs
    def acos(self):
        """arc cosine function"""
        return ["-acos"]

    @addargs
    def atan(self):
        """arc tangent function"""
        return ["-atan"]

    @addargs
    def sqr(self):
        """Square."""
        return ["-sqr"]

    @addargs
    def sqrt(self):
        """Square root."""
        return ["-sqrt"]

    @addargs
    def recip(self):
        """Reciprocal (1/current image)."""
        return ["-recip"]

    @addargs
    def abs(self):
        """Absolute value."""
        return ["-abs"]

    @addargs
    def bin(self):
        """Use (current image>0) to binarise."""
        return ["-bin"]

    @addargs
    def binv(self):
        """Binarise and invert (binarisation and logical inversion)."""
        return ["-binv"]

    @addargs
    def fillh(self):
        """fill holes in a binary mask (holes are internal - i.e. do not touch
        the edge of the FOV)."""
        return ["-fillh"]

    @addargs
    def fillh26(self):
        """fill holes using 26 connectivity"""
        return ["-fillh26"]

    @addargs
    def index(self):
        """replace each nonzero voxel with a unique (subject to wrapping) index
        number"""
        return ["-index"]

    @addargs
    def grid(self, value, spacing):
        """add a 3D grid of intensity <value> with grid spacing <spacing>"""
        return ['-grid', value, spacing]

    @addargs
    def edge(self):
        """edge strength"""
        return ["-edge"]

    @addargs
    def dog_edge(self, sigma1, sigma2):
        """difference of gaussians edge filter. Typical sigma1 is 1.0 and
        sigma2 is 1.6
        """
        return ['-dog_edge', sigma1, sigma2]

    @addargs
    def tfce(self, h, e, connectivity):
        """enhance with TFCE, e.g. -tfce 2 0.5 6 (maybe change 6 to 26 for
        skeletons)
        """
        return ['-tfce', h, e, connectivity]

    @addargs
    def tfceS(self, h, e, connectivity, x, y, z, tfce_thresh):
        """show support area for voxel (X,Y,Z)"""
        return ['-tfceS', h, e, connectivity, x, y, z, tfce_thresh]

    @addargs
    def nan(self):
        """replace NaNs (improper numbers) with 0"""
        return ["-nan"]

    @addargs
    def nanm(self):
        """make NaN (improper number) mask with 1 for NaN voxels, 0 otherwise"""
        return ["-nanm"]

    @addargs
    def rand(self):
        """add uniform noise (range 0:1)"""
        return ["-rand"]

    @addargs
    def randn(self):
        """add Gaussian noise (mean=0 sigma=1)"""
        return ["-randn"]

    @addargs
    def inm(self, image):
        """Intensity normalisation (per 3D volume mean)"""
        return ["-inm", image]

    @addargs
    def ing(self, image):
        """intensity normalisation, global 4D mean)"""
        return ["-ing", image]

    @addargs
    def range(self):
        """Set the output calmin/max to full data range."""
        return ["-range"]

    # Matrix operations

    @addargs
    def tensor_decomp(self):
        """convert a 4D (6-timepoint )tensor image into L1,2,3,FA,MD,MO,V1,2,3
        (remaining image in pipeline is FA)
        """
        return ["-tensor_decomp"]

    @addargs
    def kernel(self, *args):
        """Perform a kernel operation"""
        return ["-kernel"] + list(args)

    # Spatial filtering

    @addargs
    def dilM(self, repeat=1):
        """Mean Dilation of non-zero voxels."""
        return ['-dilM'] * repeat

    @addargs
    def dilD(self, repeat=1):
        """Modal Dilation of non-zero voxels."""
        return ["-dilD"] * repeat

    @addargs
    def dilF(self, repeat=1):
        """Maximum filtering of all voxels."""
        return ["-dilF"] * repeat

    @addargs
    def dilall(self):
        """Apply -dilM repeatedly until the entire FOV is covered"""
        return ["-dilall"]

    @addargs
    def ero(self, repeat=1):
        """Erode by zeroing non-zero voxels when zero voxels in kernel."""
        return ["-ero"] * repeat

    @addargs
    def eroF(self, repeat=1):
        """Minimum filtering of all voxels"""
        return ["-eroF"] * repeat

    @addargs
    def fmedian(self):
        """Median filtering"""
        return ["-fmedian"]

    @addargs
    def fmean(self):
        """Mean filtering, kernel weighted, (conventionally used with gauss kernel)"""
        return ["-fmean"]

    @addargs
    def fmeanu(self):
        """Mean filtering, kernel weighted, un-normalised (gives edge effects)"""
        return ["-fmeanu"]

    @addargs
    def s(self, sigma):
        """Create a gauss kernel of sigma mm and perform mean filtering"""
        return ["-s", sigma]

    # alias for -s
    smooth = s

    @addargs
    def subsamp2(self):
        """downsamples image by a factor of 2 (keeping new voxels centred on
        old)"""
        return ["-subsamp2"]

    @addargs
    def subsamp2offc(self):
        """downsamples image by a factor of 2 (non-centred)"""
        return ["-subsamp2offc"]

    # Dimensionality reduction operations

    @addargs
    def Tmean(self):
        """Mean across time."""
        return ["-Tmean"]

    @addargs
    def Tstd(self):
        """Standard deviation across time."""
        return ["-Tstd"]

    @addargs
    def Tmin(self):
        """Min across time."""
        return ["-Tmin"]

    @addargs
    def Tmax(self):
        """Max across time."""
        return ["-Tmax"]

    @addargs
    def Tmaxn(self):
        """time index of max across time."""
        return ["-Tmaxn"]

    @addargs
    def Tmedian(self):
        """median across time."""
        return ["-Tmedian"]

    @addargs
    def Tperc(self, percentage):
        """nth percentile (0-100) of FULL RANGE across time"""
        return ["-Tperc", percentage]

    @addargs
    def Tar1(self):
        """temporal AR(1) coefficient (use -odt float and probably demean
        first)"""
        return ["-Tar1"]

    # Basic statistical operations

    @addargs
    def pval(self):
        """Nonparametric uncorrected P-value"""
        return ['-pval']

    @addargs
    def pval0(self):
        """Same as -pval, but treat zeros as missing data"""
        return ['-pval0']

    @addargs
    def cpval(self):
        """Same as -pval, but gives FWE corrected P-values"""
        return ['-cpval']

    @addargs
    def ztop(self):
        """Convert Z-stat to (uncorrected) P"""
        return ['-ztop']

    @addargs
    def ptoz(self):
        """Convert (uncorrected) P to Z"""
        return ['-ptoz']

    @addargs
    def rank(self):
        """Convert (uncorrected) P to Z"""
        return ['-rank']

    @addargs
    def ranknorm(self):
        """Transform to Normal dist via ranks"""
        return ['-ranknorm']

    # Multi-argument operations

    @addargs
    def roi(self, xmin, xsize, ymin, ysize, zmin, zsize, tmin=0, tsize=-1):
        """Zero outside ROI (using voxel coordinates). """
        return ['-roi', xmin, xsize, ymin, ysize,
                zmin, zsize, tmin, tsize]

    @addargs
    def bptf(self, hp_sigma, lp_sigma):
        """Bandpass temporal filtering; nonlinear highpass and Gaussian linear
        lowpass (with sigmas in volumes, not seconds); set either sigma<0 to
        skip that filter."""
        return ["-bptf", hp_sigma, lp_sigma]

    def run(self, output=None, odt=None, **kwargs):
        """Save output of operations to image. Set ``output`` to a filename to have
        the result saved to file, or omit ``output`` entirely to have the
        result returned as a ``nibabel`` image.

        All other arguments are ultimately passed through to the
        :func:`fsl.utils.run.run` function.
        """

        cmd = ['fslmaths', self.__input] + self.__args

        if output is None:
            output = wutils.LOAD

        cmd += [output]

        if odt is not None:
            cmd.extend(('-odt', odt))

        result = self.__run(*cmd, **kwargs)

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
