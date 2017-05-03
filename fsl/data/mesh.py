#!/usr/bin/env python
#
# mesh.py - The TriangleMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`TriangleMesh` class, which represents a
3D model made of triangles.

.. note:: I/O support is very limited - currently, the only supported file
          type is the VTK legacy file format, containing the ``POLYDATA``
          dataset. the :class:`TriangleMesh` class assumes that every polygon
          defined in an input file is a triangle (i.e. refers to three
          vertices).

          See http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf
          for an overview of the VTK legacy file format.

          In the future, I may or may not add support for more complex meshes.
"""


import logging

import os.path as op
import numpy   as np

import six

from . import image as fslimage


log = logging.getLogger(__name__)


class TriangleMesh(object):
    """The ``TriangleMesh`` class represents a 3D model. A mesh is defined by
    a collection of vertices and indices.  The indices index into the list of
    vertices, and define a set of triangles which make the model.


    A ``TriangleMesh`` instance has the following attributes:


    ============== ====================================================
    ``name``       A name, typically the file name sans-suffix.

    ``dataSource`` Full path to the mesh file (or ``None`` if there is
                   no file associated with this mesh).

    ``vertices``   A :math:`N\times 3` ``numpy`` array containing
                   the vertices.

    ``indices``    A :meth:`M\times 3` ``numpy`` array containing
                   the vertex indices for :math:`M` triangles
    ============== ====================================================


    And the following methods:

    .. autosummary::
       :nosignatures:

       getBounds
       loadVertexData
       getVertexData
       clearVertexData
    """


    def __init__(self, data, indices=None):
        """Create a ``TriangleMesh`` instance.

        :arg data:    Can either be a file name, or a :math:`N\\times 3`
                      ``numpy`` array containing vertex data. If ``data`` is
                      a file name, it is passed to the
                      :func:`loadVTKPolydataFile` function.

        :arg indices: A list of indices into the vertex data, defining
                      the triangles.
        """

        if isinstance(data, six.string_types):
            infile = data
            data, lengths, indices = loadVTKPolydataFile(infile)

            if np.any(lengths != 3):
                raise RuntimeError('All polygons in VTK file must be '
                                   'triangles ({})'.format(infile))

            self.name       = op.basename(infile)
            self.dataSource = infile
        else:
            self.name       = 'TriangleMesh'
            self.dataSource = None

        if indices is None:
            indices = np.arange(data.shape[0])

        self.vertices     = np.array(data)
        self.indices      = np.array(indices).reshape((-1, 3))

        self.__vertexData = {}
        self.__loBounds   = self.vertices.min(axis=0)
        self.__hiBounds   = self.vertices.max(axis=0)


    def __repr__(self):
        """Returns a string representation of this ``TriangleMesh`` instance.
        """
        return '{}({}, {})'.format(type(self).__name__,
                                   self.name,
                                   self.dataSource)

    def __str__(self):
        """Returns a string representation of this ``TriangleMesh`` instance.
        """
        return self.__repr__()


    def getBounds(self):
        """Returns a tuple of values which define a minimal bounding box that
        will contain all vertices in this ``TriangleMesh`` instance. The
        bounding box is arranged like so:

            ``((xlow, ylow, zlow), (xhigh, yhigh, zhigh))``
        """
        return (self.__loBounds, self.__hiBounds)


    def loadVertexData(self, dataSource, vertexData=None):
        """Attempts to load scalar data associated with each vertex of this
        ``TriangleMesh`` from the given ``dataSource``. The data is returned,
        and also stored in an internal cache so it can be retrieved later
        via the :meth:`getVertexData` method.

        This method may be overridden by sub-classes.

        :arg dataSource: Path to the vertex data to load
        :arg vertexData: The vertex data itself, if it has already been
                         loaded.

        :returns: A ``(M, N)``) array, which contains ``N`` data points
                  for ``M`` vertices.
        """

        nvertices = self.vertices.shape[0]

        # Currently only white-space delimited
        # text files are supported
        if vertexData is None:
            vertexData = np.loadtxt(dataSource)
            vertexData.reshape(nvertices, -1)

        if vertexData.shape[0] != nvertices:
            raise ValueError('Incompatible size: {}'.format(dataSource))

        self.__vertexData[dataSource] = vertexData

        return vertexData


    def getVertexData(self, dataSource):
        """Returns the vertex data for the given ``dataSource`` from the
        internal vertex data cache. If the given ``dataSource`` is not
        in the cache, it is loaded via :meth:`loadVertexData`.
        """

        try:             return self.__vertexData[dataSource]
        except KeyError: return self.loadVertexData(dataSource)


    def clearVertexData(self):
        """Clears the internal vertex data cache - see the
        :meth:`loadVertexData` and :meth:`getVertexData`  methods.
        """

        self.__vertexData = {}


ALLOWED_EXTENSIONS     = ['.vtk']
"""A list of file extensions which could contain :class:`TriangleMesh` data.
"""


EXTENSION_DESCRIPTIONS = ['VTK polygon model file']
"""A description for each of the extensions in :data:`ALLOWED_EXTENSIONS`."""


def loadVTKPolydataFile(infile):
    """Loads a vtk legacy file containing a ``POLYDATA`` data set.

    :arg infile: Name of a file to load from.

    :returns: a tuple containing three values:

                - A :math:`N\\times 3` ``numpy`` array containing :math:`N`
                  vertices.
                - A 1D ``numpy`` array containing the lengths of each polygon.
                - A 1D ``numpy`` array containing the vertex indices for all
                  polygons.
    """

    lines = None

    with open(infile, 'rt') as f:
        lines = f.readlines()

    lines = [l.strip() for l in lines]

    if lines[3] != 'DATASET POLYDATA':
        raise ValueError('Only the POLYDATA data type is supported')

    nVertices = int(lines[4].split()[1])
    nPolygons = int(lines[5 + nVertices].split()[1])
    nIndices  = int(lines[5 + nVertices].split()[2]) - nPolygons

    vertices       = np.zeros((nVertices, 3), dtype=np.float32)
    polygonLengths = np.zeros( nPolygons,     dtype=np.uint32)
    indices        = np.zeros( nIndices,      dtype=np.uint32)

    for i in range(nVertices):
        vertLine       = lines[i + 5]
        vertices[i, :] = [float(w) for w in vertLine.split()]

    indexOffset = 0
    for i in range(nPolygons):

        polyLine          = lines[6 + nVertices + i].split()
        polygonLengths[i] = int(polyLine[0])

        start              = indexOffset
        end                = indexOffset + polygonLengths[i]
        indices[start:end] = [int(w) for w in polyLine[1:]]

        indexOffset        += polygonLengths[i]

    return vertices, polygonLengths, indices


def getFIRSTPrefix(modelfile):
    """If the given ``vtk`` file was generated by `FIRST
    <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_, this function
    will return the file prefix. Otherwise a ``ValueError`` will be
    raised.
    """

    if not modelfile.endswith('first.vtk'):
        raise ValueError('Not a first vtk file: {}'.format(modelfile))

    modelfile = op.basename(modelfile)
    prefix    = modelfile.split('-')
    prefix    = '-'.join(prefix[:-1])

    return prefix


def findReferenceImage(modelfile):
    """Given a ``vtk`` file, attempts to find a corresponding ``NIFTI``
    image file. Return the path to the image, or ``None`` if no image was
    found.

    Currently this function will only return an image for ``vtk`` files
    generated by `FIRST <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FIRST>`_.
    """

    try:

        dirname  = op.dirname(modelfile)
        prefixes = [getFIRSTPrefix(modelfile)]
    except:
        return None

    if prefixes[0].endswith('_first'):
        prefixes.append(prefixes[0][:-6])

    for p in prefixes:
        try:
            return fslimage.addExt(op.join(dirname, p), mustExist=True)
        except:
            continue

    return None
