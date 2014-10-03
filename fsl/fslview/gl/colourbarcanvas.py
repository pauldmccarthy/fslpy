#!/usr/bin/env python
#
# colourbarcanvas.py - Render a colour bar using OpenGL and matplotlib.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ColourBarCanvas`.

The :class:`ColourBarCanvas` contains logic which uses :mod:`matplotlib` to
draw a colour bar (with labels), and then renders said colour bar using
OpenGL.
"""

import logging
log = logging.getLogger(__name__)

import OpenGL.GL         as gl
import numpy             as np


import matplotlib.backends.backend_agg as mplagg
import matplotlib.figure               as mplfig
import matplotlib.image                as mplimg

import props


def plotColourBar(cmap,
                  vmin,
                  vmax,
                  label,
                  orient,
                  width,
                  height,
                  alpha=1.0,
                  textColour='#ffffff'):
    """Plots a colour bar using matplotlib, and returns a RGBA bitmap
    of the specified width/height.
    """

    dpi = 96.0
    pad = (vmax - vmin) * 0.075

    data = np.array([[vmin - pad, vmax + pad]])

    fig    = mplfig.Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    canvas = mplagg.FigureCanvasAgg(fig)
    ax     = fig.add_subplot(111)

    ax.plot([1, 2, 3], [4, 5, 6])
    
#    ax.imshow(data, cmap=cmap, alpha=alpha)
    
#    cbax = fig.axes([0.005, 0.001, 0.45, 0.998])
    
#    cbar = plt.colorbar(orientation="vertical", cax=cbax)
#    cbar.set_ticks((vmin,vmax))
#    cbar.set_ticklabels(('%u' % vmin, '%u' % vmax))
#    cbar.set_label(label, fontsize=24, ha='center', va='bottom')
#    cbax.tick_params(labelsize=24)

    canvas.draw()

    buf = canvas.tostring_argb()
    ncols, nrows = canvas.get_width_height()

    bitmap = np.fromstring(buf, dtype=np.uint8)
    bitmap = bitmap.reshape(nrows, ncols, 4)

    rgb = bitmap[:, :, 1:]
    a   = bitmap[:, :, 0]
    bitmap = np.dstack((rgb, a))

    mplimg.imsave('bob.png', bitmap)
    

plotColourBar(0, 0, 1, 0, 0, 800, 800)
class ColourBarCanvas(props.HasProperties):


    def __init__(self):
        pass

    
    pass
