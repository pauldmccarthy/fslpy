#!/usr/bin/env python
#
# slicecanvas.py - A wx.GLCanvas canvas which displays a single
# slice from a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path     as op

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
import fsl.props               as props
import fsl.fslview.glimagedata as glimagedata

# Locations of the shader source files.
_vertex_shader_file   = op.join(op.dirname(__file__), 'vertex_shader.glsl')
_fragment_shader_file = op.join(op.dirname(__file__), 'fragment_shader.glsl')


class SliceCanvas(wxgl.GLCanvas, props.HasProperties):
    """
    A wx.glcanvas.GLCanvas which may be used to display a single 2D slice from
    a collection of 3D images (see fsl.data.fslimage.ImageList).
    """

    # The xpos and ypos properties specify the current
    # position of a 'cursor', which is highlighted with
    # green crosshairs. The zpos property specifies the
    # currently displayed slice. These three properties
    # are all in world coordinates.
    xpos       = props.Double(clamped=True)
    ypos       = props.Double(clamped=True)
    zpos       = props.Double(clamped=True)

    # The x/y/z min/max properties specify the display
    # range, in world coordinates, of the canvas.
    xmin       = props.Double(clamped=True)
    xmax       = props.Double(clamped=True)
    ymin       = props.Double(clamped=True)
    ymax       = props.Double(clamped=True)
    zmin       = props.Double(clamped=True)
    zmax       = props.Double(clamped=True)

    # If False, the green crosshairs which show the
    # current cursor location will not be drawn.
    showCursor = props.Boolean(default=True)

    
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
        props.HasProperties.__init__(self)

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

        self.xpos = self.xmin + abs(self.xmax - self.xmin) / 2.0
        self.ypos = self.ymin + abs(self.ymax - self.ymin) / 2.0
        self.zpos = self.zmin + abs(self.zmax - self.zmin) / 2.0

        # The x/y/z pos properties are limited
        # to the x/y/z min/max bounds
        self._setPropertyConstraints()

        # when any of the xyz properties of
        # this canvas change, we need to redraw
        def posRefresh(  *a): self._refresh()
        def boundRefresh(*a): self._refresh(True)
            
        self.addListener('xpos',       self.name, posRefresh)
        self.addListener('ypos',       self.name, posRefresh)
        self.addListener('zpos',       self.name, posRefresh)
        self.addListener('xmin',       self.name, boundRefresh)
        self.addListener('xmax',       self.name, boundRefresh)
        self.addListener('ymin',       self.name, boundRefresh)
        self.addListener('ymax',       self.name, boundRefresh)
        self.addListener('zmin',       self.name, boundRefresh)
        self.addListener('zmax',       self.name, boundRefresh)
        self.addListener('showCursor', self.name, boundRefresh) 

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
        self.Bind(wx.EVT_PAINT, self._draw)

        # When the image list changes, refresh the
        # display, and update the display bounds
        self.imageList.addListener(lambda il: self._imageListChanged())


    def _setPropertyConstraints(self):
        """
        Updates the constraints on each of the x/y/z pos and min/max
        properties so they are all limited to stay within a valid
        range.
        """

        xmin = self.imageList.minBounds[self.xax]
        xmax = self.imageList.maxBounds[self.xax]
        ymin = self.imageList.minBounds[self.yax]
        ymax = self.imageList.maxBounds[self.yax]
        zmin = self.imageList.minBounds[self.zax]
        zmax = self.imageList.maxBounds[self.zax]

        self.setConstraint('xpos', 'minval', self.xmin)
        self.setConstraint('xpos', 'maxval', self.xmax)
        self.setConstraint('ypos', 'minval', self.ymin)
        self.setConstraint('ypos', 'maxval', self.ymax)
        self.setConstraint('zpos', 'minval', self.zmin)
        self.setConstraint('zpos', 'maxval', self.zmax) 

        for xprop in ['xmin', 'xmax']:
            self.setConstraint(xprop, 'minval', xmin)
            self.setConstraint(xprop, 'maxval', xmax)
        for yprop in ['ymin', 'ymax']:
            self.setConstraint(yprop, 'minval', ymin)
            self.setConstraint(yprop, 'maxval', ymax)
        for zprop in ['zmin', 'zmax']:
            self.setConstraint(zprop, 'minval', zmin)
            self.setConstraint(zprop, 'maxval', zmax)

        # reset the cursor and min/max values in
        # case the old values were out of bounds
        self.xpos = self.xpos
        self.ypos = self.ypos
        self.zpos = self.zpos
        self.xmin = self.xmin
        self.xmax = self.xmax
        self.ymin = self.ymin
        self.ymax = self.ymax
        self.zmin = self.zmin
        self.zmax = self.zmax 

            
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
        self._setPropertyConstraints()

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

            def refresh(*a): self._refresh()

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

        with open(_vertex_shader_file,   'rt') as f: vertShaderSrc = f.read()
        with open(_fragment_shader_file, 'rt') as f: fragShaderSrc = f.read()

        # vertex shader
        vertShader = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vertShader, vertShaderSrc)
        gl.glCompileShader(vertShader)
        vertResult = gl.glGetShaderiv(vertShader, gl.GL_COMPILE_STATUS)

        if vertResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(vertShader)))

        # fragment shader
        fragShader = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fragShader, fragShaderSrc)
        gl.glCompileShader(fragShader)
        fragResult = gl.glGetShaderiv(fragShader, gl.GL_COMPILE_STATUS)

        if fragResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetShaderInfoLog(fragShader)))

        # link all of the shaders!
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vertShader)
        gl.glAttachShader(program, fragShader)

        gl.glLinkProgram(program)

        gl.glDeleteShader(vertShader)
        gl.glDeleteShader(fragShader)

        linkResult = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)

        if linkResult != gl.GL_TRUE:
            raise RuntimeError('{}'.format(gl.glGetProgramInfoLog(program)))

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


    def _refresh(self, constraints=False):
        """
        Called when a display property changes. Updates x/y/z property
        values, updates the canvas bounding box, and triggers a redraw.
        """
        
        if constraints: self._setPropertyConstraints()
        self._calculateCanvasBBox(None)
        self.Refresh()

        
    def _calculateCanvasBBox(
            self,
            ev,
            canvasWidth=None,
            canvasHeight=None,
            worldWidth=None,
            worldHeight=None):
        """
        Calculates the best size to draw the slice, maintaining its
        aspect ratio, within the current canvas size. The
        worldWidth/worldHeight parameters, if provided, are used
        to calculate the displayed world space aspect ratio. If not
        provided, they are calculated from the min/max bounds of
        the displayed image list.
        """

        size = self.GetClientSize()

        if canvasWidth  is None: canvasWidth  = size.width
        if canvasHeight is None: canvasHeight = size.height

        # canvas is not yet displayed
        if canvasWidth  == 0 or \
           canvasHeight == 0 or \
           worldWidth   == 0 or \
           worldHeight  == 0:
            return

        canvasWidth  = float(canvasWidth)
        canvasHeight = float(canvasHeight)

        if worldWidth  is None: worldWidth  = float(abs(self.xmax - self.xmin))
        if worldHeight is None: worldHeight = float(abs(self.ymax - self.ymin))

        worldRatio  = worldWidth  / worldHeight
        canvasRatio = canvasWidth / canvasHeight
        
        if canvasRatio >= worldRatio:
            canvasWidth  = worldWidth  * (canvasHeight / worldHeight)
        else:
            canvasHeight = worldHeight * (canvasWidth  / worldWidth)

        canvasWidth  = int(np.floor(canvasWidth))
        canvasHeight = int(np.floor(canvasHeight))

        # if the canvas size is smaller than the window size,
        # centre the slice within the available space
        x = 0
        y = 0
        if canvasWidth  < size.width:  x = (size.width  - canvasWidth)  / 2
        if canvasHeight < size.height: y = (size.height - canvasHeight) / 2

        self._canvasBBox = [x, y, canvasWidth, canvasHeight]

        
    def _resize(self,
                bbox=None,
                xmin=None,
                xmax=None,
                ymin=None,
                ymax=None,
                zmin=None,
                zmax=None):
        """
        Sets up the GL canvas size, viewport, and
        projection. This method is called by draw(),
        so does not need to be called manually.
        """

        if bbox is None: bbox = self._canvasBBox
        if xmin is None: xmin = self.xmin
        if xmax is None: xmax = self.xmax
        if ymin is None: ymin = self.ymin
        if ymax is None: ymax = self.ymax
        if zmin is None: zmin = self.zmin
        if zmax is None: zmax = self.zmax

        x, y, width, height = bbox

        # If there are no images to be displayed,
        # the dimension bounds will all be 0,
        # which causes glOrtho to throw an error.
        if len(self.imageList) == 0:
            xmin = -1.0
            xmax =  1.0
            ymin = -1.0
            ymax =  1.0

        # set up 2D orthographic drawing
        gl.glViewport(x, y, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(xmin,       xmax,
                   ymin,       ymax,
                   zmin - 100, zmax + 100)
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

        
    def _drawSlice(self, image, sliceno, xform=None):
        """
        Draws the specified slice from the specified image on the
        canvas. If xform is not provided, the image.voxToWorldMat
        transformation matrix is used.
        """

        # The GL data is stored as an attribute of the image,
        # and is created in the _imageListChanged method when
        # images are added to the image. If there's no data
        # here, ignore it; hopefully by the time draw() is
        # called again, it will have been created.
        try:    glImageData = image.getAttribute(self.name)
        except: return
        
        imageDisplay = image.display

        xdim = image.shape[self.xax]
        ydim = image.shape[self.yax]
        zdim = image.shape[self.zax]

        # Don't draw the slice if this
        # image display is disabled
        if not imageDisplay.enabled: return

        # if the slice is out of range, don't draw it
        if sliceno < 0 or sliceno >= zdim: return

        # bind the current alpha value
        # to the shader alpha variable
        gl.glUniform1f(self.alphaPos, imageDisplay.alpha)

        # Bind the voxel coordinate buffers
        gl.glUniform1f(self.xdimPos,  glImageData.imageTexShape[0])
        gl.glUniform1f(self.ydimPos,  glImageData.imageTexShape[1])
        gl.glUniform1f(self.zdimPos,  glImageData.imageTexShape[2])

        # bind the transformation matrix
        # to the shader variable
        if xform is None:
            xform = np.array(image.voxToWorldMat, dtype=np.float32)
        xform = xform.ravel('C')
        gl.glUniformMatrix4fv(self.voxToWorldMatPos, 1, False, xform)

        # Set up the colour texture
        gl.glActiveTexture(gl.GL_TEXTURE0) 
        gl.glBindTexture(gl.GL_TEXTURE_1D, glImageData.colourBuffer)
        gl.glUniform1i(self.colourMapPos, 0) 

        # Set up the image data texture
        gl.glActiveTexture(gl.GL_TEXTURE1) 
        gl.glBindTexture(gl.GL_TEXTURE_3D, glImageData.dataBuffer)
        gl.glUniform1i(self.dataBufferPos, 1)
        
        # voxel x/y/z coordinates
        voxOffs  = [0, 0, 0]
        voxSteps = [1, 1, 1]
        voxOffs[ self.zax] = sliceno
        voxSteps[self.yax] = xdim
        voxSteps[self.zax] = xdim * ydim
        for buf, pos, step, off in zip(
                (glImageData.voxXBuffer,
                 glImageData.voxYBuffer,
                 glImageData.voxZBuffer),
                (self.voxXPos,
                 self.voxYPos,
                 self.voxZPos),
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
        glImageData.geomBuffer.bind()
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


    def _draw(self, ev):
        """
        Draws the currently selected slice to the canvas.
        """

        # image data has not been initialised.
        if not self.glReady:
            wx.CallAfter(self._initGLData)
            return

        self.context.SetCurrent(self)
        self._resize()

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

            zi = int(image.worldToVox(self.zpos, self.zax))
            self._drawSlice(image, zi)

        gl.glUseProgram(0)

        if self.showCursor:

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
