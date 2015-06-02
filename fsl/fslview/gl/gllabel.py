#!/usr/bin/env python
#
# gllabel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL           as gl

import fsl.utils.transform as transform
import fsl.fslview.gl      as fslgl
import resources           as glresources
import routines            as glroutines
import                        globject
import                        textures


class GLLabel(globject.GLImageObject):

    
    def __init__(self, image, display):

        globject.GLImageObject.__init__(self, image, display)

        imageTexName = '{}_{}' .format(type(self).__name__, id(image))
        lutTexName   = '{}_lut'.format(self.name)

        self.lutTexture   = textures.LookupTableTexture(lutTexName)
        self.imageTexture = glresources.get(
            imageTexName,
            textures.ImageTexture,
            imageTexName,
            image,
            display)

        self.vertexAttrBuffer = gl.glGenBuffers(1)

        fslgl.gllabel_funcs.compileShaders(self)
        
        self.refreshLutTexture()

        self.addListeners()


    def addListeners(self):

        display = self.display
        opts    = self.displayOpts

        def shaderUpdate(*a):
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()

        def lutUpdate(*a):
            self.refreshLutTexture()
            self.onUpdate()

        opts   .addListener('outline',       self.name, shaderUpdate)
        opts   .addListener('outlineWidth',  self.name, shaderUpdate)
        opts   .addListener('lut',           self.name, lutUpdate)
        display.addListener('alpha',         self.name, lutUpdate)
        display.addListener('brightness',    self.name, lutUpdate)
        display.addListener('contrast',      self.name, lutUpdate)
        


    def removeListeners(self):
        display = self.display
        opts    = self.displayOpts

        opts   .removeListener('outline',       self.name)
        opts   .removeListener('outlineWidth',  self.name)
        opts   .removeListener('lut',           self.name)
        display.removeListener('alpha',         self.name)
        display.removeListener('brightness',    self.name)
        display.removeListener('contrast',      self.name)

    
    def destroy(self):

        glresources.delete(self.imageTexture.getTextureName())
        self.lutTexture.destroy()

        self.removeListeners()
        fslgl.gllabel_funcs.destroy(self)

        
    def setAxes(self, xax, yax):
        """This method should be called when the image display axes change."""
        
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        fslgl.gllabel_funcs.updateShaderState(self)

        
    def generateVertices(self, zpos, xform):
        vertices, voxCoords, texCoords = glroutines.slice2D(
            self.image.shape[:3],
            self.xax,
            self.yax,
            zpos, 
            self.displayOpts.getTransform('voxel',   'display'),
            self.displayOpts.getTransform('display', 'voxel'))

        if xform is not None: 
            vertices = transform.transform(vertices, xform)

        return vertices, voxCoords, texCoords 


    def refreshLutTexture(self, *a):

        display = self.display
        opts    = self.displayOpts

        self.lutTexture.set(alpha=display.alpha / 100.0,
                            lut=opts.lut)

        
    def preDraw(self):

        self.imageTexture.bindTexture(gl.GL_TEXTURE0)
        self.lutTexture  .bindTexture(gl.GL_TEXTURE1)
        fslgl.gllabel_funcs.preDraw(self)

    
    def draw(self, zpos, xform=None):
        fslgl.gllabel_funcs.draw(self, zpos, xform)


    def postDraw(self):
        self.imageTexture.unbindTexture()
        self.lutTexture  .unbindTexture()
        fslgl.gllabel_funcs.postDraw(self)
