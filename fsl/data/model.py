#!/usr/bin/env python
#
# model.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import numpy   as np


def loadVTKPolydataFile(infile):
    
    lines = None

    with open(infile, 'rt') as f:
        lines = f.readlines()

    lines = [l.strip() for l in lines]

    if lines[3] != 'DATASET POLYDATA':
        raise ValueError('')
    
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
    

class Model(object):

    def __init__(self, data, indices=None):
        """
        """

        if isinstance(data, str):
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


    def getBounds(self):
        return (self.vertices.min(axis=0),
                self.vertices.max(axis=0))
