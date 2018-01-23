#!/usr/bin/env python
#
# gifti.py - GIFTI file support.
#
# Author: Paul McCarthy  <pauldmccarthy@gmail.com>
#         Michiel Cottar <michiel.cottaar@ndcn.ox.ac.uk>
#
"""This class provides classes and functions for working with GIFTI files.

The GIFTI file format specification can be found at
http://www.nitrc.org/projects/gifti/

Support is currently very basic - only the following classes/functions
are available:

  .. autosummary::
     :nosignatures:

     GiftiMesh
     loadGiftiMesh
     loadGiftiVertexData
     relatedFiles
"""


import            glob
import os.path as op
import            deprecation

import numpy   as np
import nibabel as nib

import fsl.utils.path     as fslpath
import fsl.data.constants as constants
import fsl.data.mesh      as fslmesh


ALLOWED_EXTENSIONS = ['.surf.gii']
"""List of file extensions that a file containing Gifti surface data
is expected to have.
"""


EXTENSION_DESCRIPTIONS = ['GIFTI surface file']
"""A description for each of the :data:`ALLOWED_EXTENSIONS`. """


class GiftiMesh(fslmesh.Mesh):
    """Class which represents a GIFTI surface image. This is essentially
    just a 3D model made of triangles.

    For each GIFTI surface file that is loaded, the
    ``nibabel.gifti.GiftiImage`` instance is stored in the :class:`.Meta`
    store, with the absolute path to the surface file as the key.
    """


    def __init__(self, infile, fixWinding=False, loadAll=False):
        """Load the given GIFTI file using ``nibabel``, and extracts surface
        data using the  :func:`loadGiftiMesh` function.

        :arg infile:     A GIFTI surface file (``*.surf.gii``).

        :arg fixWinding: Passed through to the :meth:`addVertices` method
                         for the first vertex set.

        :arg loadAll:    If ``True``, the ``infile`` directory is scanned
                         for other surface files which are then loaded
                         as additional vertex sets.

        .. todo:: Allow loading from a ``.topo.gii`` and ``.coord.gii`` file?
                  Maybe.
        """

        name   = fslpath.removeExt(op.basename(infile), ALLOWED_EXTENSIONS)
        infile = op.abspath(infile)

        surfimg, vertices, indices = loadGiftiMesh(infile)


        fslmesh.Mesh.__init__(self,
                              indices,
                              name=name,
                              dataSource=infile)

        self.addVertices(vertices, infile, fixWinding=fixWinding)
        self.setMeta(infile, surfimg)

        # Find and load all other
        # surfaces in the same directory
        # as the specfiied one.
        if loadAll:

            nvertices = vertices.shape[0]
            surfFiles = relatedFiles(infile, ALLOWED_EXTENSIONS)

            for sfile in surfFiles:

                surfimg, vertices, _ = loadGiftiMesh(sfile)

                if vertices.shape[0] != nvertices:
                    continue

                self.addVertices(vertices, sfile, select=False)
                self.setMeta(    sfile, surfimg)


    def loadVertices(self, infile, key=None, *args, **kwargs):
        """Overrides the :meth:`.Mesh.loadVertices` method.

        Attempts to load vertices for this ``GiftiMesh`` from the given
        ``infile``, which may be a GIFTI file or a plain text file containing
        vertices.
        """

        if not infile.endswith('.gii'):
            return fslmesh.Mesh.loadVertices(
                self, infile, key, *args, **kwargs)

        infile = op.abspath(infile)

        if key is None:
            key = infile

        surfimg, vertices, _ = loadGiftiMesh(infile)

        vertices = self.addVertices(vertices, key, *args, **kwargs)

        self.setMeta(infile, surfimg)

        return vertices


    def loadVertexData(self, infile, key=None):
        """Overrides the :meth:`.Mesh.loadVertexData` method.

        Attempts to load data associated with each vertex of this
        ``GiftiMesh`` from the given ``infile``, which may be a GIFTI file or
        a plain text file which contains vertex data.
        """

        if not infile.endswith('.gii'):
            return fslmesh.Mesh.loadVertexData(self, infile)

        infile = op.abspath(infile)

        if key is None:
            key = infile

        vdata = loadGiftiVertexData(infile)[1]
        return self.addVertexData(key, vdata)


def loadGiftiMesh(filename):
    """Extracts surface data from the given ``nibabel.gifti.GiftiImage``.

    The image is expected to contain the following``<DataArray>`` elements:

      - one comprising ``NIFTI_INTENT_POINTSET`` data (the surface vertices)
      - one comprising ``NIFTI_INTENT_TRIANGLE`` data (vertex indices
        defining the triangles).

    A ``ValueError`` will be raised if this is not the case.

    :arg filename: Name of a GIFTI file containing surface data.

    :returns:     A tuple containing these values:

                   - The loaded ``nibabel.gifti.GiftiImage`` instance

                   - A ``(N, 3)`` array containing ``N`` vertices.

                   - A ``(M, 3))`` array containing the vertex indices for
                     ``M`` triangles.
    """

    gimg = nib.load(filename)

    pointsetCode = constants.NIFTI_INTENT_POINTSET
    triangleCode = constants.NIFTI_INTENT_TRIANGLE

    pointsets = [d for d in gimg.darrays if d.intent == pointsetCode]
    triangles = [d for d in gimg.darrays if d.intent == triangleCode]

    if len(gimg.darrays) != 2:
        raise ValueError('{}: GIFTI surface files must contain '
                         'exactly one pointset array and one '
                         'triangle array'.format(filename))

    if len(pointsets) != 1:
        raise ValueError('{}: GIFTI surface files must contain '
                         'exactly one pointset array'.format(filename))

    if len(triangles) != 1:
        raise ValueError('{}: GIFTI surface files must contain '
                         'exactly one triangle array'.format(filename))

    vertices = pointsets[0].data
    indices  = triangles[0].data

    return gimg, vertices, indices


def loadGiftiVertexData(filename):
    """Loads vertex data from the given GIFTI file.

    It is assumed that the given file does not contain any
    ``NIFTI_INTENT_POINTSET`` or ``NIFTI_INTENT_TRIANGLE`` data arrays, and
    which contains either:

      - One ``(M, N)`` data array containing ``N`` data points for ``M``
        vertices

      - One or more ``(M, 1)`` data arrays each containing a single data point
        for ``M`` vertices, and all with the same intent code

    Returns a tuple containing:

      - The loaded ``nibabel.gifti.GiftiImage`` object

      - A ``(M, N)`` numpy array containing ``N`` data points for ``M``
        vertices
    """

    gimg = nib.load(filename)

    intents = set([d.intent for d in gimg.darrays])

    if len(intents) != 1:
        raise ValueError('{} contains multiple (or no) intents'
                         ': {}'.format(filename, intents))

    intent = intents.pop()

    if intent in (constants.NIFTI_INTENT_POINTSET,
                  constants.NIFTI_INTENT_TRIANGLE):

        raise ValueError('{} contains surface data'.format(filename))

    # Just a single array - return it as-is.
    # n.b. Storing (M, N) data in a single
    # DataArray goes against the GIFTI spec,
    # but hey, it happens.
    if len(gimg.darrays) == 1:
        vdata = gimg.darrays[0].data
        return gimg, vdata.reshape(vdata.shape[0], -1)

    # Otherwise extract and concatenate
    # multiple 1-dimensional arrays
    vdata = [d.data for d in gimg.darrays]

    if any([len(d.shape) != 1 for d in vdata]):
        raise ValueError('{} contains one or more non-vector '
                         'darrays'.format(filename))

    vdata = np.vstack(vdata).T
    vdata = vdata.reshape(vdata.shape[0], -1)

    return gimg, vdata


def relatedFiles(fname, ftypes=None):
    """Given a GIFTI file, returns a list of other GIFTI files in the same
    directory which appear to be related with the given one.  Files which
    share the same prefix are assumed to be related to the given file.

    :arg fname: Name of the file to search for related files for

    :arg ftype: If provided, only files with suffixes in this list are
                searched for. Defaults to files which contain vertex data.
    """

    if ftypes is None:
        ftypes = ['.func.gii', '.shape.gii', '.label.gii', '.time.gii']

    # We want to return all files in the same
    # directory which have the following name:

    #
    # [subj].[hemi].[type].*.[ftype]
    #

    #   where
    #     - [subj] is the subject ID, and matches fname
    #
    #     - [hemi] is the hemisphere, and matches fname
    #
    #     - [type] defines the file contents
    #
    #     - suffix is func, shape, label, time, or `ftype`

    path            = op.abspath(fname)
    dirname, fname  = op.split(path)

    # get the [subj].[hemi] prefix
    try:
        subj, hemi, _ = fname.split('.', 2)
        prefix        = '.'.join((subj, hemi))
    except Exception:
        return []

    related = []

    for ftype in ftypes:
        related.extend(
            glob.glob(op.join(dirname, '{}*{}'.format(prefix, ftype))))

    return [r for r in related if r != path]


class GiftiSurface(fslmesh.TriangleMesh):
    """Deprecated - use GiftiMesh instead. """


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use GiftiMesh instead')
    def __init__(self, infile, fixWinding=False):
        """Deprecated - use GiftiMesh instead. """
        surfimg, vertices, indices = loadGiftiSurface(infile)

        fslmesh.TriangleMesh.__init__(self, vertices, indices, fixWinding)

        name   = fslpath.removeExt(op.basename(infile), ALLOWED_EXTENSIONS)
        infile = op.abspath(infile)

        self._Mesh__name       = name
        self._Mesh__dataSource = infile
        self.surfImg           = surfimg


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use GiftiMesh instead')
    def loadVertexData(self, dataSource, vertexData=None):
        """Deprecated - use GiftiMesh instead. """

        if vertexData is None:
            if dataSource.endswith('.gii'):
                vertexData = loadGiftiVertexData(dataSource)[1]
            else:
                vertexData = None

        return fslmesh.TriangleMesh.loadVertexData(
            self, dataSource, vertexData)


@deprecation.deprecated(deprecated_in='1.6.0',
                        removed_in='2.0.0',
                        details='Use loadGiftiMesh instead')
def loadGiftiSurface(filename):
    """Deprecated - use loadGiftiMesh instead."""
    return loadGiftiMesh(filename)
