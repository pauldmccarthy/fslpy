#!/usr/bin/env python
#
# gllabel.py - OpenGL representation for label/atlas images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import OpenGL.GL      as gl

import fsl.fslview.gl as fslgl
import resources      as glresources
import                   globject
import                   textures


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
        
        fslgl.gllabel_funcs.init(self)

        self.refreshLutTexture()
        self.addListeners()

        
    def destroy(self):

        glresources.delete(self.imageTexture.getTextureName())
        self.lutTexture.destroy()

        self.removeListeners()
        fslgl.gllabel_funcs.destroy(self)


    def addListeners(self):

        display = self.display
        opts    = self.displayOpts

        def shaderUpdate(*a):
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()
            
        def shaderCompile(*a):
            fslgl.gllabel_funcs.compileShaders(self)
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate() 

        def lutUpdate(*a):
            self.refreshLutTexture()
            fslgl.gllabel_funcs.updateShaderState(self)
            self.onUpdate()

        def lutChanged(*a):
            if self.__lut is not None:
                self.__lut.removeListener('labels', self.name)
                
            self.__lut = opts.lut

            if self.__lut is not None:
                self.__lut.addListener('labels', self.name, lutUpdate)
 
            lutUpdate()

        self.__lut = opts.lut

        # TODO If you add a software shader, you will
        #      need to call gllabel_funcs.compileShaders
        #      when display.softwareMode changes

        opts    .addListener('outline',       self.name, shaderUpdate)
        opts    .addListener('outlineWidth',  self.name, shaderUpdate)
        opts    .addListener('lut',           self.name, lutChanged)
        opts.lut.addListener('labels',        self.name, lutUpdate)
        display .addListener('alpha',         self.name, lutUpdate)
        display .addListener('brightness',    self.name, lutUpdate)
        display .addListener('contrast',      self.name, lutUpdate)
        display .addListener('softwareMode',  self.name, shaderCompile)


    def removeListeners(self):
        display = self.display
        opts    = self.displayOpts

        opts   .removeListener('outline',       self.name)
        opts   .removeListener('outlineWidth',  self.name)
        opts   .removeListener('lut',           self.name)
        display.removeListener('alpha',         self.name)
        display.removeListener('brightness',    self.name)
        display.removeListener('contrast',      self.name)
        display.removeListener('softwareMode',  self.name)

        
    def setAxes(self, xax, yax):
        globject.GLImageObject.setAxes(self, xax, yax)
        fslgl.gllabel_funcs.updateShaderState(self)


    def refreshLutTexture(self, *a):

        display = self.display
        opts    = self.displayOpts

        self.lutTexture.set(alpha=display.alpha           / 100.0,
                            brightness=display.brightness / 100.0,
                            contrast=display.contrast     / 100.0,
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
