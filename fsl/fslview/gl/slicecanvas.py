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

See also the :class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas`.
"""

import logging
log = logging.getLogger(__name__)

import numpy                  as np 
import OpenGL.GL              as gl

import props

import fsl.data.image             as fslimage
import fsl.fslview.gl.globject    as globject
import fsl.fslview.gl.textures    as textures
import fsl.fslview.gl.annotations as annotations


class SliceCanvas(props.HasProperties):
    """Represens a canvas which may be used to display a single 2D slice from a
    collection of 3D images (see :class:`fsl.data.image.ImageList`).
    """

    pos = props.Point(ndims=3)
    """The currently displayed position. The ``pos.x`` and ``pos.y`` positions
    denote the position of a 'cursor', which is highlighted with green
    crosshairs. The ``pos.z`` position specifies the currently displayed
    slice. While the values of this point are in the display coordinate
    system, the dimension ordering may not be the same as the display
    coordinate dimension ordering. For this position, the x and y dimensions
    correspond to horizontal and vertical on the screen, and the z dimension
    to 'depth'.
    """

    zoom = props.Percentage(minval=100.0,
                            maxval=1000.0,
                            default=100.0,
                            clamped=True)
    """The image bounds are divided by this zoom
    factor to produce the display bounds.
    """

    
    displayBounds = props.Bounds(ndims=2)
    """The display bound x/y values specify the horizontal/vertical display
    range of the canvas, in display coordinates. This may be a larger area
    than the size of the displayed images, as it is adjusted to preserve the
    aspect ratio.
    """

    
    twoStageRender = props.Boolean(default=False)
    """If ``True``, the scene is rendered off-screen to a fixed-size texture;
    this texture is then rendered to the canvas. If ``False``, the scene is
    rendered directly to the canvas. Two-stage rendering will probably give
    better performance on old graphics cards, and when software-based
    rendering is being used.
    """

    
    showCursor = props.Boolean(default=True)
    """If ``False``, the green crosshairs which show
    the current cursor location will not be drawn.
    """
 

    zax = props.Choice((0, 1, 2), ('X axis', 'Y axis', 'Z axis'))
    """The image axis to be used as the screen 'depth' axis."""

    
    invertX = props.Boolean(default=False)
    """If True, the display is inverted along the X (horizontal screen) axis.
    """

    
    invertY = props.Boolean(default=False)
    """If True, the display is inverted along the Y (vertical screen) axis.
    """ 

    
    _labels = {
        'zoom'       : 'Zoom level',
        'showCursor' : 'Show cursor',
        'zax'        : 'Z axis',
        'invertX'    : 'Invert X axis',
        'invertY'    : 'Invert Y axis'}
    """Labels for the properties which are intended to be user editable."""

    
    _tooltips = {
        'zoom'       : 'Zoom level (min: 1, max: 10)',
        'showCursor' : 'Show/hide a green cursor indicating '
                       'the currently displayed location',
        'zax'        : 'Image axis which is used as the \'depth\' axis'}
    """Property descriptions to be used as help text."""

    
    _propHelp = _tooltips


    def calcPixelDims(self):
        """Calculate and return the approximate size (width, height) of one
        pixel in display space.
        """
        
        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)
        
        w, h = self._getSize()
        pixx = (xmax - xmin) / float(w)
        pixy = (ymax - ymin) / float(h) 

        return pixx, pixy

    
    def canvasToWorld(self, xpos, ypos):
        """Given pixel x/y coordinates on this canvas, translates them
        into xyz display coordinates.
        """

        realWidth                 = self.displayBounds.xlen
        realHeight                = self.displayBounds.ylen
        canvasWidth, canvasHeight = map(float, self._getSize())
            
        if self.invertX: xpos = canvasWidth  - xpos
        if self.invertY: ypos = canvasHeight - ypos

        if realWidth    == 0 or \
           canvasWidth  == 0 or \
           realHeight   == 0 or \
           canvasHeight == 0:
            return None
        
        xpos = self.displayBounds.xlo + (xpos / canvasWidth)  * realWidth
        ypos = self.displayBounds.ylo + (ypos / canvasHeight) * realHeight

        pos = [None] * 3
        pos[self.xax] = xpos
        pos[self.yax] = ypos
        pos[self.zax] = self.pos.z

        return pos


    def panDisplayBy(self, xoff, yoff):
        """Pans the canvas display by the given x/y offsets (specified in
        display coordinates).
        """

        if len(self.imageList) == 0: return
        
        dispBounds = self.displayBounds
        imgBounds  = self.displayCtx.bounds

        xmin, xmax, ymin, ymax = self.displayBounds[:]

        xmin = xmin + xoff
        xmax = xmax + xoff
        ymin = ymin + yoff
        ymax = ymax + yoff

        if dispBounds.xlen > imgBounds.getLen(self.xax):
            xmin = dispBounds.xlo
            xmax = dispBounds.xhi
            
        elif xmin < imgBounds.getLo(self.xax):
            xmin = imgBounds.getLo(self.xax)
            xmax = xmin + self.displayBounds.getLen(0)
            
        elif xmax > imgBounds.getHi(self.xax):
            xmax = imgBounds.getHi(self.xax)
            xmin = xmax - self.displayBounds.getLen(0)
            
        if dispBounds.ylen > imgBounds.getLen(self.yax):
            ymin = dispBounds.ylo
            ymax = dispBounds.yhi
            
        elif ymin < imgBounds.getLo(self.yax):
            ymin = imgBounds.getLo(self.yax)
            ymax = ymin + self.displayBounds.getLen(1)

        elif ymax > imgBounds.getHi(self.yax):
            ymax = imgBounds.getHi(self.yax)
            ymin = ymax - self.displayBounds.getLen(1)

        self.displayBounds[:] = [xmin, xmax, ymin, ymax]


    def centreDisplayAt(self, xpos, ypos):
        """Pans the display so the given x/y position is in the centre.
        """

        # work out current display centre
        bounds  = self.displayBounds
        xcentre = bounds.xlo + (bounds.xhi - bounds.xlo) * 0.5
        ycentre = bounds.ylo + (bounds.yhi - bounds.ylo) * 0.5

        # move to the new centre
        self.panDisplayBy(xpos - xcentre, ypos - ycentre)


    def panDisplayToShow(self, xpos, ypos):
        """Pans the display so that the given x/y position (in display
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


    def getAnnotations(self):
        """Returns a :class:`~fsl.fslview.gl.annotations.Annotations`
        instance, which can be used to annotate the canvas. 
        """
        return self._annotations

        
    def __init__(self, imageList, displayCtx, zax=0):
        """Creates a canvas object. 

        .. note:: It is assumed that each :class:`~fsl.data.image.Image`
        contained in the ``imageList`` has an attribute called ``display``,
        which refers to an :class:`~fsl.fslview.displaycontext.ImageDisplay`
        instance defining how that image is to be displayed.
        
        :arg imageList:   An :class:`~fsl.data.image.ImageList` object.
        
        :arg displayCtx:  A :class:`~fsl.fslview.displaycontext.DisplayContext`
                          object.
        
        :arg zax:        Image axis perpendicular to the plane to be displayed
                         (the 'depth' axis), default 0.
        """

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.image.ImageList instance')

        props.HasProperties.__init__(self)

        self.imageList      = imageList
        self.displayCtx     = displayCtx
        self.name           = '{}_{}'.format(self.__class__.__name__, id(self))


        # A GLObject instance is created for
        # every image in the image list, and
        # stored in this dictionary
        self._glObjects = {}

        # If two stage rendering is enabled, this
        # attribute will contain a RenderTexture
        # instance for each image in the image list
        self._renderTextures = {}

        # The zax property is the image axis which maps to the
        # 'depth' axis of this canvas. The _zAxisChanged method
        # also fixes the values of 'xax' and 'yax'.
        self.zax = zax
        self.xax = (zax + 1) % 3
        self.yax = (zax + 2) % 3

        self._annotations = annotations.Annotations(self.xax, self.yax)
        self._zAxisChanged() 

        # when any of the properties of this
        # canvas change, we need to redraw
        self.addListener('zax',           self.name, self._zAxisChanged)
        self.addListener('pos',           self.name, self._draw)
        self.addListener('displayBounds', self.name, self._draw)
        self.addListener('showCursor',    self.name, self._refresh)
        self.addListener('invertX',       self.name, self._refresh)
        self.addListener('invertY',       self.name, self._refresh)
        self.addListener('zoom',
                         self.name,
                         lambda *a: self._updateDisplayBounds())

        # When the two stage rendering option changes,
        # make sure that, if it has been enabled, a
        # rendering texture exists for every image
        # in the list
        self.addListener('twoStageRender',
                         self.name,
                         self._onTwoStageRenderChange)
        
        # When the image list changes, refresh the
        # display, and update the display bounds
        self.imageList.addListener( 'images',
                                    self.name,
                                    self._imageListChanged)
        self.displayCtx.addListener('imageOrder',
                                    self.name,
                                    self._imageListChanged) 
        self.displayCtx.addListener('bounds',
                                    self.name,
                                    self._imageBoundsChanged)


    def _initGL(self):
        # Call the _imageListChanged method - it  will generate
        # any necessary GL data for each of the images
        self._imageListChanged()


    def _onTwoStageRenderChange(
            self,
            value=None,
            valid=None,
            ctx=None,
            name=None,
            recreate=False):
        """Called when the :attr:`twoStageRender` property changes.
        """

        needRefresh = False

        # If two stage rendering has been disabled, or
        # the caller wants all render textures to be
        # recreated, destroy all existing textures
        if recreate or not self.twoStageRender:

            for image, texture in self._renderTextures.items():
                self._renderTextures.pop(image)
                texture.destroy()
                needRefresh = True

        if self.twoStageRender:

            # If any images have been removed from the image
            # list, destroy the associated render texture
            for image, texture in self._renderTextures.items():
                if image not in self.imageList:
                    self._renderTextures.pop(image)
                    texture.destroy()
                    needRefresh = True

            # If any images have been added to the list,
            # create a new render textures for them
            for image in self.imageList:

                if image in self._renderTextures:
                    continue

                display = self.displayCtx.getDisplayProperties(image)
                name    = '{}_{}_{}'.format(image.name, self.xax, self.yax)
                rt      = textures.ImageRenderTexture(
                    name, image, display, self.xax, self.yax)
                
                self._renderTextures[image] = rt
                
                needRefresh = True

        if needRefresh:
            self._refresh()


    def _zAxisChanged(self, *a):
        """Called when the :attr:`zax` property is changed. Calculates
        the corresponding X and Y axes, and saves them as attributes of
        this object. Also regenerates the GL index buffers for every
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

        self._annotations.setAxes(self.xax, self.yax)

        for image, globj in self._glObjects.items():

            if globj is not None:
                globj.setAxes(self.xax, self.yax)

        self._imageBoundsChanged()

        # Reset the canvas position as, because the
        # z axis has been changed, the old coordinates
        # will be in the wrong dimension order
        self.pos.xyz = [pos[self.xax],
                        pos[self.yax],
                        pos[self.zax]]

        # If two stage rendering is enabled, the
        # render textures need to be updated, as
        # they are configured in terms of the
        # display axes
        self._onTwoStageRenderChange(recreate=True)
 
            
    def _imageListChanged(self, *a):
        """This method is called every time an image is added or removed
        to/from the image list. For newly added images, it creates the
        appropriate :mod:`~fsl.fslview.gl.globject` type, which
        initialises the OpenGL data necessary to render the image, and then
        triggers a refresh.
        """

        # Destroy any GL objects for images 
        # which are no longer in the list
        for image, globj in self._glObjects.items():
            if image not in self.imageList:
                self._glObjects.pop(image)
                if globj is not None:
                    globj.destroy()

        # Create a GL object for any new images,
        # and attach a listener to their display
        # properties so we know when to refresh
        # the canvas.
        for image in self.imageList:

            # A GLObject already exists for this image
            if image in self._glObjects:
                continue

            display = self.displayCtx.getDisplayProperties(image)

            # Called when the GL object representation
            # of the image needs to be re-created
            def genGLObject(value=None,
                            valid=None,
                            ctx=None,
                            name=None,
                            disp=display,
                            img=image):

                log.debug('GLObject representation for {} '
                          'changed to {}'.format(disp.name,
                                                 disp.imageType))

                if not self._setGLContext():
                    return

                # Tell the previous GLObject (if
                # any) to clean up after itself
                globj = self._glObjects.get(img, None)
                if globj is not None:
                    globj.destroy()

                globj = globject.createGLObject(img, disp)
                self._glObjects[img] = globj

                if globj is not None:
                    globj.init()
                    globj.setAxes(self.xax, self.yax)

                opts = disp.getDisplayOpts()
                opts.addGlobalListener(self.name, self._refresh)
                self._refresh()
                
            genGLObject()
                
            image  .addListener('data',          self.name, self._refresh)
            display.addListener('imageType',     self.name, genGLObject)
            display.addListener('enabled',       self.name, self._refresh)
            display.addListener('transform',     self.name, self._refresh)
            display.addListener('interpolation', self.name, self._refresh)
            display.addListener('alpha',         self.name, self._refresh)
            display.addListener('brightness',    self.name, self._refresh)
            display.addListener('contrast',      self.name, self._refresh)
            display.addListener('resolution',    self.name, self._refresh)
            display.addListener('volume',        self.name, self._refresh)

        self._onTwoStageRenderChange()
        self._refresh()


    def _imageBoundsChanged(self, *a):
        """Called when the display bounds are changed.

        Updates the constraints on the :attr:`pos` property so it is
        limited to stay within a valid range, and then calls the
        :meth:`_updateDisplayBounds` method.
        """

        imgBounds = self.displayCtx.bounds

        self.pos.setMin(0, imgBounds.getLo(self.xax))
        self.pos.setMax(0, imgBounds.getHi(self.xax))
        self.pos.setMin(1, imgBounds.getLo(self.yax))
        self.pos.setMax(1, imgBounds.getHi(self.yax))
        self.pos.setMin(2, imgBounds.getLo(self.zax))
        self.pos.setMax(2, imgBounds.getHi(self.zax))

        self._updateDisplayBounds()
        

    def _applyZoom(self, xmin, xmax, ymin, ymax):
        """'Zooms' in to the given rectangle according to the
        current value of the zoom property, keeping the view
        centre consistent with respect to the current value
        of the :attr:`displayBounds` property. Returns a
        4-tuple containing the updated bound values.
        """

        if self.zoom == 100.0:
            return (xmin, xmax, ymin, ymax)

        bounds     = self.displayBounds
        zoomFactor = 100.0 / self.zoom

        xlen    = xmax - xmin
        ylen    = ymax - ymin
        newxlen = xlen * zoomFactor
        newylen = ylen * zoomFactor
 
        # centre the zoomed-in rectangle on
        # the current displayBounds centre
        xmid = bounds.xlo + 0.5 * bounds.xlen
        ymid = bounds.ylo + 0.5 * bounds.ylen

        # new x/y min/max bounds
        xmin = xmid - 0.5 * newxlen
        xmax = xmid + 0.5 * newxlen
        ymin = ymid - 0.5 * newylen
        ymax = ymid + 0.5 * newylen

        xlen = xmax - xmin
        ylen = ymax - ymin

        # clamp x/y min/max values to the
        # displayBounds constraints
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

        if xmin is None: xmin = self.displayCtx.bounds.getLo(self.xax)
        if xmax is None: xmax = self.displayCtx.bounds.getHi(self.xax)
        if ymin is None: ymin = self.displayCtx.bounds.getLo(self.yax)
        if ymax is None: ymax = self.displayCtx.bounds.getHi(self.yax)

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
                     zmax=None,
                     size=None):
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
        if zmin is None: zmin = self.displayCtx.bounds.getLo(self.zax)
        if zmax is None: zmax = self.displayCtx.bounds.getHi(self.zax)

        # If there are no images to be displayed,
        # or no space to draw, do nothing
        if size is None:
            size = self._getSize()
            
        width, height = size

        # clear the canvas
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)        
        
        if (len(self.imageList) == 0) or \
           (width  == 0)              or \
           (height == 0)              or \
           (xmin   == xmax)           or \
           (ymin   == ymax):
            return

        log.debug('Setting canvas bounds (size {}, {}): '
                  'X {: 5.1f} - {: 5.1f},'
                  'Y {: 5.1f} - {: 5.1f}'.format(
                      width, height, xmin, xmax, ymin, ymax))

        # set up 2D orthographic drawing
        gl.glViewport(0, 0, width, height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()

        # Flip the viewport if necessary
        if self.invertX: xmin, xmax = xmax, xmin
        if self.invertY: ymin, ymax = ymax, ymin
        
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

        
    def _drawCursor(self):
        """Draws a green cursor at the current X/Y position."""
        
        # A vertical line at xpos, and a horizontal line at ypos
        xverts = np.zeros((2, 2))
        yverts = np.zeros((2, 2))

        xmin, xmax = self.displayCtx.bounds.getRange(self.xax)
        ymin, ymax = self.displayCtx.bounds.getRange(self.yax)

        x = self.pos.x
        y = self.pos.y

        # How big is one pixel in world space?
        pixx, pixy = self.calcPixelDims()

        # add a little padding to the lines if they are 
        # on the boundary, so they don't get cropped        
        if x <= xmin: x = xmin + 0.5 * pixx
        if x >= xmax: x = xmax - 0.5 * pixx
        if y <= ymin: y = ymin + 0.5 * pixy
        if y >= ymax: y = ymax - 0.5 * pixy

        xverts[:, 0] = x
        xverts[:, 1] = [ymin, ymax]
        yverts[:, 0] = [xmin, xmax]
        yverts[:, 1] = y 
        
        self._annotations.line(xverts[0], xverts[1], colour=(0, 1, 0))
        self._annotations.line(yverts[0], yverts[1], colour=(0, 1, 0))


    def _drawRenderTextures(self):
        """
        """
        log.debug('Combining off-screen image textures, and rendering '
                  'to canvas (size {})'.format(self._getSize()))

        self._setViewport()

        for image in self.displayCtx.getOrderedImages():
            renderTexture = self._renderTextures.get(image, None)
            display       = self.displayCtx.getDisplayProperties(image)
            lo, hi        = display.getDisplayBounds()

            if renderTexture is None or not display.enabled:
                continue

            xmin, xmax = lo[self.xax], hi[self.xax]
            ymin, ymax = lo[self.yax], hi[self.yax]

            log.debug('Drawing image {} texture to {:0.3f}-{:0.3f}, '
                      '{:0.3f}-{:0.3f}'.format(
                          image, xmin, xmax, ymin, ymax))

            renderTexture.drawOnBounds(
                xmin, xmax, ymin, ymax, self.xax, self.yax) 


    def _draw(self, *a):
        """Draws the current scene to the canvas. """
        
        width, height = self._getSize()
        if width == 0 or height == 0:
            return

        if not self._setGLContext():
            return

        # If normal rendering, set the viewport to match
        # the current display bounds and canvas size
        if not self.twoStageRender:
            self._setViewport()

        for image in self.displayCtx.getOrderedImages():

            display = self.displayCtx.getDisplayProperties(image)
            globj   = self._glObjects.get(image, None)
            
            if (globj is None) or (not display.enabled):
                continue

            # Two-stage rendering - each image is
            # rendered to an off-screen texture -
            # these textures are combined below.
            # Set up this texture as the rendering
            # target
            if self.twoStageRender:
                renderTexture = self._renderTextures.get(image, None)
                lo, hi        = display.getDisplayBounds()

                # Assume that all is well - the texture
                # just has not yet been created
                if renderTexture is None:
                    return

                renderTexture.bindAsRenderTarget()

                self._setViewport(
                    xmin=lo[self.xax],
                    xmax=hi[self.xax],
                    ymin=lo[self.yax],
                    ymax=hi[self.yax],
                    size=renderTexture.getSize())
                
            log.debug('Drawing {} slice for image {}'.format(
                self.zax, image.name))
                
            globj.preDraw()
            globj.draw(self.pos.z)
            globj.postDraw()

            if self.twoStageRender:
                textures.ImageRenderTexture.unbindAsRenderTarget()

        if self.twoStageRender:
            self._drawRenderTextures()

        if self.showCursor:
            self._drawCursor()

        self._annotations.draw(self.pos.z)

        self._postDraw()
