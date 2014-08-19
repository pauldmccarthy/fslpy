#!/usr/bin/env python
#
# glcircle_funcs.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import OpenGL.GL as gl
import numpy     as np

def draw(glimg, zpos, xform=None):
    """Draws the specified slice from the specified image on the canvas.
    """

    image   = glimg.image
    display = glimg.display

    # Don't draw the slice if this
    # image display is disabled
    if not display.enabled: return

    # load the shaders
    gl.glUseProgram(glimg.shaders) 

    # bind the current alpha value
    # and data range to the shader
    gl.glUniform1f( glimg.signedPos,        glimg.signed)
    gl.glUniform1f( glimg.zCoordPos,        zpos)
    gl.glUniform3fv(glimg.imageShapePos, 1, np.array(image.shape,
                                                     dtype=np.float32))
    gl.glUniform1i( glimg.xaxPos,           glimg.xax)
    gl.glUniform1i( glimg.yaxPos,           glimg.yax)
    gl.glUniform1i( glimg.zaxPos,           glimg.zax)
    
    # bind the transformation matrices
    # to the shader variable
    if xform is None: xform = np.identity(4)
    
    w2w = np.array(xform,               dtype=np.float32).ravel('C')
    w2v = np.array(image.worldToVoxMat, dtype=np.float32).ravel('C')
    tcx = np.array(glimg.texCoordXform, dtype=np.float32).ravel('C')
    
    gl.glUniformMatrix4fv(glimg.worldToVoxMatPos,   1, False, w2v)
    gl.glUniformMatrix4fv(glimg.worldToWorldMatPos, 1, False, w2w)
    gl.glUniformMatrix4fv(glimg.texCoordXformPos,   1, False, tcx)

    # Set up the colour texture
    gl.glActiveTexture(gl.GL_TEXTURE0) 
    gl.glBindTexture(gl.GL_TEXTURE_1D, glimg.colourTexture)
    gl.glUniform1i(glimg.colourMapPos, 0) 

    # Set up the image data texture
    gl.glActiveTexture(gl.GL_TEXTURE1) 
    gl.glBindTexture(gl.GL_TEXTURE_3D, glimg.imageData)
    gl.glUniform1i(glimg.imageBufferPos, 1)

    # world x/y coordinates
    glimg.worldCoords.bind()
    gl.glVertexAttribPointer(
        glimg.worldCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(glimg.worldCoordPos)

    # world x/y texture coordinates
    glimg.texCoords.bind()
    gl.glVertexAttribPointer(
        glimg.texCoordPos,
        2,
        gl.GL_FLOAT,
        gl.GL_FALSE,
        0,
        None)
    gl.glEnableVertexAttribArray(glimg.texCoordPos) 

    # Draw all of the triangles!
    gl.glDrawArrays(gl.GL_TRIANGLES, 0, glimg.nVertices)

    gl.glDisableVertexAttribArray(glimg.worldCoordPos)
    gl.glDisableVertexAttribArray(glimg.texCoordPos)
    glimg.worldCoords.unbind()
    glimg.texCoords.unbind()

    gl.glUseProgram(0)
