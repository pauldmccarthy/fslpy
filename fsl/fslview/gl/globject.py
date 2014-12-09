#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and OpenGL
# representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
This module provides the :func:`createGLObject` function, which provides
mappings between :class:`~fsl.data.image.Image` types, and their
corresponding OpenGL representation.

Some other convenience functions are also provided, for generating
OpenGL vertex data.


GL Objects must have the following methods:
  - ``__init__(self, image, display)``

  - ``init(   self, xax, yax)``

  - ``ready(self)``

  - ``setAxes(self, xax, yax)``

  - ``destroy(self)``

  - ``preDraw(self)``

  - ``draw(self, zpos, xform=None)``

  - ``postDraw(self)``

"""

import logging
log = logging.getLogger(__name__)

import itertools           as it
import numpy               as np
import fsl.utils.transform as transform


def createGLObject(image, display):

    import fsl.fslview.gl.glimage      as glimage
    import fsl.fslview.gl.gltensorline as gltensorline

    _objectmap = {
        'volume' : glimage     .GLImage,
        'tensor' : gltensorline.GLTensorLine
    } 

    ctr = _objectmap.get(display.imageType, None)

    if ctr is not None: return ctr(image, display)
    else:               return None


def calculateSamplePoints(image, display, xax, yax):
    """Calculates a uniform grid of points, in the display coordinate system (as
    specified by the given :class:`~fsl.fslview.displaycontext.ImageDisplay`
    object properties) along the x-y plane (as specified by the xax/yax
    indices), at which the given image should be sampled for display purposes.

    This function returns a tuple containing:

     - a numpy array of shape `(N, 3)`, containing the coordinates of the
       centre of every sampling point in real world space.

     - the horizontal distance (along xax) between adjacent points

     - the vertical distance (along yax) between adjacent points

     - The number of samples along the horizontal axis (xax)

     - The number of samples along the vertical axis (yax)

    :arg image:   The :class:`~fsl.data.image.Image` object to
                  generate vertex and texture coordinates for.

    :arg display: A :class:`~fsl.fslview.displaycontext.ImageDisplay`
                  object which defines how the image is to be
                  rendered.

    :arg xax:     The world space axis which corresponds to the
                  horizontal screen axis (0, 1, or 2).

    :arg yax:     The world space axis which corresponds to the
                  vertical screen axis (0, 1, or 2).
    """

    transformCode = display.transform
    transformMat  = display.voxToDisplayMat 
    worldRes      = display.resolution
    
    xVoxelRes     = np.round(worldRes / image.pixdim[xax])
    yVoxelRes     = np.round(worldRes / image.pixdim[yax])

    if xVoxelRes < 1: xVoxelRes = 1
    if yVoxelRes < 1: yVoxelRes = 1

    # These values give the min/max x/y values
    # of a bounding box which encapsulates
    # the entire image
    xmin, xmax = transform.axisBounds(image.shape, transformMat, xax)
    ymin, ymax = transform.axisBounds(image.shape, transformMat, yax)


    # The width/height of a displayed voxel.
    # If we are displaying in real world space,
    # we use the world display resolution
    if transformCode == 'affine':

        xpixdim = worldRes
        ypixdim = worldRes

    # But if we're just displaying the data (the
    # transform is 'id' or 'pixdim'), we display
    # it in the resolution of said data.
    elif transformCode == 'pixdim':
        xpixdim = image.pixdim[xax] * xVoxelRes
        ypixdim = image.pixdim[yax] * yVoxelRes
        
    elif transformCode == 'id':
        xpixdim = 1.0 * xVoxelRes
        ypixdim = 1.0 * yVoxelRes

    # Number of samples across each dimension,
    # given the current sample rate
    xNumSamples = np.floor((xmax - xmin) / xpixdim)
    yNumSamples = np.floor((ymax - ymin) / ypixdim)

    # the adjusted width/height of our sample points
    xpixdim = (xmax - xmin) / xNumSamples
    ypixdim = (ymax - ymin) / yNumSamples

    log.debug('Generating coordinate buffers for {} '
              '({} resolution {}/({}, {}), num samples {})'.format(
                  image.name, transformCode, worldRes, xVoxelRes, yVoxelRes,
                  xNumSamples * yNumSamples))

    # The location of every displayed
    # point in real world space
    worldX = np.linspace(xmin + 0.5 * xpixdim,
                         xmax - 0.5 * xpixdim,
                         xNumSamples)
    worldY = np.linspace(ymin + 0.5 * ypixdim,
                         ymax - 0.5 * ypixdim,
                         yNumSamples)

    worldX, worldY = np.meshgrid(worldX, worldY)
    
    coords = np.zeros((worldX.size, 3))
    coords[:, xax] = worldX.flatten()
    coords[:, yax] = worldY.flatten()

    return coords, xpixdim, ypixdim, xNumSamples, yNumSamples


def samplePointsToTriangleStrip(coords,
                                xpixdim,
                                ypixdim,
                                xlen,
                                ylen,
                                xax,
                                yax):
    """Given a regular 2D grid of points at which an image is to be sampled (for
    example, that generated by the :func:`calculateSamplePoints` function
    above), converts those points into an OpenGL vertex triangle strip.

    A grid of M*N points is represented by M*2*(N + 1) vertices. For example,
    this image represents a 4*3 grid, with periods representing vertex
    locations::
    
        .___.___.___.___.
        |   |   |   |   |
        |   |   |   |   |
        .---.---.---.---.
        .___.___.__ .___.
        |   |   |   |   |
        |   |   |   |   |
        .---.---.---.---.
        .___.___.___.___.
        |   |   |   |   |
        |   |   |   |   |
        .___.___.___.___.

    
    Vertex locations which are vertically adjacent represent the same point in
    space. Such vertex pairs are unable to be combined because, in OpenGL,
    they must be represented by distinct vertices (we can't apply multiple
    colours/texture coordinates to a single vertex location) So we have to
    repeat these vertices in order to achieve accurate colouring of each
    voxel.

    We draw each horizontal row of samples one by one, using two triangles to
    draw each voxel. In order to eliminate the need to specify six vertices
    for every voxel, and hence to reduce the amount of memory used, we are
    using a triangle strip to draw each row of voxels. This image depicts a
    triangle strip used to draw a row of three samples (periods represent
    vertex locations)::


        1  3  5  7
        .  .  .  .
        |\ |\ |\ |
        | \| \| \|
        .  .  .  .
        0  2  4  6
      
    In order to use a single OpenGL call to draw multiple non-contiguous voxel
    rows, between every column we add a couple of 'dummy' vertices, which will
    then be interpreted by OpenGL as 'degenerate triangles', and will not be
    drawn. So in reality, a 4*3 slice would be drawn as follows (with vertices
    labelled from [a-z0-9]:

         v  x  z  1  33
         |\ |\ |\ |\ |
         | \| \| \| \|
        uu  w  y  0  2
         l  n  p  r  tt
         |\ |\ |\ |\ |
         | \| \| \| \|
        kk  m  o  q  s  
         b  d  f  h  jj
         |\ |\ |\ |\ |
         | \| \| \| \|
         a  c  e  g  i
    
    These repeated/degenerate vertices are dealt with by using a vertex index
    array.  See these links for good overviews of triangle strips and
    degenerate triangles in OpenGL:
    
     - http://www.learnopengles.com/tag/degenerate-triangles/
     - http://en.wikipedia.org/wiki/Triangle_strip

    A tuple is returned containing:

      - A 2D `numpy.float32` array of shape `(2 * (xlen + 1) * ylen), 3)`,
        containing the coordinates of all triangle strip vertices which
        represent the entire grid of sample points.
    
      - A 2D `numpy.float32` array of shape `(2 * (xlen + 1) * ylen), 3)`,
        containing the centre of every grid, to be used for texture
        coordinates/colour lookup.
    
      - A 1D `numpy.uint32` array of size `ylen * (2 * (xlen + 1) + 2) - 2`
        containing indices into the first array, defining the order in which
        the vertices need to be rendered. There are more indices than vertex
        coordinates due to the inclusion of repeated/degenerate vertices.

    :arg coords:  N*3 array of points, the sampling locations.
    
    :arg xpixdim: Length of one sample along the horizontal axis.
    
    :arg ypixdim: Length of one sample along the vertical axis.
    
    :arg xlen:    Number of samples along the horizontal axis.
    
    :arg ylen:    Number of samples along the vertical axis.
    
    :arg xax:     Display coordinate system axis which corresponds to the
                  horizontal screen axis.
    
    :arg yax:     Display coordinate system axis which corresponds to the
                  vertical screen axis.
    """

    coords = coords.reshape(ylen, xlen, 3)

    xlen = int(xlen)
    ylen = int(ylen)

    # Duplicate every row - each voxel
    # is defined by two vertices 
    coords = coords.repeat(2, 0)

    texCoords   = np.array(coords, dtype=np.float32)
    worldCoords = np.array(coords, dtype=np.float32)

    # Add an extra column at the end
    # of the world coordinates
    worldCoords = np.append(worldCoords, worldCoords[:, -1:, :], 1)
    worldCoords[:, -1, xax] += xpixdim

    # Add an extra column at the start
    # of the texture coordinates
    texCoords = np.append(texCoords[:, :1, :], texCoords, 1)

    # Move the x/y world coordinates to the
    # sampling point corners (the texture
    # coordinates remain in the voxel centres)
    worldCoords[   :, :, xax] -= 0.5 * xpixdim
    worldCoords[ ::2, :, yax] -= 0.5 * ypixdim
    worldCoords[1::2, :, yax] += 0.5 * ypixdim 

    vertsPerRow  = 2 * (xlen + 1) 
    dVertsPerRow = 2 * (xlen + 1) + 2
    nindices     = ylen * dVertsPerRow - 2

    indices = np.zeros(nindices, dtype=np.uint32)

    for yi, xi in it.product(range(ylen), range(xlen + 1)):
        
        ii = yi * dVertsPerRow + 2 * xi
        vi = yi *  vertsPerRow + xi
        
        indices[ii]     = vi
        indices[ii + 1] = vi + xlen + 1

        # add degenerate vertices at the end
        # every row (but not needed for last
        # row)
        if xi == xlen and yi < ylen - 1:
            indices[ii + 2] = vi + xlen + 1
            indices[ii + 3] = (yi + 1) * vertsPerRow

    worldCoords = worldCoords.reshape((xlen + 1) * (2 * ylen), 3)
    texCoords   = texCoords  .reshape((xlen + 1) * (2 * ylen), 3)

    return worldCoords, texCoords, indices
