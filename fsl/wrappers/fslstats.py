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


import              io
import functools as ft
import numpy     as np

import fsl.data.image      as fslimage
from . import wrapperutils as wutils


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
    Normally, the results will be returned as a scalar floating point number,
    or a ``numpy`` array. Pre-options will affect the structure of the return
    value - see :meth:`__init__` for details.


    Attribute and method calls can be chained together, so a complete
    ``fslstats`` call can be performed in a single line, e.g.::

        imgmin, imgmax = fslstats('image.nii.gz').k('mask.nii.gz').r.run()
    """

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
    """This dict contains options which do not require any additional
    arguments. They are set via attribute access on the ``fslstats``
    object.
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

        then :meth:`run` will return a 2D ``numpy`` array of shape ``(nvols,
        nvals)`` if ``t`` is set, or ``(nlabels, nvals)`` if ``K`` is set.

        If both of the ``t`` and ``K`` pre-options are set, e.g.::

            fslstats('image_4d.nii.gz', t=True, K='mask.nii.gz')

        then the result will be a 3D numpy array of shape ``(nvols, nlabels,
        nvals)``.

        If neither ``t`` or ``K`` are set, then the result will be a scalar,
        or a 1D ``numpy`` array.

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
        """Intercepts attribute accesses and accumulates ``fslstats`` command-line
        flags accordingly.
        """

        # options which take no args
        # are called as attributes
        if name in fslstats.OPTIONS:
            flag = fslstats.OPTIONS[name]
            args = False

        # options which take args
        # are called as methods
        elif name in fslstats.ARG_OPTIONS:
            flag = fslstats.ARG_OPTIONS[name]
            args = True
        else:
            raise AttributeError(name)

        addFlag = ft.partial(self.__addFlag, flag)

        if args: return addFlag
        else:    return addFlag()


    def __addFlag(self, flag, *args):
        """Used by :meth:`__getattr__`. Add the given flag and any arguments to
        the accumulated list of command-line options.
        """
        self.__options.extend(('-' + flag,) + args)
        return self


    def run(self, raw=False):
        """Run the ``fslstats`` command-line tool. See :meth:`__init__` for a
        description of the return value.

        :arg raw: Defaults to ``False``. If ``True``, the raw standard output
                  and error is returned, instead of a scalar/numpy array.

        :returns: Result of ``fslstats`` as a scalar or ``numpy`` array.
        """

        # The parsing logic below will not work
        # with versions of fslstats prior to fsl
        # 6.0.2, due to a quirk in the output
        # formatting of older versions.

        # The default behaviour of run/runfsl
        # is to tee the command output streams
        # to the calling process streams. We
        # can disable this via log=None.
        result = self.__run('fslstats', *self.__options, log=None)

        if raw:
            return result.stdout

        result  = np.genfromtxt(io.StringIO(result.stdout[0].strip()))
        sepvols = '-t' in self.__options
        lblmask = '-K' in self.__options

        # One line of output for each volume and
        # for each label (with volume the slowest
        # changing). Reshape to 3D.
        if sepvols and lblmask:

            # We need know the number of volumes
            # (or the number of labels) in order
            # to know how to shape the results.
            img = fslimage.Image(self.__input, loadData=False)

            if img.ndim >= 4: nvols = img.shape[3]
            else:             nvols = 1

            # reshape the result into
            # (nvals, nvols, nlbls)
            nlbls  = int(len(result) / nvols)
            result = result.reshape((nvols, nlbls, -1)).squeeze()

        # Scalar - use numpy indexing weirdness
        # to get our single value out.
        elif result.size == 1:
            result = result[()]

        return result


    @wutils.fileOrImage()
    @wutils.fslwrapper
    def __run(self, *cmd):
        """Run the given ``fslmaths`` command. """
        return [str(c) for c in cmd]
