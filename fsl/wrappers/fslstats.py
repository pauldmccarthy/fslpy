#!/usr/bin/env python
#
# fslstats.py - Wrapper for fslstats
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`fslstats` class, which acts as a wrapper
for the ``fslstats`` command-line tool.


.. warning:: This wrapper function will only work with FSL 6.0.2 or newer.
"""


import six
import functools as ft

import fsl.data.image      as fslimage
from . import wrapperutils as wutils


OPTIONS = {
    'robust_minmax'   : 'r',
    'minmax'          : 'R',
    'mean_entropy'    : 'e',
    'mean_entropy_nz' : 'E',
    'volume'          : 'v',
    'volume_nz'       : 'V',
    'mean'            : 'm',
    'mean_nz'         : 'M',
    'stddev'          : 's',
    'stddev_nz'       : 'S',
    'smallest_roi'    : 'w',
    'max_vox'         : 'x',
    'min_vox'         : 'X',
    'cog_mm'          : 'c',
    'cog_vox'         : 'C',
    'abs'             : 'a',
    'zero_naninf'     : 'n',
}
"""This dict contains options which do not require any additional arguments.
They are set via attribute access on the ``fslstats`` object.
"""


ARG_OPTIONS = {
    'lower_threshold' : 'l',
    'upper_threshold' : 'u',
    'percentile'      : 'p',
    'percentile_nz'   : 'P',
    'mask'            : 'k',
    'diff'            : 'd',
    'hist'            : 'h',
    'hist_bounded'    : 'H',
}
"""This dict contains options which require additional arguments.
They are set via method calls on the ``fslstats`` object (with the
additional arguments passed into the method call).
"""


# add {shortopt : shortopt} mappings
# for all options to simplify code in
# the  fslstats class
OPTIONS    .update({v : v for v in OPTIONS    .values()})
ARG_OPTIONS.update({v : v for v in ARG_OPTIONS.values()})


class fslstats(object):
    """The ``fslstats`` class is a wrapper around the ``fslstats`` command-line
    tool. It provides an object-oriented interface - options are specified by
    chaining method calls and attribute accesses together.


    .. warning:: This wrapper function will only work with FSL 6.0.2 or newer,
                 due to bugs in ``fslstats`` output formatting that are
                 present in older versions.


    Any ``fslstats`` command-line option which does not require any arguments
    (e.g. ``-r``) can be set by accessing an attribute on a ``fslstats``
    object, e.g.::

        stats = fslstats('image.nii.gz')
        stats.r


    ``fslstats`` command-line options which do require additional arguments
    (e.g. ``-k``) can be set by calling a method on an ``fslstats`` object,
    e.g.::

        stats = fslstats('image.nii.gz')
        stats.k('mask.nii.gz')


    The ``fslstats`` command can be executed via the :meth:`run` method.
    Normally, the results will be returned as a list of floating point
    numbers. Pre-options will affect the structure of the return value - see
    :meth:`__init__` for details.


    Attribute and method calls can be chained together, so a complete
    ``fslstats`` call can be performed in a single line, e.g.::

        imgmin, imgmax = fslstats('image.nii.gz').k('mask.nii.gz').r.run()
    """


    def __init__(self,
                 input,
                 t=False,
                 K=None,
                 sep_volumes=False,
                 index_mask=None):
        """Create a ``fslstats`` object.

        If one of the ``t`` or ``K`` pre-options is set, e.g.::

            fslstats('image_4d.nii.gz', t=True)

        or::

            fslstats('image_4d.nii.gz', K='mask.nii.gz')

        then the value returned by :meth:`run` will contain a list-of-lists,
        with each child list containing the results:

         - for each 3D volume contained within the input image (if ``t``
           is set), or
         - for each sub-mask contained within the mask image (if ``K``
           is set)


        If both of the ``t`` and ``K`` pre-options are set, e.g.::

            fslstats('image_4d.nii.gz', t=True, K='mask.nii.gz')

        then the result will be a list-of-lists-of-lists, where each child
        list corresponds to each 3D volume (``t``), and each grand-child list
        corresponds to each sub-mask (``K``).


        :arg input:       Input image - either a file name, or an
                          :class:`.Image` object, or a ``nibabel.Nifti1Image``
                          object.
        :arg t:           Produce separate results for each 3D volume in the
                          input image.
        :arg K:           Produce separate results for each sub-mask within
                          the provided mask image.
        :arg sep_volumes: Alias for ``t``.
        :arg index_mask:  Alias for ``K``.
        """

        if t is None: t = sep_volumes
        if K is None: K = index_mask

        self.__input   = input
        self.__options = []

        # pre-options must be supplied
        # before input image
        if t:             self.__options.append( '-t')
        if K is not None: self.__options.extend(('-K', K))

        self.__options.append(input)


    def __getattr__(self, name):
        """Intercepts attribute accesses,...
        """

        # options which take no args
        # are called as attributes
        if name in OPTIONS:
            flag = OPTIONS[name]
            args = False

        # options which take args
        # are called as methods
        elif name in ARG_OPTIONS:
            flag = ARG_OPTIONS[name]
            args = True
        else:
            raise AttributeError()

        addFlag = ft.partial(self.__addFlag, flag)

        if args: return addFlag
        else:    return addFlag()


    def __addFlag(self, flag, *args):
        """Used by :meth:`__getattr__`. Add the given flag and any arguments to
        the accumulated list of command-line options.
        """
        self.__options.extend(('-' + flag,) + args)
        return self


    def run(self):
        """Run the ``fslstats`` command-line tool. The results are returned as
        floating point numbers.
        """

        result = self.__run('fslstats', *self.__options, log=None)
        result = result.stdout[0].strip()
        result = [line.split() for line in result.split('\n')]

        sepvols = '-t' in self.__options
        lblmask = '-K' in self.__options

        # This parsing logic will not work with
        # versions of fslstats prior to fsl 6.0.2,
        # due to a quirk in the output formatting
        # of older versions.

        # One line of output for each volume and
        # for each label (with volume the slowest
        # changing).
        if sepvols and lblmask:

            # One line of output for
            # each volume and label
            result = [[float(v) for v in line] for line in result]

            # We need know the number of volumes
            # (or the number of labels) in order
            # to know how to nest the results.
            img = fslimage.Image(self.__input, loadData=False)

            if img.ndim >= 4: nvols = img.shape[3]
            else:             nvols = 1

            # split the result up into
            # nlbls lines for each volume
            nlbls   = len(result) / nvols
            offsets = range(0, nvols * nlbls, nlbls)
            result  = [result[off:off + nlbls] for off in offsets]

        # One line of output
        # for each volume/label
        elif sepvols or lblmask:
            result = [[float(v) for v in line] for line in result]

        # One line of output
        else:
            result = [float(v) for v in result[0]]

        return result


    @wutils.fileOrImage()
    @wutils.fslwrapper
    def __run(self, *cmd):
        """Run the given ``fslmaths`` command. """
        return [str(c) for c in cmd]
