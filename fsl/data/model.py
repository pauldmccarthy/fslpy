#!/usr/bin/env python
#
# model.py - The Model class, for VTK polygon data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Model` class, which represents a 3D model.

.. note:: I/O support is very limited - currently, the only supported file 
          type is the VTK legacy file format, containing the ``POLYDATA``
          dataset. the :class:`Model` class assumes that every polygon defined
          in an input file is a triangle (i.e. refers to three vertices).

          See http://www.vtk.org/wp-content/uploads/2015/04/file-formats.pdf
          for an overview of the VTK legacy file format.
"""


import logging

import os.path as op
import numpy   as np


log = logging.getLogger(__name__)


class Model(object):
    """The ``Model`` class represents a 3D model. A model is defined by a
    collection of vertices and indices.  The indices index into the list of
    vertices, and define a set of triangles which make the model.
    """

    
    def __init__(self, data, indices=None):
        """Create a ``Model`` instance.

        :arg data:    Can either be a file name, or a :math:`N\\times 3`
                      ``numpy`` array containing vertex data. If ``data`` is
                      a file name, it is passed to the
                      :func:`loadVTKPolydataFile` function.

        :arg indices: A list of indices into the vertex data.
        """

        if isinstance(data, basestring):
            infile = data
            data, lengths, indices = loadVTKPolydataFile(infile)

            if np.any(lengths != 3):
                raise RuntimeError('All polygons in VTK file must be '
                                   'triangles ({})'.format(infile))

            self.name       = op.basename(infile)
            self.dataSource = infile
        else:
            self.name       = 'Model'
            self.dataSource = 'Model'
            
        if indices is None:
            indices = np.arange(data.shape[0], dtype=np.uint32)

        self.vertices = np.array(data, dtype=np.float32)
        self.indices  = indices

        self.__loBounds = self.vertices.min(axis=0)
        self.__hiBounds = self.vertices.max(axis=0)


    def __repr__(self):
        """Rewturns a string representation of this ``Model`` instance. """
        return '{}({}, {})'.format(type(self).__name__,
                                   self.name,
                                   self.dataSource)

    def __str__(self):
        """Rewturns a string representation of this ``Model`` instance. """
        return self.__repr__()


    def getBounds(self):
        """Returns a tuple of values which define a minimal bounding box that
        will contain all vertices in this ``Model`` instance. The bounding
        box is arranged like so:

            ``((xlow, ylow, zlow), (xhigh, yhigh, zhigh))``
        """
        return (self.__loBounds, self.__hiBounds)


ALLOWED_EXTENSIONS     = ['.vtk']
"""A list of file extensions which could contain :class:`Model` data. """


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
        vertices[i, :] = map(float, vertLine.split())

    indexOffset = 0
    for i in range(nPolygons):

        polyLine          = lines[6 + nVertices + i].split()
        polygonLengths[i] = int(polyLine[0])

        start              = indexOffset
        end                = indexOffset + polygonLengths[i]
        indices[start:end] = map(int, polyLine[1:])

        indexOffset        += polygonLengths[i]

    return vertices, polygonLengths, indices
