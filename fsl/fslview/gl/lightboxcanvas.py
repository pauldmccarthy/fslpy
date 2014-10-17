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

import logging

log = logging.getLogger(__name__)

import OpenGL.GL      as gl
import numpy          as np

import                   slicecanvas
import                   props


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

    
    ncols = props.Int(clamped=True, minval=1, maxval=20, default=5)
    """This property controls the number of 
    slices to be displayed on a single row.
    """

    
    nrows = props.Int(clamped=True, minval=1, maxval=20, default=4)
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

    
    _labels = dict(
        slicecanvas.SliceCanvas._labels.items() +
        [('sliceSpacing',  'Slice spacing'),
         ('ncols',         'Number of columns'),
         ('nrows',         'Number of rows'),
         ('topRow',        'Top row'),
         ('zrange',        'Slice range'),
         ('showGridLines', 'Show grid lines')])
    """Labels for the properties which are intended to be user editable."""


    _tooltips = dict(
        slicecanvas.SliceCanvas._tooltips.items() +
        [('sliceSpacing',  'Distance (mm) between consecutive slices'),
         ('ncols',         'Number of slices to display on one row'),
         ('nrows',         'Number of rows to display on the canvas'),
         ('topRow',        'Index number of top row (from '
                           '0 to nrows-1) to display'),
         ('zrange',        'Range (mm) along Z axis of slices to display'),
         ('showGridLines', 'Show grid lines between slices')])
    """Tooltips to be used as help text."""

    _propHelp = _tooltips
    
    
    def worldToCanvas(self, xpos, ypos, zpos):
        """Given an x/y/z location in the image list world (with xpos
        corresponding to the horizontal screen axis, ypos to the vertical
        axis, and zpos to the depth axis), converts it into an x/y position,
        in world coordinates, on the canvas.
        """
        sliceno = int(np.floor((zpos - self.zrange.xlo) / self.sliceSpacing))

        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)
        
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
        3-tuple containing the (x, y, z) coordinates (in the dimension order
        of the image list space). If the given canvas position is out of the
        image range, ``None`` is returned.
        """

        nrows = self._totalRows
        ncols = self.ncols

        screenx, screeny = slicecanvas.SliceCanvas.canvasToWorld(
            self, xpos, ypos)

        xmin = self.imageList.bounds.getLo( self.xax)
        ymin = self.imageList.bounds.getLo( self.yax)
        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)

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

        
    def __init__(self, imageList, zax=0):
        """Create a :class:`LightBoxCanvas` object.
        
        :arg imageList: a :class:`~fsl.data.image.ImageList` object which
                        contains, or will contain, a list of images to be
                        displayed.
        
        :arg zax:       Image axis to be used as the 'depth' axis. Can be
                        changed via the :attr:`LightBoxCanvas.zax` property.
        """

        # These attributes are used to keep track of
        # the total number of slices to be displayed,
        # and the total number of rows to be displayed
        self._nslices   = 0
        self._totalRows = 0

        slicecanvas.SliceCanvas.__init__(self, imageList, zax)

        # default to showing the entire slice range
        self.zrange.x = imageList.bounds.getRange(self.zax)

        self._slicePropsChanged()

        self.addListener('sliceSpacing',  self.name, self._slicePropsChanged)
        self.addListener('ncols',         self.name, self._slicePropsChanged)
        self.addListener('nrows',         self.name, self._slicePropsChanged)
        self.addListener('zrange',        self.name, self._slicePropsChanged)
        self.addListener('showGridLines', self.name,
                         lambda *a: self._refresh())

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

        
    def getTotalRows(self):
        """Returns the total number of rows that may be displayed.
        """
        return self._totalRows


    def _slicePropsChanged(self, *a):
        """Called when any of the slice properties change. Regenerates slice
        locations and display bounds, and redraws
        """
        
        self._calcNumSlices()
        self._updateDisplayBounds()
        self._genSliceLocations()
        self._zPosChanged()
        self._refresh()


    def _calcNumSlices(self, *a):
        """Calculates the total number of slices to be displayed and
        the total number of rows.
        """
        
        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)
        zlen = self.zrange.xlen
        width, height = self._getSize()

        if xlen   == 0 or \
           ylen   == 0 or \
           width  == 0 or \
           height == 0:
            return

        self._nslices   = int(np.floor(zlen / self.sliceSpacing))
        self._totalRows = np.ceil(self._nslices / float(self.ncols))

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
        self._genSliceLocations()
        slicecanvas.SliceCanvas._imageListChanged(self, *a)


    def _updateZAxisProperties(self):
        """Called by the :meth:`_imageBoundsChanged` method.

        The purpose of this method is to set the slice spacing and displayed Z
        range to something sensible when the Z axis, or Z image bounds are
        changed (e.g. due to images being added/removed, or to image
        transformation matrices being changed).

        """
        newZRange = self.imageList.bounds.getRange(self.zax)
        newZGap   = self.sliceSpacing

        # Pick a sensible default for the
        # slice spacing - the smallest pixdim
        # across all images in the list
        if len(self.imageList) > 0:
            newZGap = min([i.pixdim[self.zax] for i in self.imageList])

        # Changing the zrange/sliceSpacing properties will, in most cases,
        # trigger a call to _slicePropsChanged. But for images which have the
        # same range across more than one dimension, the call might not
        # happen. So we do a check and, if the dimension ranges are the same,
        # manually call _slicePropsChanged.  Bringing out the ugly side of
        # event driven programming.
        if self.zrange.x == newZRange and self.sliceSpacing == newZGap:
            self._slicePropsChanged()
        else:
            self.zrange.x     = newZRange
            self.sliceSpacing = newZGap
            self.setConstraint('zrange', 'minDistance', newZGap)


    def _imageBoundsChanged(self, *a):
        """Overrides
        :meth:`fsl.fslview.gl.slicecanvas.SliceCanvas._imageBoundsChanged`.

        Called when the image bounds change. Updates the :attr:`zrange`
        min/max values.
        """

        slicecanvas.SliceCanvas._imageBoundsChanged(self)

        zmin,    zmax    = self.imageList.bounds.getRange(self.zax)
        oldzmin, oldzmax = self.zrange.getLimits(0)
        
        self.zrange.setLimits(0, zmin, zmax)

        # if the old limits were (0, 0) we assume
        # that the image list was empty, and the
        # zrange needs to be reset. 
        if (oldzmin == 0) and (oldzmax == 0):
            self.zrange.x = (zmin, zmax)

        if len(self.imageList) > 0:
            zgap = min([i.pixdim[self.zax] for i in self.imageList])
            self.setConstraint('zrange', 'minDistance', zgap)

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

        xmin = self.imageList.bounds.getLo( self.xax)
        ymin = self.imageList.bounds.getLo( self.yax)
        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)

        off  = self._totalRows - self.nrows - self.topRow
        ymin = ymin + ylen * off
        xmax = xmin + xlen * self.ncols
        ymax = ymin + ylen * self.nrows

        # The final display bounds calculated by
        # SliceCanvas._updateDisplayBounds is not
        # necessarily the same as the actual bounds,
        # as they are  adjusted to preserve  the
        # image aspect ratio. But the real bounds
        # are of use in the _zPosChangedmethod, so
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

        self._sliceLocs  = []
        self._transforms = []

        # calculate the transformation for each
        # slice in each image, and the index of
        # each slice to be displayed
        for i, image in enumerate(self.imageList):
            
            self._transforms.append([])
            self._sliceLocs .append([])

            for zi, zpos in enumerate(sliceLocs):

                xform = self._calculateSliceTransform(image, zi)

                self._transforms[-1].append(xform)
                self._sliceLocs[ -1].append(zpos)


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

        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)

        translate              = np.identity(4, dtype=np.float32)
        translate[3, self.xax] = xlen * col
        translate[3, self.yax] = ylen * (nrows - row - 1)
        translate[3, self.zax] = 0
        
        return translate


    def _drawGridLines(self):
        """Draws grid lines between all the displayed slices."""

        xlen = self.imageList.bounds.getLen(self.xax)
        ylen = self.imageList.bounds.getLen(self.yax)
        xmin = self.imageList.bounds.getLo( self.xax)
        ymin = self.imageList.bounds.getLo( self.yax)

        rowLines = np.zeros(((self.nrows - 1) * 2, 3), dtype=np.float32)
        colLines = np.zeros(((self.ncols - 1) * 2, 3), dtype=np.float32)
        
        topRow = self._totalRows - self.topRow 
        btmRow = topRow          - self.nrows
        
        rowLines[:, self.yax] = np.arange(
            ymin + (btmRow + 1) * ylen,
            ymin +  topRow      * ylen, ylen).repeat(2)

        rowLines[:, self.xax] = np.tile(
            np.array([xmin, xmin + self.ncols * xlen]),
            self.nrows - 1)
        
        colLines[:, self.xax] = np.arange(
            xmin + xlen,
            xmin + xlen * self.ncols, xlen).repeat(2) 
        
        colLines[:, self.yax] = np.tile(np.array([
            ymin + btmRow * ylen,
            ymin + topRow * ylen]), self.ncols - 1)

        gl.glLineWidth(2)
        gl.glBegin(gl.GL_LINES)

        gl.glColor4f(0.3, 0.9, 1.0, 0.8)
        for v in rowLines: gl.glVertex3f(*v)
        for v in colLines: gl.glVertex3f(*v)
        
        gl.glEnd() 


    def _drawCursor(self):
        """Draws a cursor at the current canvas position (the
        :attr:`~fsl.fslview.gl.SliceCanvas.pos` property).
        """

        sliceno = int(np.floor((self.pos.z - self.zrange.xlo) /
                               self.sliceSpacing))
        xlen    = self.imageList.bounds.getLen(self.xax)
        ylen    = self.imageList.bounds.getLen(self.yax)
        xmin    = self.imageList.bounds.getLo( self.xax)
        ymin    = self.imageList.bounds.getLo( self.yax)
        row     = self._totalRows - int(np.floor(sliceno / self.ncols)) - 1
        col     = int(np.floor(sliceno % self.ncols))

        xpos, ypos = self.worldToCanvas(*self.pos.xyz)

        xverts = np.zeros((2, 3))
        yverts = np.zeros((2, 3)) 

        xverts[:, self.xax] = xpos
        xverts[0, self.yax] = ymin + (row)     * ylen
        xverts[1, self.yax] = ymin + (row + 1) * ylen
        xverts[:, self.zax] = self.pos.z + 1

        yverts[:, self.yax] = ypos
        yverts[0, self.xax] = xmin + (col)     * xlen
        yverts[1, self.xax] = xmin + (col + 1) * xlen
        yverts[:, self.zax] = self.pos.z + 1

        gl.glLineWidth(1)
        gl.glBegin(gl.GL_LINES)
        gl.glColor3f(0, 1, 0)
        gl.glVertex3f(*xverts[0])
        gl.glVertex3f(*xverts[1])
        gl.glVertex3f(*yverts[0])
        gl.glVertex3f(*yverts[1])
        gl.glEnd() 

        
    def _draw(self):
        """
        """

        self._setGLContext()
        self._setViewport()

        startSlice   = self.ncols * self.topRow
        endSlice     = startSlice + self.nrows * self.ncols

        if endSlice > self._nslices:
            endSlice = self._nslices    

        # clear the canvas
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # enable transparency
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

        # disable interpolation
        gl.glShadeModel(gl.GL_FLAT)

        # Draw all the slices for all the images.
        for i, image in enumerate(self.imageList):

            try: globj = image.getAttribute(self.name)
            except KeyError:
                continue

            if (globj is None) or (not globj.ready()):
                continue 

            log.debug('Drawing {} slices ({} - {}) for image {}'.format(
                endSlice - startSlice, startSlice, endSlice, i))

            for zi in range(startSlice, endSlice):
                globj.draw(self._sliceLocs[ i][zi],
                           self._transforms[i][zi])

        if len(self.imageList) > 0:
            if self.showCursor:    self._drawCursor()
            if self.showGridLines: self._drawGridLines() 

        self._postDraw()
