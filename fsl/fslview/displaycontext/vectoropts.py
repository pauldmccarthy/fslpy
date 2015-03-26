#!/usr/bin/env python
#
# vectoropts.py - Defines the VectorOpts class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`VectorOpts` class, which contains
display options for rendering :class:`~fsl.fslview.gl.glvector.GLVector`
instances.
"""

import props

import fsl.data.strings as strings
import display          as fsldisplay

class VectorOpts(fsldisplay.DisplayOpts):

    displayMode = props.Choice(
        ('line', 'rgb'),
        default='rgb',
        labels=[strings.choices['VectorOpts.displayType.line'],
                strings.choices['VectorOpts.displayType.rgb']])
    """Mode in which the ``GLVector`` instance is to be displayed."""


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

    
    def __init__(self, image, display, imageList, displayCtx, parent=None):
        """Create a ``VectorOpts`` instance for the given image.

        See the :class:`~fsl.fslview.displaycontext.display.DisplayOpts`
        documentation for more details.
        """
        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)

        imageList.addListener('images', self.name, self.imageListChanged)
        self.imageListChanged()


    def imageListChanged(self, *a):
        """Called when the image list changes. Updates the ``modulate``
        property so that it contains a list of images which could be used
        to modulate the vector image.
        """
        
        modProp = self.getProp('modulate')
        modVal  = self.modulate
        images  = self.displayCtx.getOrderedImages()

        # the image for this VectorOpts
        # instance has been removed
        if self.image not in images:
            self.imageList.removeListener('images', self.name)
            return

        modOptions = ['none']
        modLabels  = [strings.choices['VectorOpts.modulate.none']]

        for image in images:
            
            # It doesn't make sense to
            # modulate the image by itself
            if image is self.image:
                continue

            # an image can only be used to modulate
            # the vector image if it shares the same
            # dimensions as said vector image
            if image.shape != self.image.shape[:3]:
                continue

            modOptions.append(image)
            modLabels .append(image.name)
                
            image.addListener('name',
                              self.name,
                              self.imageListChanged,
                              overwrite=True)
            
        modProp.setChoices(modOptions, modLabels, self)

        if modVal in images: self.modulate = modVal
        else:                self.modulate = 'none'
