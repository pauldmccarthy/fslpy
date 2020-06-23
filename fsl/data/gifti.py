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
     prepareGiftiVertexData
     relatedFiles
"""


import            glob
import            re
import os.path as op

import numpy   as np
import nibabel as nib

import fsl.utils.path     as fslpath
import fsl.utils.bids     as bids
import fsl.data.constants as constants
import fsl.data.mesh      as fslmesh


ALLOWED_EXTENSIONS = ['.surf.gii', '.gii']
"""List of file extensions that a file containing Gifti surface data
is expected to have.
"""


EXTENSION_DESCRIPTIONS = ['GIFTI surface file', 'GIFTI file']
"""A description for each of the :data:`ALLOWED_EXTENSIONS`. """


VERTEX_DATA_EXTENSIONS = ['.func.gii',
                          '.shape.gii',
                          '.label.gii',
                          '.time.gii']
"""File suffixes which are interpreted as GIFTI vertex data files,
containing data values for every vertex in the mesh.
"""


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

        If the file contains more than one set of vertices, the additional
        ones are added with keys of the form ``infile_i``, where ``infile`` is
        the absolute path to the file, and ``i`` is an index number, starting
        from 1. See the :meth:`.addVertices` method.

        :arg infile:     A GIFTI file (``*.gii``) which contains a surface
                         definition.

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

        surfimg, indices, vertices, vdata = loadGiftiMesh(infile)

        fslmesh.Mesh.__init__(self,
                              indices,
                              name=name,
                              dataSource=infile)

        for i, v in enumerate(vertices):
            if i == 0: key = infile
            else:      key = '{}_{}'.format(infile, i)
            self.addVertices(v, key, select=(i == 0), fixWinding=fixWinding)
        self.setMeta(infile, surfimg)

        if vdata is not None:
            self.addVertexData(infile, vdata)

        # Find and load all other
        # surfaces in the same directory
        # as the specfiied one.
        if loadAll:

            # Only attempt to auto-load sensibly
            # named gifti files (i.e. *.surf.gii,
            # rather than *.gii).
            surfFiles = relatedFiles(infile, [ALLOWED_EXTENSIONS[0]])
            nvertices = vertices[0].shape[0]

            for sfile in surfFiles:

                try:
                    surfimg, _, vertices, _ = loadGiftiMesh(sfile)
                except Exception:
                    continue

                if vertices[0].shape[0] != nvertices:
                    continue

                self.addVertices(vertices[0], sfile, select=False)
                self.setMeta(sfile, surfimg)


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

        surfimg, _, vertices, _ = loadGiftiMesh(infile)

        for i, v in enumerate(vertices):
            if i == 0: key = infile
            else:      key = '{}_{}'.format(infile, i)
            vertices[i] = self.addVertices(v, key, *args, **kwargs)

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

      - one comprising ``NIFTI_INTENT_TRIANGLE`` data (vertex indices
        defining the triangles).
      - one or more comprising ``NIFTI_INTENT_POINTSET`` data (the surface
        vertices)

    A ``ValueError`` will be raised if this is not the case.

    :arg filename: Name of a GIFTI file containing surface data.

    :returns:     A tuple containing these values:

                   - The loaded ``nibabel.gifti.GiftiImage`` instance

                   - A ``(M, 3)`` array containing the vertex indices for
                     ``M`` triangles.

                   - A list of at least one ``(N, 3)`` arrays containing ``N``
                     vertices.

                   - A ``(M, N)`` numpy array containing ``N`` data points for
                     ``M`` vertices, or ``None`` if the file does not contain
                     any vertex data.
    """

    gimg = nib.load(filename)

    pscode  = constants.NIFTI_INTENT_POINTSET
    tricode = constants.NIFTI_INTENT_TRIANGLE

    pointsets = [d for d in gimg.darrays if d.intent == pscode]
    triangles = [d for d in gimg.darrays if d.intent == tricode]
    vdata     = [d for d in gimg.darrays if d.intent not in (pscode, tricode)]

    if len(triangles) != 1:
        raise ValueError('{}: GIFTI surface files must contain '
                         'exactly one triangle array'.format(filename))

    if len(pointsets) == 0:
        raise ValueError('{}: GIFTI surface files must contain '
                         'at least one pointset array'.format(filename))

    vertices = [ps.data for ps in pointsets]
    indices  = triangles[0].data

    if len(vdata) == 0: vdata = None
    else:               vdata = prepareGiftiVertexData(vdata, filename)

    return gimg, indices, vertices, vdata


def loadGiftiVertexData(filename):
    """Loads vertex data from the given GIFTI file.

    See :func:`prepareGiftiVertexData`.

    Returns a tuple containing:

      - The loaded ``nibabel.gifti.GiftiImage`` object

      - A ``(M, N)`` numpy array containing ``N`` data points for ``M``
        vertices
    """
    gimg = nib.load(filename)
    return gimg, prepareGiftiVertexData(gimg.darrays, filename)


def prepareGiftiVertexData(darrays, filename=None):
    """Prepares vertex data from the given list of GIFTI data arrays.

    All of the data arrays are concatenated into one ``(M, N)`` array,
    containing ``N`` data points for ``M`` vertices.

    It is assumed that the given file does not contain any
    ``NIFTI_INTENT_POINTSET`` or ``NIFTI_INTENT_TRIANGLE`` data arrays, and
    which contains either:

      - One ``(M, N)`` data array containing ``N`` data points for ``M``
        vertices

      - One or more ``(M, 1)`` data arrays each containing a single data point
        for ``M`` vertices, and all with the same intent code

    Returns a ``(M, N)`` numpy array containing ``N`` data points for ``M``
    vertices.
    """

    intents = {d.intent for d in darrays}

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
    if len(darrays) == 1:
        vdata = darrays[0].data
        return vdata.reshape(vdata.shape[0], -1)

    # Otherwise extract and concatenate
    # multiple 1-dimensional arrays
    vdata = [d.data for d in darrays]

    if any([len(d.shape) != 1 for d in vdata]):
        raise ValueError('{} contains one or more non-vector '
                         'darrays'.format(filename))

    vdata = np.vstack(vdata).T
    vdata = vdata.reshape(vdata.shape[0], -1)

    return vdata


def relatedFiles(fname, ftypes=None):
    """Given a GIFTI file, returns a list of other GIFTI files in the same
    directory which appear to be related with the given one.  Files which
    share the same prefix are assumed to be related to the given file.

    This function assumes that the GIFTI files are named according to a
    standard convention - the following conventions are supported:

     - HCP-style, i.e.: ``<subject>.<hemi>.<type>.<space>.<ftype>.gii``
     - BIDS-style, i.e.:
       ``<source_prefix>_hemi-<hemi>[_space-<space>]*_<suffix>.<ftype>.gii``

    If the files are not named according to one of these conventions, this
    function will return an empty list.

    :arg fname: Name of the file to search for related files for

    :arg ftype: If provided, only files with suffixes in this list are
                searched for. Defaults to :attr:`VERTEX_DATA_EXTENSIONS`.
    """

    if ftypes is None:
        ftypes = VERTEX_DATA_EXTENSIONS

    path           = op.abspath(fname)
    dirname, fname = op.split(path)

    # We want to identify all files in the same
    # directory which are associated with the
    # given file. We assume that the files are
    # named according to one of the following
    # conventions:
    #
    #  - HCP style:
    #      <subject>.<hemi>.<type>.<space>.<ftype>.gii
    #
    #  - BIDS style:
    #      <source_prefix>_hemi-<hemi>[_space-<space>]*.<ftype>.gii
    #
    # We cannot assume consistent ordering of
    # the entities (key-value pairs) within a
    # BIDS style filename, so we cannot simply
    # use a regular expression or glob pattern.
    # Instead, for each style we define:
    #
    #  - a "matcher" function, which tests
    #    whether the file matches the style,
    #    and returns the important elements
    #    from the file name.
    #
    #  - a "searcher" function, which takes
    #    the elements of the input file
    #    that were extracted by the matcher,
    #    and searches for other related files

    # HCP style - extract "<subject>.<hemi>"
    # and "<space>".
    def matchhcp(f):
        pat   = r'^(.*\.[LR])\..*\.(.*)\..*\.gii$'
        match = re.match(pat, f)
        if match:
            return match.groups()
        else:
            return None

    def searchhcp(match, ftype):
        prefix, space = match
        template      = '{}.*.{}{}'.format(prefix, space, ftype)
        return glob.glob(op.join(dirname, template))

    # BIDS style - extract all entities (kv
    # pairs), ignoring specific irrelevant
    # ones.
    def matchbids(f):
        try:               match = bids.BIDSFile(f)
        except ValueError: return None
        match.entities.pop('desc', None)
        return match

    def searchbids(match, ftype):
        allfiles = glob.glob(op.join(dirname, '*{}'.format(ftype)))
        for f in allfiles:
            try:               bf = bids.BIDSFile(f)
            except ValueError: continue
            if bf.match(match, False):
                yield f

    # find the first style that matches
    matchers  = [matchhcp,  matchbids]
    searchers = [searchhcp, searchbids]
    for matcher, searcher in zip(matchers, searchers):
        match = matcher(fname)
        if match:
            break

    # Give up if the file does
    # not match any known style.
    else:
        return []

    # Build a list of files in the same
    # directory and matching the template
    related = []
    for ftype in ftypes:

        hits = searcher(match, ftype)

        # eliminate dupes
        related.extend([h for h in hits if h not in related])

    # exclude the file itself
    return [r for r in related if r != path]
