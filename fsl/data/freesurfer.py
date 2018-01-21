#!/usr/bin/env python
#
# freesurfer.py - The FreesurferMesh class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FreesurferMesh` class, which can be
used for loading Freesurfer geometry and vertex data files.

The following functions are also available:

  .. autosummary::
     :nosignatures:

     loadFreesurferVertexFile
     relatedFiles
"""


import os.path as op
import            glob

import nibabel.freesurfer as nibfs

import fsl.utils.path    as fslpath
import fsl.data.mghimage as fslmgh
import fsl.data.mesh     as fslmesh


GEOMETRY_EXTENSIONS = ['.pial',
                       '.white',
                       '.sphere',
                       '.inflated',
                       '.orig',
                       '.mid']
"""File extensions which are interpreted as Freesurfer geometry files. """


EXTENSION_DESCRIPTIONS = [
    "Freesurfer surface",
    "Freesurfer surface",
    "Freesurfer surface",
    "Freesurfer surface",
    "Freesurfer surface",
    "Freesurfer surface"]
"""A description for each extension in :attr:`GEOMETRY_EXTENSIONS`. """


VERTEX_DATA_EXTENSIONS = ['.curv',
                          '.crv',
                          '.area',
                          '.thickness',
                          '.volume',
                          '.mgh',
                          '.mgz']
"""File extensions which are interpreted as Freesurfer vertex data files. """


class FreesurferMesh(fslmesh.Mesh):
    """The :class:`FreesurferMesh` class represents a triangle mesh
    loaded from a Freesurfer geometry file.
    """


    def __init__(self, filename, fixWinding=False, loadAll=False):
        """Load the given Freesurfer surface file using ``nibabel``.

        :arg infile:     A Freesurfer geometry file  (e.g. ``*.pial``).

        :arg fixWinding: Passed through to the :meth:`addVertices` method
                         for the first vertex set.

        :arg loadAll:    If ``True``, the ``infile`` directory is scanned
                         for other freesurfer surface files which are then
                         loaded as additional vertex sets.
        """

        vertices, indices, meta, comment = nibfs.read_geometry(
            filename,
            read_metadata=True,
            read_stamp=True)

        filename = op.abspath(filename)
        name     = fslpath.removeExt(op.basename(filename),
                                     GEOMETRY_EXTENSIONS)

        fslmesh.Mesh.__init__(self,
                              indices,
                              name=name,
                              dataSource=filename)

        self.addVertices(vertices, filename, fixWinding=fixWinding)

        self.setMeta('comment', comment)
        for k, v in meta.items():
            self.setMeta(k, v)

        if loadAll:

            allFiles = relatedFiles(filename, ftypes=GEOMETRY_EXTENSIONS)

            for f in allFiles:
                verts, idxs = nibfs.read_geometry(f)
                self.addVertices(verts, f, select=False)


    def loadVertexData(self, infile, key=None):
        """Overrides :meth:`.Mesh.loadVertexData`. If the given ``infile``
        looks like a Freesurfer file, it is loaded via the
        :func:`loadFreesurferVertexFile` function. Otherwise, it is passed
        through to the base-class function.
        """

        if not fslpath.hasExt(infile, VERTEX_DATA_EXTENSIONS):
            return fslmesh.loadVertexData(infile, key)

        infile = op.abspath(infile)

        if key is None:
            key = infile

        vdata = loadFreesurferVertexFile(infile)

        self.addVertexData(key, vdata)

        return vdata


def loadFreesurferVertexFile(infile):
    """Loads the given Freesurfer file, assumed to contain vertex-wise data.
    """

    # morphometry file
    morphexts = ['.curv', '.crv', '.area', '.thickness', '.volume']

    if fslpath.hasExt(infile, morphexts):
        vdata = nibfs.read_morph_data(infile)

    # MGH image file
    elif fslpath.hasExt(infile, fslmgh.ALLOWED_EXTENSIONS):
        vdata = fslmgh.MGHImage(infile)[:].squeeze()

    return vdata


def relatedFiles(fname, ftypes=None):
    """Returns a list of all files which (look like they) are related to the
    given freesurfer file.
    """

    if ftypes is None:
        ftypes = VERTEX_DATA_EXTENSIONS

    #
    # .annot files contain labels for each vertex, and RGB values for each
    #  label
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

    prefix  = op.splitext(fname)[0]
    related = []

    for ftype in ftypes:
        related += list(glob.glob('{}{}'.format(prefix, ftype)))

    return [r for r in related if r != fname]
