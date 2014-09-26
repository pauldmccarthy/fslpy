#!/usr/bin/env python
#
# slicecanvas.py - Provides the SliceCanvas class, which contains the
# functionality to display a single slice from a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides the :class:`SliceCanvas` class, which contains the functionality
to display a single slice from a collection of 3D images.

The :class:`SliceCanvas` class is not intended to be instantiated - use one
of the subclasses:

  - :class:`~fsl.fslview.gl.osmesaslicecanvas.OSMesaSliceCanvas` for static
    off-screen rendering of a scene.
    
  - :class:`~fsl.fslview.gl.wxglslicecanvas.WXGLSliceCanvas` for interactive
    rendering on a :class:`wx.glcanvas.GLCanvas` canvas.
"""

import logging
log = logging.getLogger(__name__)

import numpy                  as np 
import OpenGL.GL              as gl

import props

import fsl.data.image          as fslimage
import fsl.fslview.gl          as fslgl
import fsl.fslview.gl.globject as globject


class SliceCanvas(props.HasProperties):
    """Represens a canvas which may be used to display a single 2D slice from a
    collection of 3D images (see :class:`fsl.data.image.ImageList`).
    """

    pos = props.Point(ndims=3)
    """The currently displayed position. The ``pos.x`` and ``pos.y`` positions
    denote the position of a 'cursor', which is highlighted with green
    crosshairs. The ``pos.z`` position specifies the currently displayed
    slice. While the values of this point are in the image list world
    coordinates, the dimension ordering may not be the same as the image list
    dimension ordering. For this position, the x and y dimensions correspond
    to horizontal and vertical on the screen, and the z dimension to 'depth'.
    """


    zoom = props.Real(minval=1.0,
                      maxval=10.0, 
                      default=1.0,
                      clamped=True)
    """The image bounds are divided by this zoom
    factor to produce the display bounds.
    """

    
    displayBounds = props.Bounds(ndims=2)
    """The display bound x/y values specify the horizontal/vertical display
    range of the canvas, in world coordinates. This may be a larger area
    than the size of the displayed images, as it is adjusted to preserve the
    aspect ratio.
    """

    
    showCursor = props.Boolean(default=True)
    """If ``False``, the green crosshairs which show
    the current cursor location will not be drawn.
    """
 

    zax = props.Choice((0, 1, 2), ('X axis', 'Y axis', 'Z axis'))
    """The image axis to be used as the screen 'depth' axis."""


    def _getSize(self):
        """Must be provided by subclasses of :class:`SliceCanvas`. The default
        implementation raises a :class:`NotImplementedError`.

        Subclass implementations must return a tuple containing the current
        canvas width and height.
        """
        raise NotImplementedError()

        
    def _makeGLContext(self):
        """Must be provided by subclasses of :class:`SliceCanvas`. The default
        implementation raises a :class:`NotImplementedError`.

        Subclass implementations must create and return a handle to an OpenGL
        context. This context will be stored as an object attribute called
        `glContext`.
        """
        raise NotImplementedError()

        
    def _setGLContext(self):
        """Must be provided by subclasses of :class:`SliceCanvas`. The default
        implementation raises a :class:`NotImplementedError`.

        Subclass implementations must set the current context.
        """
        raise NotImplementedError()

        
    def _refresh(self):
        """Must be provided by subclasses of :class:`SliceCanvas`. The default
        implementation raises a :class:`NotImplementedError`.

        Subclass implementations must refresh the canvas.
        """
        raise NotImplementedError()

        
    def _postDraw(self):
        """Must be provided by subclasses of :class:`SliceCanvas`. The default
        implementation raises a :class:`NotImplementedError`.

        Subclass implementations can do anything that must be done after the
        canvas has been drawn to (e.g. swapping buffers for double buffering).
        """
        raise NotImplementedError()

    
    def canvasToWorld(self, xpos, ypos):
        """Given pixel x/y coordinates on this canvas, translates them
        into the real world coordinates of the displayed slice.
        """

        realWidth                 = self.displayBounds.xlen
        realHeight                = self.displayBounds.ylen
        canvasWidth, canvasHeight = map(float, self._getSize())

        if realWidth    == 0 or \
           canvasWidth  == 0 or \
           realHeight   == 0 or \
           canvasHeight == 0:
            return 0 
        
        xpos = self.displayBounds.xlo + (xpos / canvasWidth)  * realWidth
        ypos = self.displayBounds.ylo + (ypos / canvasHeight) * realHeight

        return xpos, ypos


    def panDisplayBy(self, xoff, yoff):
        """Pans the canvas display by the given x/y offsets (specified in
        world coordinates).
        """
        
        bounds = self.displayBounds

        xmin, xmax, ymin, ymax = bounds[:]

        xmin = xmin + xoff
        xmax = xmax + xoff
        ymin = ymin + yoff
        ymax = ymax + yoff

        if xmin < bounds.getMin(0):
            xmin = bounds.getMin(0)
            xmax = xmin + bounds.getLen(0)
            
        elif xmax > bounds.getMax(0):
            xmax = bounds.getMax(0)
            xmin = xmax - bounds.getLen(0)
            
        if ymin < bounds.getMin(1):
            ymin = bounds.getMin(1)
            ymax = ymin + bounds.getLen(1)

        elif ymax > bounds.getMax(1):
            ymax = bounds.getMax(1)
            ymin = ymax - bounds.getLen(1) 

        self.displayBounds[:] = [xmin, xmax, ymin, ymax]


    def panDisplayToShow(self, xpos, ypos):
        """Pans the display so that the given x/y position (in world
        coordinates) is visible.
        """

        bounds = self.displayBounds

        if xpos >= bounds.xlo and xpos <= bounds.xhi and \
           ypos >= bounds.ylo and ypos <= bounds.yhi: return

        xoff = 0
        yoff = 0

        if   xpos <= bounds.xlo: xoff = xpos - bounds.xlo
        elif xpos >= bounds.xhi: xoff = xpos - bounds.xhi
        
        if   ypos <= bounds.ylo: yoff = ypos - bounds.ylo
        elif ypos >= bounds.yhi: yoff = ypos - bounds.yhi
        
        if xoff != 0 or yoff != 0:
            self.panDisplayBy(xoff, yoff)

        
    def __init__(self,
                 imageList,
                 zax=0,
                 glContext=None,
                 glVersion=None):
        """Creates a canvas object. 

        .. note:: It is assumed that each :class:`~fsl.data.image.Image`
        contained in the ``imageList`` has an attribute called ``display``,
        which refers to an :class:`~fsl.fslview.displaycontext.ImageDisplay`
        instance defining how that image is to be displayed.
        
        :arg imageList:  An :class:`~fsl.data.image.ImageList` object.
        
        :arg zax:        Image axis perpendicular to the plane to be displayed
                         (the 'depth' axis), default 0.

        :arg glContext:  A :class:`wx.glcanvas.GLContext` object. If ``None``,
                         one is created.

        :arg glVersion:  A tuple containing the desired (major, minor) OpenGL
                         API version to use. If None, the best possible
                         version is used. 
        """

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.image.ImageList instance')

        props.HasProperties.__init__(self)

        # Use the provided shared GL
        # context, or create a new one
        if glContext is None: self.glContext = self._makeGLContext()
        else:                 self.glContext = glContext

        self.glVersion = glVersion
        self.imageList = imageList
        self.name      = '{}_{}'.format(self.__class__.__name__, id(self))

        # The zax property is the image axis which maps to the
        # 'depth' axis of this canvas. The _zAxisChanged method
        # also fixes the values of 'xax' and 'yax'.
        self.zax = zax
        self.xax = (zax + 1) % 3
        self.yax = (zax + 2) % 3
        self._zAxisChanged()

        # when any of the properties of this
        # canvas change, we need to redraw
        def refresh(*a): self._refresh()

        self.addListener('zax',           self.name, self._zAxisChanged)
        self.addListener('pos',           self.name, refresh)
        self.addListener('showCursor',    self.name, refresh)
        self.addListener('displayBounds', self.name, refresh)
        self.addListener('zoom',
                         self.name,
                         lambda *a: self._updateDisplayBounds())

        # When the image list changes, refresh the
        # display, and update the display bounds
        self.imageList.addListener('images',
                                   self.name,
                                   self._imageListChanged)
        self.imageList.addListener('bounds',
                                   self.name,
                                   self._imageBoundsChanged)
 
        # the _initGL method is called on the
        # first draw to initialise GL stuff
        self._glReady = False


    def _initGL(self):
        """We can't figure out what OpenGL version to use until a GL context
        has been created. So this method is called on the first draw.

        It initialises the :mod:`fsl.fslview.gl` package, and ensures that
        OpenGL data has been created for each image in the image list.
        """
        
        # Call the bootstrap function, which
        # will figure out which OpenGL version
        # to use, and do some module magic
        self._setGLContext()
        fslgl.bootstrap(self.glVersion)

        # Call the _imageListChanged method - it
        # will generate any necessary GL data for
        # each of the images (which can't be done
        # until the canvas is displayed).
        self._imageListChanged()

        self._glReady = True
 

    def draw(self, *a):
        """Draws the current scene to the canvas. 

        Ths actual drawing is managed by the OpenGL version-dependent
        :func:`fsl.fslview.gl.slicecanvas_draw.drawScene` function, which does
        the actual drawing.
        """

        if not self._glReady:
            self._initGL()
            return

        self._setGLContext()
        self._setViewport() 
        fslgl.slicecanvas_draw.draw(self)
        if self.showCursor: self.drawCursor()
        self._postDraw()


    def drawCursor(self):
        """Draws a green cursor at the current X/Y position."""
        
        # A vertical line at xpos, and a horizontal line at ypos
        xverts = np.zeros((2, 3))
        yverts = np.zeros((2, 3))

        xmin, xmax = self.imageList.bounds.getRange(self.xax)
        ymin, ymax = self.imageList.bounds.getRange(self.yax)

        x = self.pos.x
        y = self.pos.y

        # How big is one pixel in world space?
        w, h = self._getSize()
        pixx = (xmax - xmin) / float(w)
        pixy = (ymax - ymin) / float(h)

        # add a little padding to the lines if they are 
        # on the boundary, so they don't get cropped        
        if x <= xmin: x = xmin + 0.5 * pixx
        if x >= xmax: x = xmax - 0.5 * pixx
        if y <= ymin: y = ymin + 0.5 * pixy
        if y >= ymax: y = ymax - 0.5 * pixy 

        xverts[:, self.xax] = x
        yverts[:, self.yax] = y 
        xverts[:, self.yax] = [ymin, ymax]
        xverts[:, self.zax] =  self.pos.z + 1
        yverts[:, self.xax] = [xmin, xmax]
        yverts[:, self.zax] =  self.pos.z + 1

        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex3f(*xverts[0])
        gl.glVertex3f(*xverts[1])
        gl.glVertex3f(*yverts[0])
        gl.glVertex3f(*yverts[1])
        gl.glEnd()

        
    def _zAxisChanged(self, *a):
        """Called when the :attr:`zax` property is changed. Calculates
        the corresponding X and Y axes, and saves them as attributes of
        the object. Also regenerates the GL index buffers for every
        image in the image list, as they are dependent upon how the
        image is being displayed.
        """

        log.debug('{}'.format(self.zax))

        # Store the canvas position, in the
        # axis order of the image space
        pos                  = [None] * 3
        pos[self.xax]        = self.pos.x
        pos[self.yax]        = self.pos.y
        pos[pos.index(None)] = self.pos.z

        # Figure out the new x and y axes
        # based on the new zax value
        dims = range(3)
        dims.pop(self.zax)
        self.xax = dims[0]
        self.yax = dims[1]

        for image in self.imageList:

            try:   glData = image.getAttribute(self.name)

            # if this lookup fails, it means that the GL data
            # for this image has not yet been generated.
            except KeyError: continue

            glData.setAxes(self.xax, self.yax)

        self._imageBoundsChanged()
        
        # Reset the canvas position as, because the
        # z axis has been changed, the old coordinates
        # will be in the wrong dimension order
        self.pos.xyz = [pos[self.xax],
                        pos[self.yax],
                        pos[self.zax]]
 
            
    def _imageListChanged(self, *a):
        """This method is called every time an image is added or removed
        to/from the image list. For newly added images, it creates the
        appropriate :mod:`~fsl.fslview.gl.globject` type, which
        initialises the OpenGL data necessary to render the image, and then
        triggers a refresh.
        """

        # Create a GL object for any new images,
        # and attach a listener to their display
        # properties so we know when to refresh
        # the canvas.
        for image in self.imageList:

            try:
                image.getAttribute(self.name)
                continue
                
            except KeyError:
                pass

            display = image.getAttribute('display')

            def genGLObject(ctx=None, value=None, valid=None, disp=display):
                globj = globject.createGLObject(image, disp)
                image.setAttribute(self.name, globj)

                if globj is not None: globj.init(self.xax, self.yax)
                self._refresh()
            genGLObject()
                
            def refresh(*a): self._refresh()
            
            display.addListener('imageType',       self.name, genGLObject)
            display.addListener('enabled',         self.name, refresh)
            display.addListener('transform',       self.name, refresh)
            display.addListener('interpolation',   self.name, refresh)
            display.addListener('alpha',           self.name, refresh)
            display.addListener('displayRange',    self.name, refresh)
            display.addListener('clipLow',         self.name, refresh)
            display.addListener('clipHigh',        self.name, refresh)
            display.addListener('worldResolution', self.name, refresh)
            display.addListener('voxelResolution', self.name, refresh)
            display.addListener('cmap',            self.name, refresh)
            display.addListener('volume',          self.name, refresh)

        self._refresh()


    def _imageBoundsChanged(self, *a):
        """Called when the image list bounds are changed.

        Updates the constraints on the :attr:`pos` property so it is
        limited to stay within a valid range, and then calls the
        :meth:`_updateDisplayBounds` method.
        """

        imgBounds = self.imageList.bounds

        self.pos.setMin(0, imgBounds.getLo(self.xax))
        self.pos.setMax(0, imgBounds.getHi(self.xax))
        self.pos.setMin(1, imgBounds.getLo(self.yax))
        self.pos.setMax(1, imgBounds.getHi(self.yax))
        self.pos.setMin(2, imgBounds.getLo(self.zax))
        self.pos.setMax(2, imgBounds.getHi(self.zax))

        self._updateDisplayBounds()
        

    def _applyZoom(self, xmin, xmax, ymin, ymax):
        """'Zooms' in to the given rectangle according to the
        current value of the zoom property. Returns a 4-tuple
        containing the updated bound values.
        """

        if self.zoom == 1.0:
            return (xmin, xmax, ymin, ymax)
        
        zoomFactor  = 1.0 / self.zoom

        xlen = xmax - xmin
        ylen = ymax - ymin

        newxlen = xlen * zoomFactor
        newylen = ylen * zoomFactor

        xmin = self.pos.x - 0.5 * newxlen
        xmax = self.pos.x + 0.5 * newxlen
        ymin = self.pos.y - 0.5 * newylen
        ymax = self.pos.y + 0.5 * newylen

        xlen = xmax - xmin
        ylen = ymax - ymin

        bounds = self.displayBounds

        if xmin < bounds.getMin(0):
            xmin = bounds.getMin(0)
            xmax = xmin + xlen
            
        elif xmax > bounds.getMax(0):
            xmax = bounds.getMax(0)
            xmin = xmax - xlen
            
        if ymin < bounds.getMin(1):
            ymin = bounds.getMin(1)
            ymax = ymin + ylen

        elif ymax > bounds.getMax(1):
            ymax = bounds.getMax(1)
            ymin = ymax - ylen

        return (xmin, xmax, ymin, ymax)

        
    def _updateDisplayBounds(self, xmin=None, xmax=None, ymin=None, ymax=None):
        """Called on canvas resizes, image bound changes, and zoom changes.
        
        Calculates the bounding box, in world coordinates, to be displayed on
        the canvas. Stores this bounding box in the displayBounds property. If
        any of the parameters are not provided, the image list
        :attr:`fsl.data.image.ImageList.bounds` are used.

        :arg xmin: Minimum x (horizontal) value to be in the display bounds.
        :arg xmax: Maximum x value to be in the display bounds.
        :arg ymin: Minimum y (vertical) value to be in the display bounds.
        :arg ymax: Maximum y value to be in the display bounds.
        """

        if xmin is None: xmin = self.imageList.bounds.getLo(self.xax)
        if xmax is None: xmax = self.imageList.bounds.getHi(self.xax)
        if ymin is None: ymin = self.imageList.bounds.getLo(self.yax)
        if ymax is None: ymax = self.imageList.bounds.getHi(self.yax)

        log.debug('Required display bounds: X: ({}, {}) Y: ({}, {})'.format(
            xmin, xmax, ymin, ymax))

        canvasWidth, canvasHeight = self._getSize()
        dispWidth                 = float(xmax - xmin)
        dispHeight                = float(ymax - ymin)

        if canvasWidth  == 0 or \
           canvasHeight == 0 or \
           dispWidth    == 0 or \
           dispHeight   == 0:
            self.displayBounds[:] = [xmin, xmax, ymin, ymax]
            return

        # These ratios are used to determine whether
        # we need to expand the display range to
        # preserve the image aspect ratio.
        dispRatio   =       dispWidth    / dispHeight
        canvasRatio = float(canvasWidth) / canvasHeight

        # the canvas is too wide - we need
        # to expand the display width, thus 
        # effectively shrinking the display
        # along the horizontal axis
        if canvasRatio > dispRatio:
            newDispWidth = canvasWidth * (dispHeight / canvasHeight)
            xmin         = xmin - 0.5 * (newDispWidth - dispWidth)
            xmax         = xmax + 0.5 * (newDispWidth - dispWidth)

        # the canvas is too high - we need
        # to expand the display height
        elif canvasRatio < dispRatio:
            newDispHeight = canvasHeight * (dispWidth / canvasWidth)
            ymin          = ymin - 0.5 * (newDispHeight - dispHeight)
            ymax          = ymax + 0.5 * (newDispHeight - dispHeight)

        self.displayBounds.setLimits(0, xmin, xmax)
        self.displayBounds.setLimits(1, ymin, ymax) 

        xmin, xmax, ymin, ymax = self._applyZoom(xmin, xmax, ymin, ymax)

        log.debug('Final display bounds: X: ({}, {}) Y: ({}, {})'.format(
            xmin, xmax, ymin, ymax))

        self.displayBounds[:] = (xmin, xmax, ymin, ymax)

        
    def _setViewport(self,
                     xmin=None,
                     xmax=None,
                     ymin=None,
                     ymax=None,
                     zmin=None,
                     zmax=None):
        """Sets up the GL canvas size, viewport, and projection.

        If any of the min/max parameters are not provided, they are
        taken from the :attr:`displayBounds` (x/y), and the image
        list :attr:`~fsl.data.image.ImageList.bounds` (z).

        :arg xmin: Minimum x (horizontal) location
        :arg xmax: Maximum x location
        :arg ymin: Minimum y (vertical) location
        :arg ymax: Maximum y location
        :arg zmin: Minimum z (depth) location
        :arg zmax: Maximum z location
        """
        
        if xmin is None: xmin = self.displayBounds.xlo
        if xmax is None: xmax = self.displayBounds.xhi
        if ymin is None: ymin = self.displayBounds.ylo
        if ymax is None: ymax = self.displayBounds.yhi
        if zmin is None: zmin = self.imageList.bounds.getLo(self.zax)
        if zmax is None: zmax = self.imageList.bounds.getHi(self.zax)

        # If there are no images to be displayed,
        # or no space to draw, do nothing
        width, height = self._getSize()
        
        if (len(self.imageList) == 0) or \
           (width  == 0)              or \
           (height == 0)              or \
           (xmin   == xmax)           or \
           (ymin   == ymax):
            return

        log.debug('Setting canvas bounds: '
                  'X {: 5.1f} - {: 5.1f},'
                  'Y {: 5.1f} - {: 5.1f}'.format(xmin, xmax, ymin, ymax))

        # set up 2D orthographic drawing
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(xmin,        xmax,
                   ymin,        ymax,
                   zmin - 1000, zmax + 1000)
        # I don't know why the above +/-1000 is necessary :(
        # The '1000' is empirically arbitrary, but it seems
        # that I need to extend the depth clipping range
        # beyond the range of the data. This is despite the
        # fact that below, I'm actually translating the
        # displayed slice to Z=0! I don't understand OpenGL
        # sometimes. Most of the time.

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
        trans[self.zax] = -self.pos.z
        gl.glTranslatef(*trans)
