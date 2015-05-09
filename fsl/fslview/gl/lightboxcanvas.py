#!/usr/bin/env python
#
# lightboxcanvas.py - A SliceCanvas which displays multiple slices along a
# single axis from a collection of 3D images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""A :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas` which displays multiple
slices along a single axis from a collection of 3D images.
"""

import sys
import logging

import numpy     as np
import OpenGL.GL as gl

import props

import fsl.fslview.gl.slicecanvas as slicecanvas
import fsl.fslview.gl.textures    as textures


log = logging.getLogger(__name__)


class LightBoxCanvas(slicecanvas.SliceCanvas):
    """Represents an OpenGL canvas which displays multiple slices from a
    collection of 3D images (see :class:`fsl.data.image.ImageList`). The
    slices are laid out on the same canvas along rows and columns, with the
    slice at the minimum Z position translated to the top left of the canvas,
    and the slice with the maximum Z value translated to the bottom right.
    """

    
    sliceSpacing = props.Real(clamped=True,
                              minval=0.1,
                              maxval=30.0,
                              default=1.0)
    """This property controls the spacing
    between slices (in real world coordinates).
    """

    
    ncols = props.Int(clamped=True, minval=1, maxval=100, default=5)
    """This property controls the number of 
    slices to be displayed on a single row.
    """

    
    nrows = props.Int(clamped=True, minval=1, maxval=100, default=4)
    """This property controls the number of 
    rows to be displayed on the canvas.
    """ 

    
    topRow = props.Int(clamped=True, minval=0, maxval=20, default=0)
    """This property controls the (0-indexed) row
    to be displayed at the top of the canvas, thus
    providing the ability to scroll through the
    slices.
    """

    
    zrange = props.Bounds(ndims=1)
    """This property controls the range, in world
    coordinates, of the slices to be displayed.
    """


    showGridLines = props.Boolean(default=False)
    """If True, grid lines are drawn between the displayed slices. """


    highlightSlice = props.Boolean(default=False)
    """If True, a box will be drawn around the slice containing the current
    location.
    """
    
    
    def worldToCanvas(self, xpos, ypos, zpos):
        """Given an x/y/z location in the image list world (with xpos
        corresponding to the horizontal screen axis, ypos to the vertical
        axis, and zpos to the depth axis), converts it into an x/y position,
        in world coordinates, on the canvas.
        """
        sliceno = int(np.floor((zpos - self.zrange.xlo) / self.sliceSpacing))

        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)
        
        row = self._totalRows - int(np.floor(sliceno / self.ncols)) - 1
        col =                   int(np.floor(sliceno % self.ncols))

        xpos = xpos + xlen * col
        ypos = ypos + ylen * row
        
        return xpos, ypos

        
    def canvasToWorld(self, xpos, ypos):
        """Overrides
        :meth:`fsl.fslview.gl.slicecanvas.SliceCanvas.canvasToWorld`.

        Given pixel x/y coordinates on this canvas, translates them into the
        real world x/y/z coordinates of the displayed slice.  Returns a
        3-tuple containing the (x, y, z) display system coordinates. If the
        given canvas position is out of the image range, ``None`` is returned.
        """

        nrows = self._totalRows
        ncols = self.ncols

        screenPos = slicecanvas.SliceCanvas.canvasToWorld(
            self, xpos, ypos)

        if screenPos is None:
            return None

        screenx = screenPos[self.xax]
        screeny = screenPos[self.yax]

        xmin = self.displayCtx.bounds.getLo( self.xax)
        ymin = self.displayCtx.bounds.getLo( self.yax)
        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)

        xmax = xmin + ncols * xlen
        ymax = ymin + nrows * ylen

        col     =         int(np.floor((screenx - xmin) / xlen))
        row     = nrows - int(np.floor((screeny - ymin) / ylen)) - 1
        sliceno = row * ncols + col

        if screenx <  xmin or \
           screenx >  xmax or \
           screeny <  ymin or \
           screeny >  ymax or \
           sliceno <  0    or \
           sliceno >= self._nslices:
            return None

        xpos = screenx -          col      * xlen
        ypos = screeny - (nrows - row - 1) * ylen
        zpos = self.zrange.xlo + (sliceno + 0.5) * self.sliceSpacing

        pos = [0, 0, 0]
        pos[self.xax] = xpos
        pos[self.yax] = ypos
        pos[self.zax] = zpos

        return tuple(pos)

        
    def getTotalRows(self):
        """Returns the total number of rows that may be displayed.
        """
        return self._totalRows

        
    def __init__(self, imageList, displayCtx, zax=0):
        """Create a :class:`LightBoxCanvas` object.
        
        :arg imageList:  a :class:`~fsl.data.image.ImageList` object which
                         contains, or will contain, a list of images to be
                         displayed.

        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         object which defines how that image list is to be
                         displayed.
        
        :arg zax:        Image axis to be used as the 'depth' axis. Can be
                         changed via the :attr:`LightBoxCanvas.zax` property.
        """

        # These attributes are used to keep track of
        # the total number of slices to be displayed,
        # and the total number of rows to be displayed
        self._nslices   = 0
        self._totalRows = 0

        slicecanvas.SliceCanvas.__init__(self, imageList, displayCtx, zax)

        # This will point to a RenderTexture if
        # the offscreen render mode is enabled
        self.__offscreenRenderTexture = None

        # default to showing the entire slice range
        zmin, zmax = displayCtx.bounds.getRange(self.zax)
        self.zrange.xmin = zmin
        self.zrange.xmax = zmax
        self.zrange.x    = zmin, zmax

        self._slicePropsChanged()

        self.addListener('sliceSpacing',   self.name, self._slicePropsChanged)
        self.addListener('ncols',          self.name, self._slicePropsChanged)
        self.addListener('nrows',          self.name, self._slicePropsChanged)
        self.addListener('zrange',         self.name, self._slicePropsChanged)
        self.addListener('showGridLines',  self.name, self._refresh)
        self.addListener('highlightSlice', self.name, self._refresh)

        # Called when the top row changes -
        # adjusts display range and refreshes
        def rowChange(*a):
            self._updateDisplayBounds()
            self._refresh()

        self.addListener('topRow', self.name, rowChange)

        # Add a listener to the position so when it
        # changes we can adjust the display range (via
        # the topRow property) to ensure the slice
        # corresponding to the current z position is
        # visible. SliceCanvas.__init__ has already
        # registered a listener, on pos, with
        # self.name - so we use a different name
        # here
        self.addListener('pos',
                         '{}_zPosChanged'.format(self.name),
                         self._zPosChanged)


    def _slicePropsChanged(self, *a):
        """Called when any of the slice properties change. Regenerates slice
        locations and display bounds, and redraws
        """
        
        self._calcNumSlices()
        self._genSliceLocations()
        self._zPosChanged()
        self._updateDisplayBounds()
        self._refresh()


    def _renderModeChange(self, *a):
        """Overrides :meth:`.SliceCanvas._renderModeChange`.
        """
        
        if self.__offscreenRenderTexture is not None:
            self.__offscreenRenderTexture.destroy()
            self.__offscreenRenderTexture = None
            
        slicecanvas.SliceCanvas._renderModeChange(self, *a)


    def _updateRenderTextures(self):
        """Overrides :meth:`.SliceCanvas._updateRenderTextures`.
        """

        if self.renderMode == 'onscreen':
            return

        # The LightBoxCanvas does offscreen rendering
        # a bit different to the SliceCanvas. The latter
        # uses a separate render texture for each image,
        # whereas here we're going to use a single
        # render texture for all images. 
        elif self.renderMode == 'offscreen':
            if self.__offscreenRenderTexture is not None:
                self.__offscreenRenderTexture.destroy()

            self.__offscreenRenderTexture = textures.RenderTexture(
                '{}_{}'.format(type(self).__name__, id(self)),
                gl.GL_LINEAR)

            self.__offscreenRenderTexture.setSize(768, 768)

        # The LightBoxCanvas handles re-render mode
        # the same way as the SliceCanvas - a separate
        # RenderTextureStack for eacn globject
        elif self.renderMode == 'prerender':
            
            # Delete any RenderTextureStack instances for
            # images which have been removed from the list
            for image, tex in self._renderTextures.items():
                if image not in self.imageList:
                    self._renderTextures.pop(image)
                    tex.destroy()

            # Create a RendeTextureStack for images
            # which have been added to the list
            for image in self.imageList:
                if image in self._renderTextures:
                    continue

                globj = self._glObjects.get(image, None)
                
                if globj is None:
                    continue

                rt = textures.RenderTextureStack(globj)
                rt.setAxes(self.xax, self.yax)

                self._renderTextures[image] = rt

        self._refresh()


    def _calcNumSlices(self, *a):
        """Calculates the total number of slices to be displayed and
        the total number of rows.
        """
        
        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)
        zlen = self.zrange.xlen
        width, height = self._getSize()

        if xlen   == 0 or \
           ylen   == 0 or \
           width  == 0 or \
           height == 0:
            return

        self._nslices   = int(np.floor(zlen / self.sliceSpacing))
        self._totalRows = int(np.ceil(self._nslices / float(self.ncols)))

        if self._nslices == 0 or self._totalRows == 0:
            return
        
        # All slices are going to be displayed, so
        # we'll 'disable' the topRow property
        if self._totalRows < self.nrows:
            self.setConstraint('topRow', 'minval', 0)
            self.setConstraint('topRow', 'maxval', 0)

        # nrows slices are going to be displayed,
        # and the topRow property can be used to
        # scroll through all available rows.
        else:
            self.setConstraint('topRow',
                               'maxval',
                               self._totalRows - self.nrows)


    def _zPosChanged(self, *a):
        """Called when the :attr:`~fsl.fslview.gl.slicecanvas.SliceCanvas.pos`
        ``z`` value changes.

        Makes sure that the corresponding slice is visible.
        """
        # figure out where we are in the canvas world
        canvasX, canvasY = self.worldToCanvas(*self.pos.xyz)

        # See the _updateDisplayBounds method for an
        # explanation of the _realBounds attribute
        xlo, xhi, ylo, yhi = self._realBounds

        # already in bounds
        if canvasX >= xlo and \
           canvasX <= xhi and \
           canvasY >= ylo and \
           canvasY <= yhi:
            return

        # figure out what row we're on
        sliceno = int(np.floor((self.pos.z - self.zrange.xlo) /
                                self.sliceSpacing))
        row     = int(np.floor(sliceno / self.ncols))

        # and make sure that row is visible
        self.topRow = row


    def _imageListChanged(self, *a):
        """Overrides
        :meth:`~fsl.fslview.gl.slicecanvas.SliceCanvas._imageListChanged`.

        Regenerates slice locations for all images, and calls the super
        implementation.
        """
        self._updateZAxisProperties()
        self._genSliceLocations()
        slicecanvas.SliceCanvas._imageListChanged(self, *a)


    def _updateZAxisProperties(self):
        """Called by the :meth:`_imageBoundsChanged` method.

        The purpose of this method is to set the slice spacing and displayed Z
        range to something sensible when the Z axis, or Z image bounds are
        changed (e.g. due to images being added/removed, or to image
        transformation matrices being changed).

        """

        if len(self.imageList) == 0:
            self.setConstraint('zrange', 'minDistance', 0)
            self.zrange.x     = (0, 0)
            self.sliceSpacing = 0
        else:

            # Pick a sensible default for the
            # slice spacing - the smallest pixdim
            # across all images in the list 
            newZGap = sys.float_info.max

            for image in self.imageList:
                display = self.displayCtx.getDisplayProperties(image)

                # TODO this is specific to the Image type,
                # and shouldn't be. We're going to need to
                # support other overlay types soon...
                if   display.transform == 'id':
                    zgap = 1
                elif display.transform == 'pixdim':
                    zgap = image.pixdim[self.zax]
                else:
                    zgap = min(image.pixdim[:3])

                if zgap < newZGap:
                    newZGap = zgap

            newZRange = self.displayCtx.bounds.getRange(self.zax)

            # Changing the zrange/sliceSpacing properties will, in most cases,
            # trigger a call to _slicePropsChanged. But for images which have
            # the same range across more than one dimension, the call might not
            # happen. So we do a check and, if the dimension ranges are the
            # same,  manually call _slicePropsChanged.  Bringing out the ugly
            # side of event driven programming.
            self.zrange.setLimits(0, *newZRange)
            self.setConstraint('zrange',       'minDistance', newZGap)
            self.setConstraint('sliceSpacing', 'minval',      newZGap)


    def _imageBoundsChanged(self, *a):
        """Overrides
        :meth:`fsl.fslview.gl.slicecanvas.SliceCanvas._imageBoundsChanged`.

        Called when the image bounds change. Updates the :attr:`zrange`
        min/max values.
        """

        slicecanvas.SliceCanvas._imageBoundsChanged(self)

        self._updateZAxisProperties()
        self._calcNumSlices()
        self._genSliceLocations()
        
        
    def _updateDisplayBounds(self):
        """Overrides
        :meth:`fsl.fslview.gl.slicecanvas.SliceCanvas._updateDisplayBounds`.

        Called on canvas resizes, image bound changes and lightbox slice
        property changes. Calculates the required bounding box that is to
        be displayed, in real world coordinates.
        """

        xmin = self.displayCtx.bounds.getLo( self.xax)
        ymin = self.displayCtx.bounds.getLo( self.yax)
        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)


        # Calculate the vertical offset required to
        # ensure that the current 'topRow' is the first
        # row, and the correct number of rows ('nrows')
        # are displayed
        
        # if the number of rows to be displayed (nrows)
        # is more than the number of rows that exist
        # (totalRows), calculate an offset to vertically
        # centre the existing row space in the display
        # row space
        if self._totalRows < self.nrows:
            off  = (self._totalRows - self.nrows) / 2.0

        # otherwise calculate the offset so that the
        # top of the display space lines up with the
        # current topRow
        else:
            off  = self._totalRows - self.nrows - self.topRow

        ymin = ymin + ylen * off
        xmax = xmin + xlen * self.ncols
        ymax = ymin + ylen * self.nrows

        # The final display bounds calculated by
        # SliceCanvas._updateDisplayBounds is not
        # necessarily the same as the actual bounds,
        # as they are  adjusted to preserve  the
        # image aspect ratio. But the real bounds
        # are of use in the _zPosChanged method, so
        # we save them here as an attribute
        self._realBounds = (xmin, xmax, ymin, ymax)

        slicecanvas.SliceCanvas._updateDisplayBounds(
            self, xmin, xmax, ymin, ymax)


    def _genSliceLocations(self):
        """Called when any of the slice display properties change.

        For every image in the image list, generates a list of transformation
        matrices, and a list of slice indices. The latter specifies the slice
        indices from the image to be displayed, and the former specifies the
        transformation matrix to be used to position the slice on the canvas.
        """
        
        # calculate the locations, in real world coordinates,
        # of all slices to be displayed on the canvas
        sliceLocs = np.arange(
            self.zrange.xlo + self.sliceSpacing * 0.5,
            self.zrange.xhi,
            self.sliceSpacing)

        self._sliceLocs  = {}
        self._transforms = {}

        # calculate the transformation for each
        # slice in each image, and the index of
        # each slice to be displayed
        for i, image in enumerate(self.imageList):

            iSliceLocs  = []
            iTransforms = []
            
            for zi, zpos in enumerate(sliceLocs):

                xform = self._calculateSliceTransform(image, zi)

                iTransforms.append(xform)
                iSliceLocs .append(zpos)

            self._transforms[image] = iTransforms
            self._sliceLocs[ image] = iSliceLocs


    def _calculateSliceTransform(self, image, sliceno):
        """Calculates a transformation matrix for the given slice number
        (voxel index) in the given image.

        Each slice is displayed on the same canvas, but is translated to a
        specific row/column.  So translation matrix is created, to position
        the slice in the correct location on the canvas.
        """

        nrows = self._totalRows
        ncols = self.ncols

        row = int(np.floor(sliceno / ncols))
        col = int(np.floor(sliceno % ncols))

        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)

        translate              = np.identity(4, dtype=np.float32)
        translate[3, self.xax] = xlen * col
        translate[3, self.yax] = ylen * (nrows - row - 1)
        translate[3, self.zax] = 0
        
        return translate


    def _drawGridLines(self):
        """Draws grid lines between all the displayed slices."""

        xlen = self.displayCtx.bounds.getLen(self.xax)
        ylen = self.displayCtx.bounds.getLen(self.yax)
        xmin = self.displayCtx.bounds.getLo( self.xax)
        ymin = self.displayCtx.bounds.getLo( self.yax)

        rowLines = np.zeros(((self.nrows - 1) * 2, 2), dtype=np.float32)
        colLines = np.zeros(((self.ncols - 1) * 2, 2), dtype=np.float32)
        
        topRow = self._totalRows - self.topRow 
        btmRow = topRow          - self.nrows

        rowLines[:, 1] = np.arange(
            ymin + (btmRow + 1) * ylen,
            ymin +  topRow      * ylen, ylen).repeat(2)

        rowLines[:, 0] = np.tile(
            np.array([xmin, xmin + self.ncols * xlen]),
            self.nrows - 1)
        
        colLines[:, 0] = np.arange(
            xmin + xlen,
            xmin + xlen * self.ncols, xlen).repeat(2) 
        
        colLines[:, 1] = np.tile(np.array([
            ymin + btmRow * ylen,
            ymin + topRow * ylen]), self.ncols - 1)

        colour = (0.3, 0.9, 1.0, 0.8)

        for lines in (rowLines, colLines):
            for i in range(0, len(lines), 2):
                self.getAnnotations().line(lines[i],
                                           lines[i + 1],
                                           colour=colour,
                                           width=2)


        
    def _drawSliceHighlight(self):
        """Draws a box around the slice which contains the current cursor location.
        """
        
        sliceno = int(np.floor((self.pos.z - self.zrange.xlo) /
                               self.sliceSpacing))

        xlen    = self.displayCtx.bounds.getLen(self.xax)
        ylen    = self.displayCtx.bounds.getLen(self.yax)
        xmin    = self.displayCtx.bounds.getLo( self.xax)
        ymin    = self.displayCtx.bounds.getLo( self.yax) 
        row     = int(np.floor(sliceno / self.ncols))
        col     = int(np.floor(sliceno % self.ncols))

        # don't draw the cursor if it is on a
        # non-existent or non-displayed slice
        if sliceno >  self._nslices:            return
        if row     <  self.topRow:              return
        if row     >= self.topRow + self.nrows: return

        # in GL space, the top row is actually the bottom row
        row = self._totalRows - row - 1

        self.getAnnotations().rect((xmin + xlen * col,
                                    ymin + ylen * row),
                                   xlen,
                                   ylen,
                                   colour=(1, 0, 0),
                                   width=2)

        
    def _drawCursor(self):
        """Draws a cursor at the current canvas position (the
        :attr:`~fsl.fslview.gl.SliceCanvas.pos` property).
        """

        sliceno = int(np.floor((self.pos.z - self.zrange.xlo) /
                               self.sliceSpacing))
        xlen    = self.displayCtx.bounds.getLen(self.xax)
        ylen    = self.displayCtx.bounds.getLen(self.yax)
        xmin    = self.displayCtx.bounds.getLo( self.xax)
        ymin    = self.displayCtx.bounds.getLo( self.yax)
        row     = int(np.floor(sliceno / self.ncols))
        col     = int(np.floor(sliceno % self.ncols))

        # don't draw the cursor if it is on a
        # non-existent or non-displayed slice
        if sliceno >  self._nslices:            return
        if row     <  self.topRow:              return
        if row     >= self.topRow + self.nrows: return

        # in GL space, the top row is actually the bottom row
        row = self._totalRows - row - 1

        xpos, ypos = self.worldToCanvas(*self.pos.xyz)

        xverts = np.zeros((2, 2))
        yverts = np.zeros((2, 2)) 

        xverts[:, 0] = xpos
        xverts[0, 1] = ymin + (row)     * ylen
        xverts[1, 1] = ymin + (row + 1) * ylen

        yverts[:, 1] = ypos
        yverts[0, 0] = xmin + (col)     * xlen
        yverts[1, 0] = xmin + (col + 1) * xlen

        annot = self.getAnnotations()

        annot.line(xverts[0], xverts[1], colour=(0, 1, 0), width=1)
        annot.line(yverts[0], yverts[1], colour=(0, 1, 0), width=1)

        
    def _draw(self, *a):
        """
        """

        if not self._setGLContext():
            return

        if self.renderMode == 'offscreen':
            
            log.debug('Rendering to off-screen texture')

            rt = self.__offscreenRenderTexture
            
            lo = [None] * 3
            hi = [None] * 3
            
            lo[self.xax], hi[self.xax] = self.displayBounds.x
            lo[self.yax], hi[self.yax] = self.displayBounds.y
            lo[self.zax], hi[self.zax] = self.zrange
            
            rt.bindAsRenderTarget()
            rt.setRenderViewport(self.xax, self.yax, lo, hi)
            gl.glClear(gl.GL_COLOR_BUFFER_BIT)
            
        else:
            self._setViewport()

        startSlice = self.ncols * self.topRow
        endSlice   = startSlice + self.nrows * self.ncols

        if endSlice > self._nslices:
            endSlice = self._nslices    

        # Draw all the slices for all the images.
        for image in self.displayCtx.getOrderedImages():

            display = self.displayCtx.getDisplayProperties(image)

            globj = self._glObjects.get(image, None)

            if (globj is None) or (not display.enabled):
                continue

            log.debug('Drawing {} slices ({} - {}) for '
                      'image {} directly to canvas'.format(
                          endSlice - startSlice, startSlice, endSlice, image))

            zposes = self._sliceLocs[ image][startSlice:endSlice]
            xforms = self._transforms[image][startSlice:endSlice]

            if self.renderMode == 'prerender':
                rt = self._renderTextures.get(image, None)

                if rt is None:
                    continue
                
                log.debug('Drawing {} slices ({} - {}) for image {} '
                          'from pre-rendered texture'.format(
                              endSlice - startSlice,
                              startSlice,
                              endSlice,
                              image))
                
                for zpos, xform in zip(zposes, xforms):
                    rt.draw(zpos, xform)
            else:

                globj.preDraw()
                globj.drawAll(zposes, xforms)
                globj.postDraw()

        if self.renderMode == 'offscreen':
            rt.unbindAsRenderTarget()
            self._setViewport()
            rt.drawOnBounds(
                0,
                self.displayBounds.xlo,
                self.displayBounds.xhi,
                self.displayBounds.ylo,
                self.displayBounds.yHi,
                self.xax,
                self.yax)

        self.getAnnotations().draw(self.pos.z)

        if len(self.imageList) > 0:
            if self.showCursor:     self._drawCursor()
            if self.showGridLines:  self._drawGridLines()
            if self.highlightSlice: self._drawSliceHighlight()

        self._annotations.draw(self.pos.z, skipHold=True)
                
        self._postDraw()
