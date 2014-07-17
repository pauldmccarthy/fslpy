#!/usr/bin/env python
#
# glimagedata.py - Create OpenGL data to render 2D slices of a 3D image.
#
# A GLImageData object encapsulates the OpenGL information necessary
# to render 2D slices of a 3D image.
# 
# A slice from one image is rendered using four buffers and two textures.
#
# The first buffer, the 'geometry buffer' simply contains the 3D
# coordinates (single precision floating point) of four vertices, which
# define the geometry of a single voxel (using triangle strips).
#
# The remaining buffers contain the X, Y, and Z coordinates of the voxels
# in the slice to be displayed. These coordinates are stored as unsigned
# 16 bit integers, and used both to position a voxel, and to look up its
# value in the 3D data texture (see below). 
#
# The image data itself is stored as a 3D texture. Data for signed or
# unsigned 8 or 16 bit integer images is stored on the GPU in the same
# format; all other data types are stored as 32 bit floating point.
#
# Finally, a 1D texture is used is used to store a lookup table containing
# an RGBA8 colour map, to colour each voxel according to its value.
#
# All of these things are created when a GLImageData object is
# instantiated. They are available as attributes of the object:
#
#  - imageBuffer
#  - xBuffer
#  - yBuffer
#  - zBuffer
#  - geomBuffer
#  - colourBuffer
#
# The contents of all of these buffers is is dependent upon the way that
# the image is being displayed.  They are regenerated automatically when
# the image display properties are changed (via listeners registered on
# the relevant fsl.fslview.displaycontext.ImageDisplay properties).
# 
# If the display orientation changes (i.e. the image dimensions that map
# to the screen X/Y axes) the genIndexBuffers method must be called
# manually, to regenerate the voxel indices.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import numpy as np

class GLImageData(object):

    def __init__(self, image, xax, yax, imageDisplay):
        """
        Initialise the OpenGL data buffers required to render the given image.
        Parameters:
        
          - image:        A fsl.data.image.Image object.
        
          - xax:          The image axis which maps to the screen x axis.
        
          - yax:          The image axis which maps to the screen y axis.
        
          - imageDisplay: A fsl.fslview.displaycontext.ImageDisplay object
                          which describes how the image is to be displayed.
        """
        
        self.image   = image
        self.display = imageDisplay

        self.genVertexData(xax, yax)
        self.updateColourData()

        # Add listeners to this image so the view can be
        # updated when its display properties are changed
        self._configDisplayListeners()


    def genVertexData(self, xax, yax):
        """
        (Re-)Generates data buffers containing X, Y, and Z coordinates,
        used for indexing into the image. Also generates the geometry
        buffer, which defines the geometry of a single voxel. If a
        sampling rate other than 1 is passed in, the generated index
        buffers will contain a sampling of the full coordinate space
        for the X and Y dimensions, and the vertices in the geometry
        buffer will be scaled accordingly.
        """

        self.xax = xax
        self.yax = yax
        self.zax = 3 - xax - yax
        
        image = self.image

        # vertex coordinates
        # texture coordinates 

        xdim = image.shape[self.xax]
        ydim = image.shape[self.yax]

        xidxs = np.arange(xdim)
        yidxs = np.arange(ydim)
        
        xidxs, yidxs = np.meshgrid(xidxs, yidxs)
        
        xidxs = xidxs.ravel()
        yidxs = yidxs.ravel()

        geomData  = np.zeros((xdim * ydim * 4, 3), dtype=np.float32)
        
        for i, (xi, yi) in enumerate(zip(xidxs, yidxs)):
            geomData[i * 4 + 0, [xax, yax]] = [-0.5, -0.5]
            geomData[i * 4 + 1, [xax, yax]] = [-0.5,  0.5]
            geomData[i * 4 + 2, [xax, yax]] = [ 0.5,  0.5]
            geomData[i * 4 + 3, [xax, yax]] = [ 0.5, -0.5]
            geomData[i * 4:i * 4 + 4, xax] += xi
            geomData[i * 4:i * 4 + 4, yax] += yi

        geomData        = image.voxToWorld(geomData)
            
        self.vertexData = geomData.ravel('C')
        self.xdim       = image.shape[self.xax]
        self.ydim       = image.shape[self.yax]
        self.zdim       = image.shape[self.zax]

        
    def updateColourData(self):
        """
        Regenerates the colour buffer used to colour image voxels.
        """

        display = self.display

        log.debug('Generating colour buffer for '
                  'image {} (map: {})'.format(
                      self.image.name,
                      display.cmap.name))
    
        # Create [self.colourResolution] rgb values,
        # spanning the entire range of the image
        # colour map

        if self.image.is4DImage():
            image = self.image.data[:, :, :, display.volume]
        else:
            image = self.image.data

        image = np.transpose(image, (self.xax, self.yax, self.zax))

        imin  = float(display.displayRange.xlo)
        imax  = float(display.displayRange.xhi)
        image = (image - imin) / (imax - imin)

        colourData = display.cmap(image)
        colourData = np.floor(colourData * 255)
        colourData = np.array(colourData, dtype=np.uint8)
        colourData = colourData.repeat(4, 2)
        colourData = colourData.ravel('C')

        self.colourData = colourData


    def _configDisplayListeners(self):
        """
        Adds a bunch of listeners to the image.ImageDisplay object which
        defines how the given image is to be displayed. This is done so we
        can update the colour texture when image display properties are
        changed. 
        """

        def vertexUpdateNeeded(*a):
            self.genVertexData(self.xax, self.yax)

        def colourUpdateNeeded(*a):
            self.updateColourData()

        def colourAndVertexUpdateNeeded(*a):
            self.genVertexData(self.xax, self.yax)
            self.updateColourData()

        display = self.display
        lnrName = 'GlImageData_{}'.format(id(self))

        display.addListener('transform',    lnrName, vertexUpdateNeeded)
        display.addListener('displayRange', lnrName, colourUpdateNeeded)
        display.addListener('rangeClip',    lnrName, colourUpdateNeeded)
        display.addListener('cmap',         lnrName, colourUpdateNeeded)
        display.addListener('samplingRate',
                            lnrName,
                            colourAndVertexUpdateNeeded)
        display.addListener('volume',       lnrName, colourUpdateNeeded)
