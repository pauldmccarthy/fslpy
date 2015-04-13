#!/usr/bin/env python
#
# sceneopts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import copy

import props

import fsl.fslview.gl.colourbarcanvas as colourbarcanvas

import fsl.data.strings as strings

class SceneOpts(props.HasProperties):
    """The ``SceneOpts`` class defines settings which are applied to
    :class:`.CanvasPanel` views.
    """

    
    showCursor = props.Boolean(default=True)

    
    zoom = props.Percentage(minval=10, maxval=1000, default=100, clamped=True)

    
    showColourBar = props.Boolean(default=False)

    
    colourBarLocation  = props.Choice(
        ('top', 'bottom', 'left', 'right'),
        labels=[strings.choices['SceneOpts.colourBarLocation.top'],
                strings.choices['SceneOpts.colourBarLocation.bottom'],
                strings.choices['SceneOpts.colourBarLocation.left'],
                strings.choices['SceneOpts.colourBarLocation.right']])

    
    colourBarLabelSide = copy.copy(colourbarcanvas.ColourBarCanvas.labelSide)

    
    performance = props.Choice(
        (1, 2, 3, 4, 5),
        default=5,
        labels=[strings.choices['SceneOpts.performance.1'],
                strings.choices['SceneOpts.performance.2'],
                strings.choices['SceneOpts.performance.3'],
                strings.choices['SceneOpts.performance.4'],
                strings.choices['SceneOpts.performance.5']])
    """User controllable performacne setting.

    This property is linked to the :attr:`twoStageRender`,
    :attr:`resolutionLimit`, and :attr:`fastMode` properties. Setting the
    performance to a low value will result in faster rendering time, at the
    cost of reduced features, and poorer rendering quality.

    See the :meth:`_onPerformanceChange` method.
    """
                
    
    twoStageRender = props.Boolean(default=False)
    """Enable two-stage rendering, useful for low-performance graphics cards/
    software rendering.

    See :attr:`~fsl.fslview.gl.slicecanvas.SliceCanvas.twoStageRender`.
    """


    resolutionLimit = props.Real(default=0, minval=0, maxval=5, clamped=True)
    """The highest resolution at which any image should be displayed.

    See :attr:`~fsl.fslview.gl.slicecanvas.SliceCanvas.resolutionLimit` and
    :attr:`~fsl.fslview.displaycontext.display.Display.resolution`.
    """

    
    fastMode = props.Boolean(default=False)
    """If ``True``, all images should be displayed in a 'fast mode'.

    The definition of 'fast mode' is intentionally left unspecified, but will
    generally mean using a GL fragment shader which is optimised for speed,
    possibly at the cost of omitting some features.

    See :attr:`~fsl.fslview.gl.slicecanvas.SliceCanvas.fastMode` and
    :attr:`~fsl.fslview.displaycontext.display.Display.fastMode`.
    """


    def __init__(self):
        
        name = '{}_{}'.format(type(self).__name__, id(self))
        self.addListener('performance', name, self._onPerformanceChange)
        
        self._onPerformanceChange()


    def _onPerformanceChange(self, *a):
        """Called when the :attr:`performance` property changes.

        Changes the values of the :attr:`twoStageRender`, :attr:`fastMode` and
        :attr:`resolutionLimit` properties accoridng to the performance
        setting.
        """

        if   self.performance == 5:
            self.twoStageRender  = False
            self.fastMode        = False
            self.resolutionLimit = 0
            
        elif self.performance == 4:
            self.twoStageRender  = True
            self.fastMode        = False
            self.resolutionLimit = 0
            
        elif self.performance == 3:
            self.twoStageRender  = True
            self.fastMode        = True
            self.resolutionLimit = 0

        elif self.performance == 2:
            self.twoStageRender  = True
            self.fastMode        = True
            self.resolutionLimit = 1
            
        elif self.performance == 1:
            self.twoStageRender  = True
            self.fastMode        = True
            self.resolutionLimit = 1.5
