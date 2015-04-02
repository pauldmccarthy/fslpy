#!/usr/bin/env python
#
# selectiontexture.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

import numpy     as np
import OpenGL.GL as gl

import fsl.fslview.gl.textures as textures


log = logging.getLogger(__name__)


class SelectionTexture(textures.Texture):

    def __init__(self, selection, name):

        self.name      = name
        self.selection = selection
        self.texture   = gl.glGenTextures(1)

        log.debug('Created GL texture for {}: {}'.format(self.name,
                                                         self.texture)) 

        selection.addListener('selection', name, self._selectionChanged)

        self._init()
        self.refresh()


    def _init(self):
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.texture)
        
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MAG_FILTER,
                           gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_MIN_FILTER,
                           gl.GL_NEAREST)

        gl.glTexParameterfv(gl.GL_TEXTURE_3D,
                            gl.GL_TEXTURE_BORDER_COLOR,
                            np.array([0, 0, 0, 0], dtype=np.float32))
        
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_S,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_T,
                           gl.GL_CLAMP_TO_BORDER)
        gl.glTexParameteri(gl.GL_TEXTURE_3D,
                           gl.GL_TEXTURE_WRAP_R,
                           gl.GL_CLAMP_TO_BORDER)

        shape = self.selection.selection.shape
        gl.glTexImage3D(gl.GL_TEXTURE_3D,
                        0,
                        gl.GL_ALPHA8,
                        shape[0],
                        shape[1],
                        shape[2],
                        0,
                        gl.GL_ALPHA,
                        gl.GL_UNSIGNED_BYTE,
                        None)
        
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)

        
    def refresh(self, block=None, offset=None):
        
        if block is None or offset is None:
            data   = self.selection.selection
            offset = [0, 0, 0]
        else:
            data = block

        data = data * 255

        log.debug('Updating selection texture (offset {}, size {})'.format(
            offset, data.shape))
        
        gl.glBindTexture(gl.GL_TEXTURE_3D, self.texture)
        gl.glTexSubImage3D(gl.GL_TEXTURE_3D,
                           0,
                           offset[0],
                           offset[1],
                           offset[2],
                           data.shape[0],
                           data.shape[1],
                           data.shape[2],
                           gl.GL_ALPHA,
                           gl.GL_UNSIGNED_BYTE,
                           data.ravel('F'))
        gl.glBindTexture(gl.GL_TEXTURE_3D, 0)
 
    
    def _selectionChanged(self, *a):
        
        old, new, offset = self.selection.getLastChange()

        if old is None or new is None:
            data   = self.selection.selection
            offset = [0, 0, 0]
        else:
            data = new

        self.refresh(data, offset)
