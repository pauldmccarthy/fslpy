#!/usr/bin/env python
#
# naninfrange.py - The naninfrange function.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :func:`naninfrange` function, which calculates
the range of a numpy array, ignoring infinite and nan values.
"""


import numpy as np


def naninfrange(data):
    """Returns the minimum and maximum values in the given ``numpy`` array,
    ignoring ``nan`` and ``inf`` values.

    The ``numpy.nanmin``/``numpy.nanmax`` functions do not handle
    positive/negative infinity, so if such values are in the data, we need to
    use an alternate approach to calculating the minimum/maximum.
    """

    if not np.issubdtype(data.dtype, np.floating):
        return data.min(), data.max()

    # But np.nanmin/nanmax are substantially
    # faster than the alternate, so we try it
    # first.
    dmin = np.nanmin(data)
    dmax = np.nanmax(data)

    # If there are no nans/infs in the data,
    # we can just use nanmin/nanmax
    if np.isfinite(dmin) and np.isfinite(dmax):
        return dmin, dmax

    # The entire array contains nans
    if np.isnan(dmin):
        return dmin, dmin

    # Otherwise we need to calculate min/max
    # only on finite values. This is the slow
    # option.

    # Find all finite values
    finite = np.isfinite(data)

    # Try to calculate min/max on those values.
    # An error will be raised if there are no
    # finite values in the array
    try:
        return data[finite].min(), data[finite].max()
    except Exception:
        return np.nan, np.nan
