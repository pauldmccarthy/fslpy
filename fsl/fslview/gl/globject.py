#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and OpenGL
# representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`GLObject` class, which is a superclass for
all 2D OpenGL representations of :class:`fsl.data.image.Image` instances.

This module also provides the :func:`createGLObject` function, which provides
mappings between :class:`~fsl.data.image.Image` types, and their corresponding
OpenGL representation.

Some other convenience functions are also provided, for generating
OpenGL vertex data.
"""


import logging

import itertools           as it
import numpy               as np
import fsl.utils.transform as transform


log = logging.getLogger(__name__)


def createGLObject(image, display):
    """Create :class:`GLObject` instance for the given
    :class:`~fsl.data.image.Image` instance.

    :arg image:   A :class:`~fsl.data.image.Image` instance.
    :arg display: A :class:`~fsl.fslview.displaycontext.Display` instance.
    """

    import fsl.fslview.gl.glvolume as glvolume
    import fsl.fslview.gl.glmask   as glmask
    import fsl.fslview.gl.glvector as glvector

    _objectmap = {
        'volume' : glvolume.GLVolume,
        'mask'   : glmask  .GLMask,
        'vector' : glvector.GLVector
    } 

    ctr = _objectmap.get(display.imageType, None)

    if ctr is not None: return ctr(image, display)
    else:               return None


class GLObject(object):
    """The :class:`GLObject` class is a superclass for all 2D OpenGL
    objects.
    """

    def __init__(self):
        """Create a :class:`GLObject`.  The constructor adds one attribute to
        this instance, ``name``, which is simply a unique name for this
        instance.
        """

        self.name = '{}_{}'.format(type(self).__name__, id(self))
                

    def init(self):
        """Perform any necessary OpenGL initialisation, such as
        creating textures and vertices.
        """
        raise NotImplementedError()

    
    def ready(self):
        """This method should return ``False`` if this :class:`GLObject` is
        not yet ready to be displayed, ``True`` otherwise.
        """
        raise NotImplementedError()

    
    def setAxes(self, xax, yax):
        """This method is called when the display orientation for this
        :class:`GLObject` changes. It should perform any necessary updates to
        the GL data (e.g. regenerating/moving vertices).
        """
        raise NotImplementedError()

    
    def destroy(self):
        """This method is called when this :class:`GLObject` is no longer
        needed.
        
        It should perform any necessary cleaning up, such as deleting texture
        handles.
        """
        raise NotImplementedError()

    
    def preDraw(self):
        """This method is called at the start of a draw routine.

        It should perform any initialisation which is required before one or
        more calls to the :meth:`draw` method are made, such as binding and
        configuring textures.
        """
        raise NotImplementedError()

    
    def draw(self, zpos, xform=None):
        """This method should draw a view of this :class:`GLObject` at the
        given Z position, which specifies the position along the screen
        depth axis.

        If the ``xform`` parameter is provided, it should be applied to the
        model view transformation before drawing.
        """
        raise NotImplementedError()


    def drawAll(self, zposes, xforms):
        """This method should do the same as multiple calls to the
        :meth:`draw` method, one for each of the Z positions and
        transformation matrices contained in the ``zposes`` and
        ``xforms`` arrays.

        In some circumstances (hint: the
        :class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas`),
        better performance may be achievbed in combining multiple
        renders, rather than doing it with separate calls to :meth:`draw`.

        The default implementation does exactly this, so this method
        need only be overridden for subclasses which are able to get
        better performance by combining the draws.
        """
        for (zpos, xform) in zip(zposes, xforms):
            self.draw(zpos, xform)


    def postDraw(self):
        """This method is called after the :meth:`draw` method has been called
        one or more times.

        It should perform any necessary cleaning up, such as unbinding
        textures.
        """
        raise NotImplementedError()


class GLSimpleObject(GLObject):
    """The ``GLSimpleObject`` class is a convenience superclass for simple
    rendering tasks (probably fixed-function) which require no setup or
    initialisation/management of GL memory or state. All subclasses need to
    do is implement the :meth:`GLObject.draw` method.

    Subclasses should not assume that any of the other methods will ever
    be called.

    On calls to :meth:`draw`, the following attributes will be available on
    ``GLSimpleObject`` instances:

      - ``xax``: Index of the display coordinate system axis that corresponds
                 to the horizontal screen axis.
      - ``yax``: Index of the display coordinate system axis that corresponds
                 to the vertical screen axis.
    """

    def __init__(self):
        GLObject.__init__(self)
        self.__ready = False

    def init(   self): pass
    def destroy(self): pass
    def ready(  self): return self.__ready

    def setAxes(self, xax, yax):
        self.xax     =  xax
        self.yax     =  yax
        self.zax     = 3 - xax - yax
        self.__ready = True

    def preDraw( self): pass
    def postDraw(self): pass


class GLImageObject(GLObject):
    """The ``GLImageObject` class is the superclass for all GL representations
    of :class:`~fsl.data.image.Image` instances.
    """
    
    def __init__(self, image, display):
        """Create a ``GLImageObject``.

        This constructor adds the following attributes to this instance:
        
          - ``image``:       A reference to the image.
          - ``display``:     A reference to the display.
          - ``displayOpts``: A reference to the image type-specific display
                             options.

        :arg image:   The :class:`~fsl.data.image.Image` instance
        :arg display: An associated
                      :class:`~fsl.fslview.displaycontext.Display` instance.
        """
        
        GLObject.__init__(self)
        self.image       = image
        self.display     = display
        self.displayOpts = display.getDisplayOpts()


def calculateSamplePoints(image, display, xax, yax):
    """Calculates a uniform grid of points, in the display coordinate system
    (as specified by the given
    :class:`~fsl.fslview.displaycontext.ImageDisplay` object properties) along
    the x-y plane (as specified by the xax/yax indices), at which the given
    image should be sampled for display purposes.

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
    transformMat  = display.getTransform('voxel', 'display')
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
    
    coords = np.zeros((worldX.size, 3), dtype=np.float32)
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
    """Given a regular 2D grid of points at which an image is to be sampled
    (for example, that generated by the :func:`calculateSamplePoints` function
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


def voxelGrid(points, xax, yax, xpixdim, ypixdim):
    """Given a ``N*3`` array of ``points`` (assumed to be voxel
    coordinates), creates an array of vertices which can be used
    to render each point as an unfilled rectangle.

    :arg points:  An ``N*3`` array of voxel xyz coordinates

    :arg xax:     XYZ axis index that maps to the horizontal scren axis
    
    :arg yax:     XYZ axis index that maps to the vertical scren axis
    
    :arg xpixdim: Length of a voxel along the x axis.
    
    :arg ypixdim: Length of a voxel along the y axis.
    """

    if len(points.shape) == 1:
        points = points.reshape(1, 3)

    npoints  = points.shape[0]
    vertices = np.repeat(np.array(points, dtype=np.float32), 4, axis=0)

    xpixdim = xpixdim / 2.0
    ypixdim = ypixdim / 2.0

    # bottom left corner
    vertices[ ::4, xax] -= xpixdim 
    vertices[ ::4, yax] -= ypixdim

    # bottom right
    vertices[1::4, xax] += xpixdim
    vertices[1::4, yax] -= ypixdim
    
    # top left
    vertices[2::4, xax] -= xpixdim
    vertices[2::4, yax] += ypixdim

    # top right
    vertices[3::4, xax] += xpixdim
    vertices[3::4, yax] += ypixdim

    # each square is rendered as four lines
    indices = np.array([0, 1, 0, 2, 1, 3, 2, 3], dtype=np.uint32)
    indices = np.tile(indices, npoints)
    
    indices = (indices.T +
               np.repeat(np.arange(0, npoints * 4, 4, dtype=np.uint32), 8)).T
    
    return vertices, indices


def slice2D(dataShape, xax, yax, voxToDisplayMat):
    """Generates and returns four vertices which denote a slice through an
    array of the given ``dataShape``, parallel to the plane defined by the
    given ``xax`` and ``yax``, in the space defined by the given
    ``voxToDisplayMat``.

    :arg dataShape:       Number of elements along each dimension in the
                          image data.
    
    :arg xax:             Index of display axis which corresponds to the
                          horizontal screen axis.

    :arg yax:             Index of display axis which corresponds to the
                          vertical screen axis. 
    
    :arg voxToDisplayMat: Affine transformation matrix which transforms from
                          voxel/array indices into the display coordinate
                          system.
    
    Returns a tuple containing:
    
      - A ``4*3`` ``numpy.float32`` array containing the vertex locations
        of a slice through the data. The values along the ``Z`` axis are set
        to ``0``.
    
      - A ``numpy.uint32`` array to be used as vertex indices.
    """
        
    xmin, xmax = transform.axisBounds(dataShape, voxToDisplayMat, xax)
    ymin, ymax = transform.axisBounds(dataShape, voxToDisplayMat, yax)

    worldCoords = np.zeros((4, 3), dtype=np.float32)

    worldCoords[0, [xax, yax]] = (xmin, ymin)
    worldCoords[1, [xax, yax]] = (xmin, ymax)
    worldCoords[2, [xax, yax]] = (xmax, ymin)
    worldCoords[3, [xax, yax]] = (xmax, ymax)

    indices = np.arange(0, 4, dtype=np.uint32)

    return worldCoords, indices 


def subsample(data, resolution, pixdim=None, volume=None):
    """Samples the given data according to the given resolution.

    :arg data:       The data to be sampled.

    :arg resolution: Sampling resolution, proportional to the values in
                     ``pixdim``.

    :arg pixdim:     Length of each dimension in the input data (defaults to
                     ``(1.0, 1.0, 1.0)``).

    :arg volume:     If the image is a 4D volume, the volume index of the 3D
                     image to be sampled.
    """

    if pixdim is None:
        pixdim = (1.0, 1.0, 1.0)

    xstep = np.round(resolution / pixdim[0])
    ystep = np.round(resolution / pixdim[1])
    zstep = np.round(resolution / pixdim[2])

    if xstep < 1: xstep = 1
    if ystep < 1: ystep = 1
    if zstep < 1: zstep = 1

    xstart = xstep / 2
    ystart = ystep / 2
    zstart = zstep / 2

    if volume is not None:
        if len(data.shape) > 3: sample = data[xstart::xstep,
                                              ystart::ystep,
                                              zstart::zstep,
                                              volume]
        else:                   sample = data[xstart::xstep,
                                              ystart::ystep,
                                              zstart::zstep]
    else:
        if len(data.shape) > 3: sample = data[xstart::xstep,
                                              ystart::ystep,
                                              zstart::zstep,
                                              :]
        else:                   sample = data[xstart::xstep,
                                              ystart::ystep,
                                              zstart::zstep]        

    return sample


def broadcast(vertices, indices, zposes, xforms, zax):
    """Given a set of vertices and indices (assumed to be 2D representations
    of some geometry in a 3D space, with the depth axis specified by ``zax``),
    replicates them across all of the specified Z positions, applying the
    corresponding transformation to each set of vertices.

    :arg vertices: Vertex array (a ``N*3`` numpy array).
    
    :arg indices:  Index array.
    
    :arg zposes:   Positions along the depth axis at which the vertices
                   are to be replicated.
    
    :arg xforms:   Sequence of transformation matrices, one for each
                   Z position.
    
    :arg zax:      Index of the 'depth' axis

    Returns three values:
    
      - A numpy array containing all of the generated vertices
    
      - A numpy array containing the original vertices for each of the
        generated vertices, which may be used as texture coordinates

      - A new numpy array containing all of the generated indices.
    """

    vertices = np.array(vertices)
    indices  = np.array(indices)
    
    nverts   = vertices.shape[0]
    nidxs    = indices.shape[ 0]

    allTexCoords  = np.zeros((nverts * len(zposes), 3), dtype=np.float32)
    allVertCoords = np.zeros((nverts * len(zposes), 3), dtype=np.float32)
    allIndices    = np.zeros( nidxs  * len(zposes),     dtype=np.uint32)
    
    for i, (zpos, xform) in enumerate(zip(zposes, xforms)):

        vertices[:, zax] = zpos

        vStart = i * nverts
        vEnd   = vStart + nverts

        iStart = i * nidxs
        iEnd   = iStart + nidxs

        allIndices[   iStart:iEnd]    = indices + i * nverts
        allTexCoords[ vStart:vEnd, :] = vertices
        allVertCoords[vStart:vEnd, :] = transform.transform(vertices, xform)
        
    return allVertCoords, allTexCoords, allIndices
