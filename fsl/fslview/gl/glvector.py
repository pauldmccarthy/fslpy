#!/usr/bin/env python
#
# glvector.py - OpenGL vertex creation and rendering code for drawing a
# X*Y*Z*3 image as a vector.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Defines the :class:`GLVector` class, which encapsulates the logic for
rendering 2D slices of a ``X*Y*Z*3`` :class:`.Image` as a vector. The
``GLVector`` class provides the interface defined by the :class:`.GLObject`
class.


The ``GLVector`` class is a base class whcih is not intended to be
instantiated directly. The :class:`.GLRGBVector` and :class:`.GLLineVector`
subclasses should be used instead.  These two subclasses share the
functionality provided by this class.


The vector image is stored on the GPU as a 3D RGB texture, where the ``R``
channel contains the ``x`` vector values, the ``G`` channel the ``y`` values,
and the ``B`` channel the ``z`` values. 


Three 1D textures are used to store a colour table for each of the ``x``,
``y`` and ``z`` components. A custom fragment shader program looks up the
``xyz`` vector values, looks up colours for each of them, and combines the
three colours to form the final fragment colour.


The colour of each vector may be modulated by another image, specified by the
:attr:`.VectorOpts.modulate` property.  This modulation image is stored as a
3D single-channel texture.
"""

import numpy                    as np
import OpenGL.GL                as gl

import fsl.data.image           as fslimage
import fsl.fslview.colourmaps   as fslcm
import resources                as glresources
import                             textures
import                             globject



class GLVector(globject.GLImageObject):
    """The :class:`GLVector` class encapsulates the data and logic required
    to render 2D slices of a ``X*Y*Z*3`` image as vectors.
    """

    def __init__(self, image, display, prefilter=None):
        """Create a :class:`GLVector` object bound to the given image and
        display.

        Initialises the OpenGL data required to render the given image.
        This method does the following:
        
          - Creates the image texture, the modulate texture, and the three
            colour map textures.

          - Adds listeners to the :class:`.Display` and :class:`.VectorOpts`
            instances, so the textures and geometry can be updated when
            necessary.

        :arg image:     An :class:`.Image` object.
        
        :arg display:   A :class:`.Display` object which describes how the
                        image is to be displayed.

        :arg prefilter: An optional function which filters the data before it
                        is stored as a 3D texture. See :class:`.ImageTexture`.
                        Whether or not this function is provided, the data is
                        transposed so that the fourth dimension is the fastest
                        changing.
        """

        if not image.is4DImage() or image.shape[3] != 3:
            raise ValueError('Image must be 4 dimensional, with 3 volumes '
                             'representing the XYZ vector angles')

        globject.GLImageObject.__init__(self, image, display)

        display = self.display
        opts    = self.displayOpts
        name    = self.name

        self.xColourTexture = textures.ColourMapTexture('{}_x'.format(name))
        self.yColourTexture = textures.ColourMapTexture('{}_y'.format(name))
        self.zColourTexture = textures.ColourMapTexture('{}_z'.format(name))
        self.modTexture     = None
        self.imageTexture   = None
        
        def modUpdate( *a):
            self.refreshModulateTexture()
            self.updateShaderState()
            self.onUpdate()

        def cmapUpdate(*a):
            self.refreshColourTextures()
            self.updateShaderState()
            self.onUpdate()
            
        def shaderUpdate(*a):
            self.updateShaderState()
            self.onUpdate() 

        def shaderCompile(*a):
            self.compileShaders()
            self.updateShaderState()
            self.onUpdate()

        display.addListener('softwareMode',  name, shaderCompile)
        display.addListener('alpha',         name, cmapUpdate)
        display.addListener('brightness',    name, cmapUpdate)
        display.addListener('contrast',      name, cmapUpdate) 
        opts   .addListener('xColour',       name, cmapUpdate)
        opts   .addListener('yColour',       name, cmapUpdate)
        opts   .addListener('zColour',       name, cmapUpdate)
        opts   .addListener('suppressX',     name, cmapUpdate)
        opts   .addListener('suppressY',     name, cmapUpdate)
        opts   .addListener('suppressZ',     name, cmapUpdate)
        opts   .addListener('modulate',      name, modUpdate)
        opts   .addListener('modThreshold',  name, shaderUpdate)

        # the fourth dimension (the vector directions) 
        # must be the fastest changing in the texture data
        if prefilter is None:
            realPrefilter = lambda d:           d.transpose((3, 0, 1, 2))
        else:
            realPrefilter = lambda d: prefilter(d.transpose((3, 0, 1, 2)))

        texName = '{}_{}'.format(type(self).__name__, id(self.image))
        self.imageTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            self.image,
            display=self.display,
            nvals=3,
            normalise=True,
            prefilter=realPrefilter) 

        self.refreshModulateTexture()
        self.refreshColourTextures()

        
    def destroy(self):
        """Deletes the GL textures, and deregisters the listeners configured in
        :meth:`__init__`.

        This method must be called by subclass implementations.
        """

        self.xColourTexture.destroy()
        self.yColourTexture.destroy()
        self.zColourTexture.destroy()

        glresources.delete(self.imageTexture.getTextureName())
        glresources.delete(self.modTexture  .getTextureName())

        self.imageTexture = None
        self.modTexture   = None

        self.display    .removeListener('softwareMode',  self.name)
        self.display    .removeListener('alpha',         self.name)
        self.display    .removeListener('brightness',    self.name)
        self.display    .removeListener('contrast',      self.name)
        self.displayOpts.removeListener('xColour',       self.name)
        self.displayOpts.removeListener('yColour',       self.name)
        self.displayOpts.removeListener('zColour',       self.name)
        self.displayOpts.removeListener('suppressX',     self.name)
        self.displayOpts.removeListener('suppressY',     self.name)
        self.displayOpts.removeListener('suppressZ',     self.name)
        self.displayOpts.removeListener('modulate',      self.name)
        self.displayOpts.removeListener('modThreshold',  self.name)


    def updateShaderState(self):
        """This method must be provided by subclasses."""
        raise NotImplementedError('updateShaderState must be implemented by '
                                  '{} subclasses'.format(type(self).__name__))

    
    def compileShaders(self):
        """This method must be provided by subclasses."""
        raise NotImplementedError('compileShaders must be implemented by '
                                  '{} subclasses'.format(type(self).__name__)) 


    def refreshModulateTexture(self):
        """Called when the :attr`.VectorOpts.modulate` property changes.

        Reconfigures the modulation texture. If no modulation image is
        selected, a 'dummy' texture is creatad, which contains all white
        values (and which result in the modulation texture having no effect).
        """

        if self.modTexture is not None:
            glresources.delete(self.modTexture.getTextureName())
            self.modTexture = None

        modImage = self.displayOpts.modulate

        if modImage == 'none':
            textureData = np.zeros((5, 5, 5), dtype=np.uint8)
            textureData[:] = 255
            modImage   = fslimage.Image(textureData)
            modDisplay = None
            norm       = False
            
        else:
            modDisplay = self.display
            norm       = True

        texName = '{}_{}_{}_modulate'.format(
            type(self).__name__, id(self.image), id(modImage))
        self.modTexture = glresources.get(
            texName,
            textures.ImageTexture,
            texName,
            modImage,
            display=modDisplay,
            normalise=norm)


    def refreshColourTextures(self, colourRes=256):
        """Called when the component colour maps need to be updated, when one
        of the :attr:`.VectorOpts.xColour`, ``yColour``, ``zColour``,
        ``suppressX``, ``suppressY``, or ``suppressZ`` properties change.

        Regenerates the colour textures.
        """

        display = self.display
        opts    = self.displayOpts

        xcol = opts.xColour
        ycol = opts.yColour
        zcol = opts.zColour

        xcol[3] = 1.0
        ycol[3] = 1.0
        zcol[3] = 1.0

        xsup = opts.suppressX
        ysup = opts.suppressY
        zsup = opts.suppressZ 

        xtex = self.xColourTexture
        ytex = self.yColourTexture
        ztex = self.zColourTexture

        drange = fslcm.briconToDisplayRange(
            (0.0, 1.0),
            display.brightness / 100.0,
            display.contrast   / 100.0)
        
        for colour, texture, suppress in zip(
                (xcol, ycol, zcol),
                (xtex, ytex, ztex),
                (xsup, ysup, zsup)):

            if not suppress:
                
                cmap = np.array(
                    [np.linspace(0.0, i, colourRes) for i in colour]).T
                
                # Component magnitudes of 0 are
                # transparent, but any other
                # magnitude is fully opaque
                cmap[:, 3] = display.alpha / 100.0
                cmap[0, 3] = 0.0 
            else:
                cmap = np.zeros((colourRes, 4))

            texture.set(cmap=cmap, displayRange=drange)
        

    def setAxes(self, xax, yax):
        """Stores the new x/y/z axes."""

        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        
    def preDraw(self):
        """Must be called by subclass implementations.

        Ensures that the five textures (the vector and modulation images,
        and the three colour textures) are bound to texture units 0-4
        respectively.
        """
        
        self.imageTexture  .bindTexture(gl.GL_TEXTURE0)
        self.modTexture    .bindTexture(gl.GL_TEXTURE1)
        self.xColourTexture.bindTexture(gl.GL_TEXTURE2)
        self.yColourTexture.bindTexture(gl.GL_TEXTURE3)
        self.zColourTexture.bindTexture(gl.GL_TEXTURE4)

        
    def postDraw(self):
        """Must be called by subclass implementations.

        Unbindes the five GL textures.
        """

        self.imageTexture  .unbindTexture()
        self.modTexture    .unbindTexture()
        self.xColourTexture.unbindTexture()
        self.yColourTexture.unbindTexture()
        self.zColourTexture.unbindTexture()
