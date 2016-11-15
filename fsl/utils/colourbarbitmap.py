#!/usr/bin/env python
#
# colourbarbitmap.py - A function which renders a colour bar using
# matplotlib as an RGBA bitmap.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single function, :func:`colourBarBitmap`, which uses
:mod:`matplotlib` to plot a colour bar. The colour bar is rendered off-screen
and returned as an RGBA bitmap.
"""


def colourBarBitmap(cmap,
                    width,
                    height,
                    cmapResolution=256,
                    negCmap=None,
                    invert=False,
                    ticks=None,
                    ticklabels=None,
                    tickalign=None,
                    label=None,
                    orientation='vertical',
                    labelside='top',
                    alpha=1.0,
                    fontsize=10,
                    bgColour=None,
                    textColour='#ffffff'):
    """Plots a colour bar using :mod:`matplotlib`.

    
    The rendered colour bar is returned as a RGBA bitmap within a
    ``numpy.uint8`` array of size :math:`w \\times h \\times 4`, with the
    top-left pixel located at index ``[0, 0, :]``.


    A rendered colour bar will look something like this:

    .. image:: images/colourbarbitmap.png
       :scale: 50%
       :align: center
    
    
    :arg cmap:         Name of a registered :mod:`matplotlib` colour map.

    :arg width:        Colour bar width in pixels.
    
    :arg height:       Colour bar height in pixels.

    :arg negCmap:      If provided, two colour maps are drawn, centered at 0.

    :arg invert:       If ``True``, the colour map is inverted.

    :arg ticks:        Locations of tick labels. 

    :arg ticklabels:   Tick labels.

    :arg tickalign:    Tick alignment (one for each tick, either ``'left'`` or
                       ``'right'``).

    :arg label:        Text label to show next to the colour bar.
    
    :arg orientation:  Either ``vertical`` or ``horizontal``.
    
    :arg labelside:    If ``orientation`` is ``vertical`` ``labelSide`` may
                       be either ``left`` or ``right``. Otherwise, if
                       ``orientation`` is ``horizontal``, ``labelSide`` may
                       be ``top`` or ``bottom``.
    
    :arg alpha:        Colour bar transparency, in the range ``[0.0 - 1.0]``.
    
    :arg fontsize:     Label font size in points.
    
    :arg bgColour:     Background colour - can be any colour specification
                       that is accepted by :mod:`matplotlib`.
    
    :arg textColour:   Label colour - can be any colour specification that
                       is accepted by :mod:`matplotlib`.
    """

    # These imports are expensive, so we're
    # importing at the function level.
    import numpy                           as np
    import matplotlib.backends.backend_agg as mplagg
    import matplotlib.figure               as mplfig

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

    dpi   = 96.0
    ncols = cmapResolution
    data  = genColours(cmap, ncols, invert, alpha)

    if negCmap is not None:
        ndata  = genColours(negCmap, ncols, not invert, alpha)
        data   = np.concatenate((ndata, data), axis=1)
        ncols *= 2

    fig    = mplfig.Figure(figsize=(width / dpi, height / dpi), dpi=dpi)
    canvas = mplagg.FigureCanvasAgg(fig)
    ax     = fig.add_subplot(111)
    
    if bgColour is not None:
        fig.patch.set_facecolor(bgColour)
    else:
        fig.patch.set_alpha(0)

    # draw the colour bar
    ax.imshow(data,
              aspect='auto',
              origin='lower',
              interpolation='nearest')

    ax.set_xlim((0, ncols - 1))

    ax.set_yticks([])
    ax.tick_params(colors=textColour, labelsize=fontsize, length=0)
    
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
        label = ax.xaxis.get_label()

    if ticks is None or ticklabels is None:
        ax.set_xticks([])
    else:
        
        ax.set_xticks(np.array(ticks) * ncols)
        ax.set_xticklabels(ticklabels)
        ticklabels = ax.xaxis.get_ticklabels()

    try:
        fig.tight_layout()
    except:
        pass

    # Adjust the x label after tight_layout,
    # otherwise it will overlap with the tick
    # labels. I don't understand why, but I
    # have to set va to the opposite of what
    # I would have thought.
    if label is not None and ticklabels is not None:
        if labelside == 'top':
            label.set_va('bottom')
            label.set_position((0.5, 0.97))
        else:
            label.set_va('top')
            label.set_position((0.5, 0.03))

    # This must be done *after* calling
    # tick_top/tick_bottom, as I think
    # the label bjects get recreated.
    if ticklabels is not None and tickalign is not None:
        for l, a in zip(ticklabels, tickalign):
            l.set_horizontalalignment(a)
    
    canvas.draw()

    buf = canvas.tostring_argb()
    ncols, nrows = canvas.get_width_height()

    bitmap = np.fromstring(buf, dtype=np.uint8)
    bitmap = bitmap.reshape(nrows, ncols, 4).transpose([1, 0, 2])

    # the bitmap is in argb order,
    # but we want it in rgba
    rgb = bitmap[:, :, 1:]
    a   = bitmap[:, :, 0]
    bitmap = np.dstack((rgb, a))

    if orientation == 'vertical':
        bitmap = np.flipud(bitmap.transpose([1, 0, 2]))
        bitmap = np.rot90(bitmap, 2)

    return bitmap


def genColours(cmap, cmapResolution, invert, alpha):
    """Generate an array containing ``cmapResolution`` colours from the given
    colour map object/function.
    """

    import numpy         as np
    import matplotlib.cm as cm
    
    ncols         = cmapResolution
    cmap          = cm.get_cmap(cmap)
    data          = np.linspace(0.0, 1.0, ncols)
    
    if invert:
        data = data[::-1]
    
    data          = np.repeat(data.reshape(ncols, 1), 2, axis=1)
    data          = data.transpose()
    data          = cmap(data)
    data[:, :, 3] = alpha

    return data
