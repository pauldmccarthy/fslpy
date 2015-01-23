#!/usr/bin/env python
#
# tensoropts.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import props

import fsl.data.strings as strings
import display          as fsldisplay

class TensorOpts(fsldisplay.DisplayOpts):

    displayMode = props.Choice(
        ('line', 'rgb'),
        labels=[strings.choices['TensorOpts.displayType.line'],
                strings.choices['TensorOpts.displayType.rgb']])


    xColour = props.Colour(default=(1.0, 0.0, 0.0))

    
    yColour = props.Colour(default=(0.0, 1.0, 0.0))

    
    zColour = props.Colour(default=(0.0, 0.0, 1.0))


    suppressX = props.Boolean(default=False)

    
    suppressY = props.Boolean(default=False)

    
    suppressZ = props.Boolean(default=False)


    # make this nounbind?
    modulate  = props.Choice()

    
    def __init__(self, image, display, imageList, displayCtx, parent=None):
        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)

        imageList.addListener('images', self.name, self.imageListChanged)
        self.imageListChanged()


    def imageListChanged(self, *a):
        
        modProp = self.getProp('modulate')
        modVal  = self.modulate
        images  = self.displayCtx.getOrderedImages()

        # the image for this TensorOpts
        # instance has been removed
        if self.image not in images:
            self.removeListener('images', self.name)
            return

        modOptions = ['none']
        modLabels  = [strings.choices['TensorOpts.modulate.none']]

        for image in images:
            
            # It doesn't make sense to
            # modulate the image by itself
            if image is self.image:
                continue

            # an image can only be used to modulate
            # the tensor image if it shares the same
            # dimensions as said tensor image
            if image.shape  != self.image.shape[ :3] or \
               image.pixdim != self.image.pixdim[:3]:
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
