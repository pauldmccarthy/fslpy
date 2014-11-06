#!/usr/bin/env python
#
# textbitmap.py - A function which renders some text using matplotlib, and
# returns it as an RGBA bitmap.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single function, :func:`textBitmap`, which renders
some text using :mod:`matplotlib`, and returns it as an RGBA bitmap.
"""

import logging
log = logging.getLogger(__name__)

import numpy                           as np
import matplotlib.backends.backend_agg as mplagg
import matplotlib.figure               as mplfig


def textBitmap(text,
               width,
               height,
               fontSize,
               fgColour,
               bgColour,
               alpha=1.0):

    dpi    = 96.0
    fig    = mplfig.Figure(figsize=(width / dpi, height / dpi),
                           dpi=dpi)
    canvas = mplagg.FigureCanvasAgg(fig)
    ax     = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')

    if bgColour is not None: fig.patch.set_facecolor(bgColour)
    else:                    fig.patch.set_alpha(0)

    ax.set_xticks([])
    ax.set_yticks([])

    ax.text(0.5,
            0.5,
            text,
            fontsize=fontSize,
            verticalalignment='center',
            horizontalalignment='center',
            transform=ax.transAxes,
            color=fgColour)


    try:    fig.tight_layout()
    except: pass

    canvas.draw()
    buf = canvas.tostring_argb()
    ncols, nrows = canvas.get_width_height()

    bitmap = np.fromstring(buf, dtype=np.uint8)
    bitmap = bitmap.reshape(nrows, ncols, 4)

    rgb = bitmap[:, :, 1:]
    a   = bitmap[:, :, 0]
    bitmap = np.dstack((rgb, a))

    return bitmap 
