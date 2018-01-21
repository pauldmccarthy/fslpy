#!/usr/bin/env python
#
# freesurfer.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""


import os.path as op

import nibabel as nib

import fsl.utils.path as fslpath
import fsl.data.mesh  as fslmesh


class FreesurferMesh(fslmesh.TriangleMesh):
    """
    """

    def __init__(self, filename):
        """
        """

        vertices, indices, meta, comment = nib.freesurfer.read_geometry(
            filename,
            read_metadata=True,
            read_stamp=True)

        fslmesh.TriangleMesh.__init__(self, vertices, indices)

        self.dataSource = op.abspath(filename)
        self.name       = fslpath.removeExt(op.basename(filename),
                                            ALLOWED_EXTENSIONS)



    def loadVertexData(self, dataSource, vertexData=None):
        pass



ALLOWED_EXTENSIONS = ['.pial',
                      '.white',
                       '.sphere',
                      '.inflated',
                      '.orig',
                      '.sulc',
                      '.mid' ]
EXTENSION_DESCRIPTIONS = [
]


def relatedFiles(fname):
    """
    """

    #
    # .annot files contain labels for each vertex, and RGB values for each label
    #    -> nib.freesurfer.read_annot
    #
    # .label files contain scalar labels associated with each vertex
    #    -> read_label
    #
    # .curv files contain vertex data
    #    -> nib.freesurfer.read_morph_data
    #
    # .w files contain vertex data (potentially for a subset of vertices)
    #    -> ?
    pass
