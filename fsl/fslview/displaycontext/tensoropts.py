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


    modulate  = props.Choice()

    
    def __init__(self, image, display, imageList, displayCtx, parent=None):
        fsldisplay.DisplayOpts.__init__(self,
                                        image,
                                        display,
                                        imageList,
                                        displayCtx,
                                        parent)

        print 'image:     ', type(image)
        print 'display:   ', type(display)
        print 'imageList: ', type(imageList)
        print 'displayCtx:', type(displayCtx)

        imageList.addListener('images', self.name, self.imageListChanged)
        self.imageListChanged()


    def imageListChanged(self, *a):

        modProp = self.getProp('modulate')
        modVal  = self.modulate

        images = self.imageList[:]

        # the image for this TensorOpts
        # instance has been removed
        if self.image not in images:
            self.removeListener('images', self.name)
            return

        # It doesn't make sense to
        # modulate the image by itself
        images.remove(self.image)

        # Update choices when any
        # image name changes too
        for image in images:
            image.addListener('name',
                              self.name,
                              self.imageListChanged,
                              overwrite=True)
        
        names  = [strings.choices['TensorOpts.modulate.none']] + \
                 [i.name for i in images]
        images = ['none'] + images

        print 'Updating choices (value: {}): {}'.format(modVal, names)

        modProp.setChoices(images, names, self)

        if modVal in images: self.modulate = modVal
        else:                self.modulate = 'none'
