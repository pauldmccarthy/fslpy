#!/usr/bin/env python
#
# glvtkobject.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy     as np
import OpenGL.GL as gl

import                            globject
import fsl.utils.transform     as transform
import fsl.fslview.gl.routines as glroutines
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


    def destroy(self):
        pass


    def _updateVertices(self, *a):

        vertices = self.overlay.vertices
        indices  = self.overlay.indices

        if self.opts.refImage is not None:
            xform = self.opts.getCoordSpaceTransform()

            if xform is not None:
                vertices = transform.transform(vertices, xform)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.indices  = np.array(indices,  dtype=np.uint32)
        self.onUpdate()

        
    def getDisplayBounds(self):
        return self.opts.getDisplayBounds()
        
    
    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax
 

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

        if xform is not None:
            clipPlaneVerts = transform.transform(clipPlaneVerts, xform)
            vertices       = transform.transform(vertices, xform)

        if zax == 0:
            print 'Z {}: {} -- clipping plane vertices: {}'.format(
                zax,
                zpos,
                clipPlaneVerts)

            print 'vertex limits: {} - {}'.format(
                vertices.min(axis=0), vertices.max(axis=0))

        vertices = vertices.ravel('C')
        
        planeEq = glroutines.planeEquation(clipPlaneVerts[0, :],
                                           clipPlaneVerts[1, :],
                                           clipPlaneVerts[2, :])

        gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
        gl.glEnable(gl.GL_CLIP_PLANE0)
        gl.glEnable(gl.GL_CULL_FACE)
        gl.glEnable(gl.GL_STENCIL_TEST)
        
        gl.glClipPlane(gl.GL_CLIP_PLANE0, planeEq)
        
        gl.glClear(gl.GL_STENCIL_BUFFER_BIT)

        gl.glColorMask(gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE, gl.GL_FALSE)

        # first pass - render front faces
        gl.glStencilFunc(gl.GL_ALWAYS, 0, 0)
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_INCR)
        gl.glCullFace(gl.GL_BACK)

        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
        gl.glDrawElements(gl.GL_TRIANGLES,
                          len(indices),
                          gl.GL_UNSIGNED_INT,
                          indices) 

        # Second pass - render back faces
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_DECR)
        gl.glCullFace(gl.GL_FRONT)
        
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
        gl.glDrawElements(gl.GL_TRIANGLES,
                          len(indices),
                          gl.GL_UNSIGNED_INT,
                          indices)
 
        # third pass - render the intersection
        # of the front and back faces from the
        # stencil buffer
        gl.glColorMask(gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE, gl.GL_TRUE)

        gl.glDisable(gl.GL_CLIP_PLANE0)
        gl.glDisable(gl.GL_CULL_FACE)

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
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY) 

    
    def postDraw(self):
        pass
