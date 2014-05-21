#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import numpy       as np

import                wx
import wx.glcanvas as wxgl

import OpenGL.GL   as gl

# Under OS X, I don't think I can request an OpenGL 3.2 core profile
# using wx - I'm stuck with OpenGL 2.1 I'm using these ARB extensions
# for functionality which is standard in 3.2.
import OpenGL.GL.ARB.instanced_arrays as arbia
import OpenGL.GL.ARB.draw_instanced   as arbdi

import fsl.data.fslimage       as fslimage
import fsl.fslview.glimagedata as glimagedata


# The vertex shader positions and colours a single vertex.
vertex_shader = """
#version 120

/* Opacity - constant for a whole image */
uniform float alpha;

/* image data texture */
uniform sampler3D dataBuffer;

/* Voxel coordinate -> world space transformation matrix */
uniform mat4 voxToWorldMat;

/* Image dimensions */
uniform float xdim;
uniform float ydim;
uniform float zdim;

/* Current vertex */
attribute vec3 inVertex;

/* Current voxel coordinates */
attribute float voxX;
attribute float voxY;
attribute float voxZ;

/* Voxel value passed through to fragment shader */ 
varying float fragVoxValue;

void main(void) {

    /*
     * Offset the vertex by the current voxel position
     * (and perform standard transformation from data
     * coordinates to screen coordinates).
     */
    vec3 vertPos = inVertex + vec3(voxX, voxY, voxZ);
    gl_Position = gl_ModelViewProjectionMatrix * \
        (voxToWorldMat * vec4(vertPos, 1.0));

    /* Pass the voxel value through to the shader. */
    float normVoxX = voxX / xdim + 0.5 / xdim;
    float normVoxY = voxY / ydim + 0.5 / ydim;
    float normVoxZ = voxZ / zdim + 0.5 / zdim;
    vec4 vt = texture3D(dataBuffer, vec3(normVoxX, normVoxY, normVoxZ));
    fragVoxValue = vt.r;
}
"""


# Buffer shader. Given the current voxel value, looks
# up the appropriate colour in the colour buffer.
fragment_shader = """
#version 120

uniform float     alpha;
uniform sampler1D colourMap;
varying float     fragVoxValue;

void main(void) {

    vec4  voxTexture = texture1D(colourMap, fragVoxValue);
    vec3  voxColour  = voxTexture.rgb;
    float voxAlpha   = alpha;

    if (voxTexture.a < voxAlpha) voxAlpha = voxTexture.a;

    gl_FragColor = vec4(voxColour, voxAlpha);
}
"""


class SliceCanvas(wxgl.GLCanvas):
    """
    A wx.glcanvas.GLCanvas which may be used to display a single 2D slice from
    a collection of 3D images (see fsl.data.fslimage.ImageList).
    """

    @property
    def zpos(self):
        """
        The slice currently being displayed.
        """
        return self._zpos

    @zpos.setter
    def zpos(self, zpos):
        """
        Change the slice being displayed. You will need to manually call
        Refresh() after changing the zpos.
        """

        if   zpos > self.zmax: zpos = self.zmax
        elif zpos < self.zmin: zpos = self.zmin

        self._zpos = zpos

    @property
    def xpos(self):
        """
        The current X (horizontal) location of the cursor. 
        """
        return self._xpos

    @xpos.setter
    def xpos(self, xpos):
        """
        Change the x cursor position. You will need to manually call
        Refresh() after changing the xpos.
        """ 

        if   xpos > self.xmax: xpos = self.xmax
        elif xpos < self.xmin: xpos = self.xmin

        self._xpos = xpos

    @property
    def ypos(self):
        """
        The current Y (vertical) location of the cursor.
        """
        return self._ypos

    @ypos.setter
    def ypos(self, ypos):
        """
        Change the y cursor position. You will need to manually call
        Refresh() after changing the ypos.
        """ 
        
        if   ypos > self.ymax: ypos = self.ymax
        elif ypos < self.ymin: ypos = self.ymin

        self._ypos = ypos


    def canvasToWorldX(self, xpos):
        """
        Given a pixel x coordinate on this canvas, translates it
        into the real world coordinates of the displayed slice.
        """

        realWidth   = float(self.xmax - self.xmin)
        sliceStart  = float(self._canvasBBox[0])
        sliceWidth  = float(self._canvasBBox[2])

        # Translate the xpos from the canvas to
        # the slice bounding box, then translate
        # the xpos from the slice bounding box
        # to real world coordinates
        xpos = xpos - sliceStart
        xpos = self.xmin  + (xpos / sliceWidth)  * realWidth

        return xpos


    def canvasToWorldY(self, ypos):
        """
        Given a pixel y coordinate on this canvas, translates it
        into the real world coordinates of the displayed slice.
        """
        
        realHeight   = float(self.ymax - self.ymin)
        sliceStart   = float(self._canvasBBox[1])
        sliceHeight  = float(self._canvasBBox[3])
        
        ypos = ypos - sliceStart
        ypos = self.ymin  + (ypos /  sliceHeight) *  realHeight

        return ypos 

        
    def __init__(self, parent, imageList, zax=0, context=None):
        """
        Creates a canvas object. The OpenGL data buffers are set up the
        first time that the canvas is displayed/drawn.
        
        Parameters:
        
          parent    - WX parent object
        
          imageList - a fslimage.ImageList object.
        
          zax       - Axis perpendicular to the plane to be displayed
                      (the 'depth' axis), default 0.

          context   - wx.glcanvas.GLContext object. If None, one is created.
        """

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.fslimage.ImageList instance') 

        wxgl.GLCanvas.__init__(self, parent)

        # Use the provided shared GL
        # context, or create a new one
        if context is None: self.context = wxgl.GLContext(self)
        else:               self.context = context

        self.imageList = imageList
        self.name      = 'SliceCanvas_{}'.format(id(self))

        # These attributes map from the image axes to
        # the display axes. xax is horizontal, yax
        # is vertical, and zax is depth.
        #
        # TODO Currently, the displayed x/horizontal and
        # y/vertical axes are defined by their order in
        # the image. We could allow the caller to specify
        # which axes should be horizontal/vertical.
        dims = range(3)
        dims.pop(zax)
        self.xax = dims[0]
        self.yax = dims[1]
        self.zax = zax

        self.xmin = imageList.minBounds[self.xax]
        self.ymin = imageList.minBounds[self.yax]
        self.zmin = imageList.minBounds[self.zax]
        self.xmax = imageList.maxBounds[self.xax]
        self.ymax = imageList.maxBounds[self.yax]
        self.zmax = imageList.maxBounds[self.zax]

        self._xpos = self.xmin + abs(self.xmax - self.xmin) / 2.0
        self._ypos = self.ymin + abs(self.ymax - self.ymin) / 2.0
        self._zpos = self.zmin + abs(self.zmax - self.zmin) / 2.0

        # When drawn, the slice does not necessarily take
        # up the entire canvas size, as its aspect ratio
        # is maintained. The _canvasBBox attribute is used
        # to store the [x, y, width, height] bounding box
        # within which the slice is actually drawn. It is
        # updated by the _calculateCanvasBBox method
        # whenever the canvas is resized
        self._canvasBBox = [0, 0, 0, 0]
        self.Bind(wx.EVT_SIZE, self._calculateCanvasBBox)

        # This flag is set by the _initGLData method
        # when it has finished initialising the OpenGL
        # shaders
        self.glReady = False

        # All the work is done by the draw method
        self.Bind(wx.EVT_PAINT, self.draw)

        # When the image list changes, refresh the
        # display, and update the display bounds
        self.imageList.addListener(lambda il: self._imageListChanged())


    def _imageListChanged(self):
        """
        This method is called once by _initGLData on the first draw, and
        then again every time an image is added or removed from the
        image list. For newly added images, it creates a GLImageData
        object, which initialises the OpenGL data necessary to render
        the image. This method also updates the canvas bounds (i.e.
        the min/max x/y/z coordinates across all images being displayed).
        """

        # Update the minimum/maximum
        # image bounds along each axis
        self.xmin = self.imageList.minBounds[self.xax]
        self.ymin = self.imageList.minBounds[self.yax]
        self.zmin = self.imageList.minBounds[self.zax]

        self.xmax = self.imageList.maxBounds[self.xax]
        self.ymax = self.imageList.maxBounds[self.yax]
        self.zmax = self.imageList.maxBounds[self.zax]

        # reset the cursor in case the
        # old values were out of bounds
        self.xpos = self.xpos
        self.ypos = self.ypos
        self.zpos = self.zpos

        # Create a GLImageData object for any new images,
        # and attach a listener to their display properties
        # so we know when to refresh the canvas.
        for image in self.imageList:
            try:

                # TODO I could share GLImageData instances
                # across different canvases which are
                # displaying the image with the same axis
                # orientation. Could store the GLImageData
                # object with a geneic name, e.g.
                # "GLImageData_0_1_2", where 0, 1, 2, are
                # the screen x/y/z axes.
                glData = image.getAttribute(self.name)
                continue
                
            except KeyError:
                pass
                
            glData = glimagedata.GLImageData(image, self.xax, self.yax)
            image.setAttribute(self.name, glData)

            def refresh(*a):
                self.Refresh()

            image.display.addListener('enabled',    self.name, refresh)
            image.display.addListener('alpha',      self.name, refresh)
            image.display.addListener('displayMin', self.name, refresh)
            image.display.addListener('displayMax', self.name, refresh)
            image.display.addListener('rangeClip',  self.name, refresh)
            image.display.addListener('cmap',       self.name, refresh)

        self.Refresh()


    def _compileShaders(self):
        """
        Compiles and links the vertex and fragment shader programs,
        and returns a reference to the resulting program. Raises
        an error if compilation/linking fails.

        I'm explicitly not using the PyOpenGL
        OpenGL.GL.shaders.compileProgram function, because it
        attempts to validate the program after compilation, which
        fails due to texture data not being bound at the time of
        validation.
        """

        # vertex shader
        vertShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertShader, vertex_shader)
        gl.glCompileShader(vertShader)
        vertResult = gl.glGetShaderiv(vertShader, gl.GL_COMPILE_STATUS)

        if vertResult != gl.GL_TRUE:
            raise '{}'.format(gl.glGetShaderInfoLog(vertShader))

        # fragment shader
        fragShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragShader, fragment_shader)
        gl.glCompileShader(fragShader)
        fragResult = gl.glGetShaderiv(fragShader, gl.GL_COMPILE_STATUS)

        if fragResult != gl.GL_TRUE:
            raise '{}'.format(gl.glGetShaderInfoLog(fragShader))

        # link all of the shaders!
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertShader)
        gl.glAttachShader(program, fragShader)

        gl.glLinkProgram(program)

        gl.glDeleteShader(vertShader)
        gl.glDeleteShader(fragShader)

        linkResult = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)

        if linkResult != gl.GL_TRUE:
            raise '{}'.format(gl.glGetProgramInfoLog(program))

        return program


    def _initGLData(self):
        """
        Compiles the vertex and fragment shader programs, and
        stores references to the shader variables as attributes
        of this SliceCanvas object. This method is only called
        once, on the first draw.
        """

        # A bit hacky. We can only set the GL context (and create
        # the GL data) once something is actually displayed on the
        # screen. The _initGLData method is called (asynchronously)
        # by the draw() method if it sees that the glReady flag has
        # not yet been set. But draw() may be called mored than once
        # before _initGLData is called. Here, to prevent
        # _initGLData from running more than once, the first time
        # it is called it simply overwrites itself with a dummy method.
        self._initGLData = lambda s: s
 
        self.context.SetCurrent(self)

        self.shaders = self._compileShaders()

        # Indices of all vertex/fragment shader parameters
        self.alphaPos         = gl.glGetUniformLocation(self.shaders, 'alpha')
        self.dataBufferPos    = gl.glGetUniformLocation(self.shaders,
                                                        'dataBuffer')
        self.voxToWorldMatPos = gl.glGetUniformLocation(self.shaders,
                                                        'voxToWorldMat')
        self.colourMapPos     = gl.glGetUniformLocation(self.shaders,
                                                        'colourMap') 
        self.xdimPos          = gl.glGetUniformLocation(self.shaders, 'xdim')
        self.ydimPos          = gl.glGetUniformLocation(self.shaders, 'ydim')
        self.zdimPos          = gl.glGetUniformLocation(self.shaders, 'zdim')        
        self.inVertexPos      = gl.glGetAttribLocation( self.shaders,
                                                        'inVertex')
        self.voxXPos          = gl.glGetAttribLocation( self.shaders, 'voxX')
        self.voxYPos          = gl.glGetAttribLocation( self.shaders, 'voxY')
        self.voxZPos          = gl.glGetAttribLocation( self.shaders, 'voxZ')

        # initialise data for the images that
        # are already in the image list 
        self._imageListChanged()

        self.glReady = True


    def _calculateCanvasBBox(self, ev):
        """
        Calculates the best size to draw the slice, maintaining its
        aspect ratio, within the given (maximum) width and height.
        """

        size = self.GetClientSize()

        if (size.width == 0) or (size.height == 0):
            return
        
        width  = float(size.width)
        height = float(size.height)

        realWidth  = float(self.xmax - self.xmin)
        realHeight = float(self.ymax - self.ymin)

        realRatio   = realWidth / realHeight
        canvasRatio = width     / height
        
        if canvasRatio >= realRatio:
            width  = realWidth  * (height / realHeight)
        else:
            height = realHeight * (width  / realWidth)

        width  = int(np.floor(width))
        height = int(np.floor(height))

        # center the slice within
        # the available space
        x = 0
        y = 0
        if width  != size.width:  x = (size.width  - width)  / 2
        if height != size.height: y = (size.height - height) / 2

        self._canvasBBox = [x, y, width, height]

        return width, height

        
    def resize(self):
        """
        Sets up the GL canvas size, viewport, and
        projection. This method is called by draw(),
        so does not need to be called manually.
        """

        x, y, width, height = self._canvasBBox

        # set up 2D orthographic drawing
        gl.glViewport(x, y, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(self.xmin,       self.xmax,
                   self.ymin,       self.ymax,
                   self.zmin - 100, self.zmax + 100)
        # I don't know why the above +/-100 is necessary :(
        # The '100' is arbitrary, but it seems that I need
        # to extend the depth clipping range beyond the
        # range of the data. This is despite the fact that
        # below, I'm actually translating the displayed
        # slice to Z=0! I don't understand OpenGL sometimes.
        # Most of the time.

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # Rotate world space so the displayed slice
        # is visible and correctly oriented
        # TODO There's got to be a more generic way
        # to perform this rotation. This will break
        # if I add functionality allowing the user
        # to specifty the x/y axes on initialisation.
        if self.zax == 0:
            gl.glRotatef(-90, 1, 0, 0)
            gl.glRotatef(-90, 0, 0, 1)
            
        elif self.zax == 1:
            gl.glRotatef(270, 1, 0, 0)

        # move the currently displayed slice to screen Z coord 0
        trans = [0, 0, 0]
        trans[self.zax] = -self.zpos 
        gl.glTranslatef(*trans)


    def draw(self, ev):
        """
        Draws the currently selected slice to the canvas.
        """

        # image data has not been initialised.
        if not self.glReady:
            wx.CallAfter(self._initGLData)
            return

        self.context.SetCurrent(self)
        self.resize()

        # clear the canvas
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # load the shaders
        gl.glUseProgram(self.shaders)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # disable interpolation
        gl.glShadeModel(gl.GL_FLAT)

        for image in self.imageList:

            # The GL data is stored as an attribute of the image,
            # and is created in the _imageListChanged method when
            # images are added to the image. If there's no data
            # here, ignore it; hopefully by the time draw() is
            # called again, it will have been created.
            try:    glImageData = image.getAttribute(self.name)
            except: continue
            
            imageDisplay = image.display
            dataBuffer   = glImageData.dataBuffer
            voxXBuffer   = glImageData.voxXBuffer
            voxYBuffer   = glImageData.voxYBuffer
            voxZBuffer   = glImageData.voxZBuffer
            geomBuffer   = glImageData.geomBuffer
            colourBuffer = glImageData.colourBuffer

            xdim = image.shape[self.xax]
            ydim = image.shape[self.yax]
            zdim = image.shape[self.zax]

            # Don't draw the slice if this
            # image display is disabled
            if not imageDisplay.enabled: continue 

            # Figure out which slice we are drawing,
            # and if it's out of range, don't draw it
            zi = int(image.worldToVox(self.zpos, self.zax))
            if zi < 0 or zi >= zdim: continue

            # bind the current alpha value
            # to the shader alpha variable
            gl.glUniform1f(self.alphaPos, imageDisplay.alpha)

            # Bind the voxel coordinate buffers
            gl.glUniform1f(self.xdimPos,  glImageData.imageTexShape[0])
            gl.glUniform1f(self.ydimPos,  glImageData.imageTexShape[1])
            gl.glUniform1f(self.zdimPos,  glImageData.imageTexShape[2])

            # bind the transformation matrix
            # to the shader variable
            xmat = np.array(image.voxToWorldMat, dtype=np.float32)
            gl.glUniformMatrix4fv(self.voxToWorldMatPos, 1, True, xmat)

            # Set up the colour texture
            gl.glActiveTexture(gl.GL_TEXTURE0) 
            gl.glBindTexture(gl.GL_TEXTURE_1D, colourBuffer)
            gl.glUniform1i(self.colourMapPos, 0) 

            # Set up the image data texture
            gl.glActiveTexture(gl.GL_TEXTURE1) 
            gl.glBindTexture(gl.GL_TEXTURE_3D, dataBuffer)
            gl.glUniform1i(self.dataBufferPos, 1)
            
            # voxel x/y/z coordinates
            voxOffs  = [0, 0, 0]
            voxSteps = [1, 1, 1]
            voxOffs[ self.zax] = zi
            voxSteps[self.yax] = xdim
            voxSteps[self.zax] = xdim * ydim
            for buf, pos, step, off in zip(
                    (voxXBuffer, voxYBuffer, voxZBuffer),
                    (self.voxXPos, self.voxYPos, self.voxZPos),
                    voxSteps,
                    voxOffs):

                if off == 0: off = None
                else:        off = buf + (off * 4)
                
                buf.bind()
                gl.glVertexAttribPointer(
                    pos,
                    1,
                    gl.GL_FLOAT,
                    gl.GL_FALSE,
                    0,
                    off)
                gl.glEnableVertexAttribArray(pos)
                arbia.glVertexAttribDivisorARB(pos, step)

            # The geometry buffer, which defines the geometry of a
            # single vertex (4 vertices, drawn as a triangle strip)
            geomBuffer.bind()
            gl.glVertexAttribPointer(
                self.inVertexPos,
                3,
                gl.GL_FLOAT,
                gl.GL_FALSE,
                0,
                None)
            gl.glEnableVertexAttribArray(self.inVertexPos)
            arbia.glVertexAttribDivisorARB(self.inVertexPos, 0)

            # Draw all of the triangles!
            arbdi.glDrawArraysInstancedARB(
                gl.GL_TRIANGLE_STRIP, 0, 4, xdim * ydim)

            gl.glDisableVertexAttribArray(self.inVertexPos)
            gl.glDisableVertexAttribArray(self.voxXPos)
            gl.glDisableVertexAttribArray(self.voxYPos)
            gl.glDisableVertexAttribArray(self.voxZPos)

        gl.glUseProgram(0)

        # A vertical line at xpos, and a horizontal line at ypos

        xverts = np.zeros((2, 3))
        yverts = np.zeros((2, 3))

        # add a little padding to the lines if they are
        # on the boundary, so they don't get cropped
        if self.xpos == self.xmin: xverts[:, self.xax] = self.xpos + 0.5
        else:                      xverts[:, self.xax] = self.xpos
        if self.ypos == self.ymin: yverts[:, self.yax] = self.ypos + 0.5
        else:                      yverts[:, self.yax] = self.ypos        

        xverts[:, self.yax] = [self.ymin, self.ymax]
        xverts[:, self.zax] =  self.zpos + 1
        yverts[:, self.xax] = [self.xmin, self.xmax]
        yverts[:, self.zax] =  self.zpos + 1

        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex3f(*xverts[0])
        gl.glVertex3f(*xverts[1])
        gl.glVertex3f(*yverts[0])
        gl.glVertex3f(*yverts[1])
        gl.glEnd()

        self.SwapBuffers()
