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


class GLModel(globject.GLObject):

    def __init__(self, overlay, display):

        globject.GLObject.__init__(self)

        self.overlay = overlay
        self.display = display
        self.opts    = display.getDisplayOpts()


    def destroy(self):
        pass

        
    def getDisplayBounds(self):
        return self.overlay.getBounds()
        
    
    def setAxes(self, xax, yax):
        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax

        self._prepareOutlineVertices()
 


    def _prepareOutlineVertices(self):

        verts   = self.overlay.vertices
        mean    = verts.mean(axis=0)

        verts   = verts - mean
        
        verts[:, self.xax] *= 0.9
        verts[:, self.yax] *= 0.9

        verts += mean

        self.outlineVertices = verts


    def preDraw(self):

        pass

    
    def draw(self, zpos, xform=None):

        if self.opts.outline: self.drawOutline(zpos, xform)
        else:                 self.drawFilled( zpos, xform)


    def drawFilled(self, zpos, xform):

        xax = self.xax
        yax = self.yax
        zax = self.zax

        vertices = self.overlay.vertices
        indices  = self.overlay.indices

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
            vertices       = transform.transform(vertices, xform).ravel('C')
            

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

        colour    = self.opts.colour
        colour[3] = self.display.alpha
        
        gl.glColor(*colour)
        gl.glBegin(gl.GL_QUADS)

        gl.glVertex3f(*clipPlaneVerts[0, :])
        gl.glVertex3f(*clipPlaneVerts[1, :])
        gl.glVertex3f(*clipPlaneVerts[2, :])
        gl.glVertex3f(*clipPlaneVerts[3, :])
        gl.glEnd()

        gl.glDisable(gl.GL_STENCIL_TEST)
        gl.glDisableClientState(gl.GL_VERTEX_ARRAY) 

    
    def drawOutline(self, zpos, xform):
        xax = self.xax
        yax = self.yax
        zax = self.zax

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

        planeEq = glroutines.planeEquation(clipPlaneVerts[0, :],
                                           clipPlaneVerts[1, :],
                                           clipPlaneVerts[2, :])

        vertices   = self.overlay.vertices
        olVertices = self.outlineVertices
        indices    = self.overlay.indices
        
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

        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_INCR)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, olVertices)
        gl.glDrawElements(gl.GL_TRIANGLES,
                          len(indices),
                          gl.GL_UNSIGNED_INT,
                          indices) 

        # Second pass - render back faces
        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_INCR)
        gl.glCullFace(gl.GL_FRONT)
        
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, vertices)
        gl.glDrawElements(gl.GL_TRIANGLES,
                          len(indices),
                          gl.GL_UNSIGNED_INT,
                          indices)

        gl.glStencilOp(gl.GL_KEEP, gl.GL_KEEP, gl.GL_INCR)
        gl.glVertexPointer(3, gl.GL_FLOAT, 0, olVertices)
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

        gl.glStencilFunc(gl.GL_EQUAL, 3, 255)

        colour    = self.opts.colour
        colour[3] = self.display.alpha
        
        gl.glColor(*colour)
        gl.glBegin(gl.GL_QUADS)

        gl.glVertex3f(*clipPlaneVerts[0, :])
        gl.glVertex3f(*clipPlaneVerts[1, :])
        gl.glVertex3f(*clipPlaneVerts[2, :])
        gl.glVertex3f(*clipPlaneVerts[3, :])
        gl.glEnd()

        gl.glStencilFunc(gl.GL_EQUAL, 1, 255)

        colour    = self.opts.colour
        colour[3] = self.display.alpha
        
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
