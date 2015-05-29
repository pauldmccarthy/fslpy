#!/usr/bin/env python
#
# glmodel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy     as np
import OpenGL.GL as gl

import                            globject
import fsl.utils.transform     as transform
import fsl.fslview.gl.routines as glroutines
import fsl.fslview.gl.textures as textures
import fsl.fslview.gl.shaders  as shaders
import fsl.fslview.colourmaps  as fslcmaps


class GLModel(globject.GLObject):

    def __init__(self, overlay, display):

        globject.GLObject.__init__(self)

        self.overlay = overlay
        self.display = display
        self.opts    = display.getDisplayOpts()

        self.opts.addListener('refImage',   self.name, self._updateVertices)
        self.opts.addListener('coordSpace', self.name, self._updateVertices)
        self.opts.addListener('transform',  self.name, self._updateVertices)

        self._updateVertices()

        self._renderTexture = textures.GLObjectRenderTexture(
            self.name, self, 0, 1)

        vertShaderSrc = shaders.getVertexShader(  self)
        fragShaderSrc = shaders.getFragmentShader(self)
        self.shaders  = shaders.compileShaders(vertShaderSrc, fragShaderSrc)

        self.texPos       = gl.glGetUniformLocation(self.shaders, 'tex')
        self.texWidthPos  = gl.glGetUniformLocation(self.shaders, 'texWidth')
        self.texHeightPos = gl.glGetUniformLocation(self.shaders, 'texHeight')

        gl.glUseProgram(self.shaders)
        gl.glUniform1i( self.texPos, 0)
        gl.glUniform1f( self.texWidthPos,  256.0)
        gl.glUniform1f( self.texHeightPos, 256.0)
        gl.glUseProgram(0)

        
    def destroy(self):
        self._renderTexture.destroy()
        gl.glDeleteProgram(self.shaders)


    def _updateVertices(self, *a):

        vertices = self.overlay.vertices
        indices  = self.overlay.indices

        xform = self.opts.getCoordSpaceTransform()

        if xform is not None:
            vertices = transform.transform(vertices, xform)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices  = np.array(indices,  dtype=np.uint32)
        self.onUpdate()

        
    def getDisplayBounds(self):
        return self.opts.getDisplayBounds()

    
    def getDataResolution(self, xax, yax):

        # TODO How can I have this resolution tied
        # to the rendering target resolution (i.e.
        # the screen), instead of being fixed?
        # 
        # Perhaps the DisplayContext class should 
        # have a method which returns the current
        # rendering resolution for a given display
        # space axis/length ..
        #
        # Also, isn't it a bit dodgy to be accessing
        # the DisplayContext instance through the
        # DisplayOpts instance? Why not just pass
        # the displayCtx instance to the GLObject
        # constructor, and have it directly accessible
        # by all GLobjects?

        zax = 3 - xax - yax

        xDisplayLen = self.opts.displayCtx.bounds.getLen(xax)
        yDisplayLen = self.opts.displayCtx.bounds.getLen(yax)
        zDisplayLen = self.opts.displayCtx.bounds.getLen(zax)

        lo, hi = self.getDisplayBounds()

        xModelLen = abs(hi[xax] - lo[xax])
        yModelLen = abs(hi[yax] - lo[yax])
        zModelLen = abs(hi[zax] - lo[zax])

        resolution      = [1, 1, 1]
        resolution[xax] = int(round(2048.0 * xModelLen / xDisplayLen))
        resolution[yax] = int(round(2048.0 * yModelLen / yDisplayLen))
        resolution[zax] = int(round(2048.0 * zModelLen / zDisplayLen))
        
        return resolution
        
    
    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        self._renderTexture.setAxes(xax, yax)
 

    def preDraw(self):
        pass

    
    def draw(self, zpos, xform=None):

        display = self.display 
        opts    = self.opts

        xax = self.xax
        yax = self.yax
        zax = self.zax

        vertices = self.vertices
        indices  = self.indices

        lo, hi = self.getDisplayBounds()

        xmin = lo[xax]
        ymin = lo[yax]
        xmax = hi[xax]
        ymax = hi[yax]

        clipPlaneVerts                = np.zeros((4, 3), dtype=np.float32)
        clipPlaneVerts[0, [xax, yax]] = [xmin, ymin]
        clipPlaneVerts[1, [xax, yax]] = [xmin, ymax]
        clipPlaneVerts[2, [xax, yax]] = [xmax, ymax]
        clipPlaneVerts[3, [xax, yax]] = [xmax, ymin]
        clipPlaneVerts[:,  zax]       =  zpos

        vertices = vertices.ravel('C')
        planeEq  = glroutines.planeEquation(clipPlaneVerts[0, :],
                                            clipPlaneVerts[1, :],
                                            clipPlaneVerts[2, :])

        self._renderTexture.bindAsRenderTarget()
        self._renderTexture.setRenderViewport(xax, yax, lo, hi)

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)
        gl.glClear(gl.GL_STENCIL_BUFFER_BIT)

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnable(gl.GL_CLIP_PLANE0)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_STENCIL_TEST)

        gl.glClipPlane(gl.GL_CLIP_PLANE0, planeEq)
        gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE)

        # First and second passes - render front and
        # back faces separately. In the stencil buffer,
        # subtract the mask created by the second
        # render from the mask created by the first -
        # this gives us a mask which shows the
        # intersection of the model with the clipping
        # plane.
        gl.glStencilFunc(gl.GL_ALWAYS, 0, 0)

        # I don't understand why, but if any of the
        # display system axes are inverted, we need
        # to render the back faces first, otherwise
        # the cross-section mask will not be created
        # correctly.
        direction = [gl.GL_INCR, gl.GL_DECR]
        if np.any(hi < lo): faceOrder = [gl.GL_FRONT, gl.GL_BACK]
        else:               faceOrder = [gl.GL_BACK,  gl.GL_FRONT]
        
        for face, direction in zip(faceOrder, direction):
            
            gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, direction)
            gl.glCullFace(face)

            gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
            gl.glDrawElements(gl.GL_TRIANGLES,
                              len(indices),
                              gl.GL_UNSIGNED_INT,
                              indices)

        # third pass - render the intersection of the 
        # front and back faces from the stencil buffer
        gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)

        gl.glDisable(gl.GL_CLIP_PLANE0)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY)

        gl.glStencilFunc(gl.GL_NOTEQUAL, 0, 255)

        colour = list(fslcmaps.applyBricon(
            opts.colour[:3],
            display.brightness / 100.0,
            display.contrast   / 100.0))
        
        colour.append(display.alpha / 100.0)

        gl.glColor(*colour)
        gl.glBegin(gl.GL_QUADS)

        gl.glVertex3f(*clipPlaneVerts[0, :])
        gl.glVertex3f(*clipPlaneVerts[1, :])
        gl.glVertex3f(*clipPlaneVerts[2, :])
        gl.glVertex3f(*clipPlaneVerts[3, :])
        gl.glEnd()

        gl.glDisable(gl.GL_STENCIL_TEST)

        self._renderTexture.unbindAsRenderTarget()
        self._renderTexture.restoreViewport()

        if opts.outline:
            gl.glUseProgram(self.shaders)

        self._renderTexture.drawOnBounds(
            zpos, xmin, xmax, ymin, ymax, xax, yax, xform)
        
        if opts.outline:
            gl.glUseProgram(0)

    
    def postDraw(self):
        pass
