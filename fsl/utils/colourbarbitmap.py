#!/usr/bin/env python
#
# colourbarbitmap.py - A function which renders a colour bar using
# matplotlib as an RGBA bitmap.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single function, :func:`plotColourBar`, which uses
:mod:`matplotlib` to plot a colour bar. The colour bar is rendered off-screen
and returned as an rgba bitmap.
"""

import logging
log = logging.getLogger(__name__)


import numpy                           as np
import matplotlib.backends.backend_agg as mplagg
import matplotlib.figure               as mplfig
import matplotlib.cm                   as cm


def colourBarBitmap(cmap,
                    vmin,
                    vmax,
                    width,
                    height,
                    label=None,
                    orientation='vertical',
                    labelside='top',
                    alpha=1.0,
                    fontsize=10,
                    textColour='#ffffff'):
    """Plots a colour bar using matplotlib, and returns a RGBA bitmap
    of the specified width/height.
    """

    if orientation not in ['vertical', 'horizontal']:
        raise ValueError('orientation must be vertical or horizontal')

    if orientation == 'horizontal':
        if labelside not in ['top', 'bottom']:
            raise ValueError('labelside must be top or bottom')
    else:
        if labelside not in ['left', 'right']:
            raise ValueError('labelside must be left or right')

    # vertical plots are rendered horizontally,
    # and then simply rotated at the end
    if orientation == 'vertical':
        width, height = height, width
        if labelside == 'left': labelside = 'top'
        else:                   labelside = 'bottom'

    ncols         = 256
    dpi           = 96.0
    cmap          = cm.get_cmap(cmap)
    data          = np.linspace(0.0, 1.0, ncols)
    data          = np.repeat(data.reshape(ncols, 1), 2, axis=1)
    data          = data.transpose()
    data          = cmap(data)
    data[:, :, 3] = alpha

    fig    = mplfig.Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    canvas = mplagg.FigureCanvasAgg(fig)
    ax     = fig.add_subplot(111)

    # make figure background invisible
    fig.patch.set_alpha(0)

    # draw the colour bar
    ax.imshow(data,
              aspect='auto',
              origin='lower',
              interpolation='bilinear')

    ax.set_xlim((0, ncols))
        
    ax.set_yticks([])
    ax.set_xticks((0, ncols))
    ax.set_xticklabels(('{}'.format(vmin), '{}'.format(vmax)))
    ax.tick_params(colors=textColour, labelsize=fontsize)

    minlbl, maxlbl = ax.get_xticklabels()

    minlbl.set_horizontalalignment('left')
    maxlbl.set_horizontalalignment('right')

    if labelside == 'top':
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        va = 'top'
    else:
        ax.xaxis.tick_bottom()
        ax.xaxis.set_label_position('bottom') 
        va = 'bottom'
    
    if label is not None:
        ax.set_xlabel(label,
                      fontsize=fontsize,
                      color=textColour,
                      va=va)

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

    if orientation == 'vertical':
        bitmap = np.flipud(bitmap.transpose([1, 0, 2]))
    return bitmap
