#!/usr/bin/env python
#
# textbitmap.py - A function which renders some text using matplotlib, and
# returns it as an RGBA bitmap.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single function, :func:`textBitmap`, which renders
some text off-screen using :mod:`matplotlib`, and returns it as an RGBA bitmap.
"""


def textBitmap(text,
               width,
               height,
               fontSize,
               fgColour,
               bgColour,
               alpha=1.0):
    """Draw some text using :mod:`matplotlib`.


    The rendered text is returned as a RGBA bitmap within a ``numpy.uint8``
    array of size :math:`w \\times h \\times 4`, with the top-left pixel
    located at index ``[0, 0, :]``.

    :arg text:     Text to render.
    
    :arg width:    Width in pixels.
    
    :arg height:   Height in pixels.
    
    :arg fontSize: Font size in points.
    
    :arg fgColour: Foreground (text) colour - can be any colour specification
                   that is accepted by :mod:`matplotlib`.
    
    :arg bgColour: Background colour  - can be any colour specification that
                   is accepted by :mod:`matplotlib`..
    
    :arg alpha:    Text transparency, in the range ``[0.0 - 1.0]``.
    """

    # Imports are expensive
    import numpy                           as np
    import matplotlib.backends.backend_agg as mplagg
    import matplotlib.figure               as mplfig

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
            color=fgColour,
            alpha=alpha)

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
