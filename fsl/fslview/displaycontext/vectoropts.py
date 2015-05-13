#!/usr/bin/env python
#
# vectoropts.py - Defines the VectorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VectorOpts` class, which contains display
options for rendering :class:`.GLVector` instances.
"""

import props

import fsl.data.image   as fslimage
import fsl.data.strings as strings
import display          as fsldisplay


class VectorOpts(fsldisplay.DisplayOpts):


    xColour = props.Colour(default=(1.0, 0.0, 0.0))
    """Colour used to represent the X vector magnitude."""

    
    yColour = props.Colour(default=(0.0, 1.0, 0.0))
    """Colour used to represent the Y vector magnitude."""

    
    zColour = props.Colour(default=(0.0, 0.0, 1.0))
    """Colour used to represent the Z vector magnitude."""


    suppressX = props.Boolean(default=False)
    """Do not use the X vector magnitude to colour vectors."""

    
    suppressY = props.Boolean(default=False)
    """Do not use the Y vector magnitude to colour vectors."""

    
    suppressZ = props.Boolean(default=False)
    """Do not use the Z vector magnitude to colour vectors."""


    modulate  = props.Choice()
    """Modulate the vector colours by another image."""

    
    # TODO This is currently a percentage
    # of the modulation image data range.
    # It should be an absolute value
    modThreshold = props.Percentage(default=0.0)
    """Hide voxels for which the modulation value is below this threshold."""

    
    def __init__(self,
                 overlay,
                 display,
                 overlayList,
                 displayCtx,
                 parent=None,
                 *args,
                 **kwargs):
        """Create a ``VectorOpts`` instance for the given image.

        See the :class:`.DisplayOpts` documentation for more details.
        """

        if not isinstance(overlay, fslimage.Image):
            raise RuntimeError('{} can only be used with an {} overlay'.format(
                type(self).__name__, fslimage.Image.__name__)) 
        
        fsldisplay.DisplayOpts.__init__(self,
                                        overlay,
                                        display,
                                        overlayList,
                                        displayCtx,
                                        parent,
                                        *args,
                                        **kwargs)

        overlayList.addListener('overlays',
                                self.name,
                                self.__overlayListChanged)
        self.__overlayListChanged()


    def __overlayListChanged(self, *a):
        """Called when the overlay list changes. Updates the ``modulate``
        property so that it contains a list of overlays which could be used
        to modulate the vector image.
        """
        
        modProp  = self.getProp('modulate')
        modVal   = self.modulate
        overlays = self.displayCtx.getOrderedOverlays()

        # the image for this VectorOpts
        # instance has been removed
        if self.overlay not in overlays:
            self.overlayList.removeListener('overlays', self.name)
            return

        modOptions = ['none']
        modLabels  = [strings.choices['VectorOpts.modulate.none']]

        for overlay in overlays:
            
            # It doesn't make sense to
            # modulate the image by itself
            if overlay is self.overlay:
                continue

            # The modulate image must
            # be an image. Duh.
            if not isinstance(overlay, fslimage.Image):
                continue

            # an image can only be used to modulate
            # the vector image if it shares the same
            # dimensions as said vector image
            if overlay.shape != self.overlay.shape[:3]:
                continue

            modOptions.append(overlay)
            modLabels .append(overlay.name)
                
            overlay.addListener('name',
                                self.name,
                                self.__overlayListChanged,
                                overwrite=True)
            
        modProp.setChoices(modOptions, modLabels, self)

        if modVal in overlays: self.modulate = modVal
        else:                  self.modulate = 'none'


# TODO RGBVector/LineVector subclasses for any type
# specific options (e.g. line width for linevector)

class LineVectorOpts(VectorOpts):

    lineWidth = props.Int(minval=1, maxval=10, default=1)

    directed  = props.Boolean(default=False)
    """

    The directed property cannot be unbound across multiple LineVectorOpts
    instances, as it affects the OpenGL representation
    """

    def __init__(self, *args, **kwargs):

        kwargs['nounbind'] = ['directed']

        VectorOpts.__init__(self, *args, **kwargs)
