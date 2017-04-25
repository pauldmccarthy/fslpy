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

     GiftiSurface
     loadGiftiSurface
     relatedFiles
"""


import            glob
import os.path as op

import numpy   as np
import nibabel as nib

import fsl.utils.path as fslpath
from . import            constants
from . import            mesh


class GiftiSurface(mesh.TriangleMesh):
    """Class which represents a GIFTI surface image. This is essentially
    just a 3D model made of triangles.

    In addition to the ``vertices`` and ``indices`` provided by the
    :class:`.TriangleMesh` class (from which the ``GiftiSurface`` class
    derives), a ``GiftiSurface`` instance has the following attributes:

    ============== ====================================================
    ``name``       A name, typically the file name sans-suffix.
    ``dataSource`` Full path to the GIFTI file.
    ``surfImg``    Reference to the loaded ``nibabel.gifti.GiftiImage``
    ============== ====================================================
    """


    def __init__(self, infile):
        """Load the given GIFTI file using ``nibabel``, and extracts surface
        data using the  :func:`loadGiftiSurface` function.

        :arg infile: A GIFTI surface file (``*.surf.gii``).

        .. todo:: Allow loading from a ``.topo.gii`` and ``.coord.gii`` file?
                  Maybe.
        """

        surfimg, vertices, indices = loadGiftiSurface(infile)

        mesh.TriangleMesh.__init__(self, vertices, indices)

        name   = fslpath.removeExt(op.basename(infile), ALLOWED_EXTENSIONS)
        infile = op.abspath(infile)

        self.name       = name
        self.dataSource = infile
        self.surfImg    = surfimg


    def loadVertexData(self, dataSource, vertexData=None):
        """Overrides the :meth:`.TriangleMesh.loadVertexData` method.

        Attempts to load data associated with each vertex of this
        ``GiftiSurface`` from the given ``dataSource``, which may be
        a GIFTI file or a plain text file which contains vertex data.
        """

        if vertexData is None:
            if dataSource.endswith('.gii'):
                vertexData = loadGiftiVertexData(dataSource)[1]
            else:
                vertexData = None

        return mesh.TriangleMesh.loadVertexData(self, dataSource, vertexData)


ALLOWED_EXTENSIONS = ['.surf.gii', '.gii']
"""List of file extensions that a file containing Gifti surface data
is expected to have.
"""


EXTENSION_DESCRIPTIONS = ['GIFTI surface file', 'GIFTI surface file']
"""A description for each of the :data:`ALLOWED_EXTENSIONS`.
"""


def loadGiftiSurface(filename):
    """Extracts surface data from the given ``nibabel.gifti.GiftiImage``.

    The image is expected to contain the following``<DataArray>`` elements:

      - one comprising ``NIFTI_INTENT_POINTSET`` data (the surface vertices)
      - one comprising ``NIFTI_INTENT_TRIANGLE`` data (vertex indices
        defining the triangles).

    A ``ValueError`` will be raised if this is not the case.

    :arg filename: Name of a GIFTI file containing surface data.

    :returns:     A tuple containing these values:

                   - The loaded ``nibabel.gifti.GiftiImage`` instance

                   - A :math:`N\\times 3` ``numpy`` array containing :math:`N`
                     vertices.

                   - A :math:`M\\times 3` ``numpy`` array containing the
                     vertex indices for :math:`M` triangles.
    """

    gimg = nib.load(filename)

    pointsetCode = constants.NIFTI_INTENT_POINTSET
    triangleCode = constants.NIFTI_INTENT_TRIANGLE

    pointsets = [d for d in gimg.darrays if d.intent == pointsetCode]
    triangles = [d for d in gimg.darrays if d.intent == triangleCode]

    if len(gimg.darrays) != 2:
        raise ValueError('GIFTI surface files must contain exactly '
                         'one pointset array and one triangle array')

    if len(pointsets) != 1:
        raise ValueError('GIFTI surface files must contain '
                         'exactly one pointset array')

    if len(triangles) != 1:
        raise ValueError('GIFTI surface files must contain '
                         'exactly one triangle array')

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
        return gimg, gimg.darrays[0].data

    # Otherwise extract and concatenate
    # multiple 1-dimensional arrays
    vdata = [d.data for d in gimg.darrays]

    if any([len(d.shape) != 1 for d in vdata]):
        raise ValueError('{} contains one or more non-vector '
                         'darrays'.format(filename))

    return gimg, np.vstack(vdata).T


def relatedFiles(fname):
    """Given a GIFTI file, returns a list of other GIFTI files in the same
    directory which appear to be related with the given one.  Files which
    share the same prefix are assumed to be related to the given file.
    """

    # We want to return all files in the same
    # directory which have the following name:

    #
    # [prefix].*.[type].gii
    #
    #   where
    #     - prefix is the file prefix, and which
    #       may include periods.
    #
    #     - we don't care about the middle
    #
    #     - type is func, shape, label, or time

    # We determine the unique prefix of the
    # given file, and back-up to the most
    # recent period. Then search for other
    # files which have that same (non-unique)
    # prefix.
    prefix  = fslpath.uniquePrefix(fname)
    lastdot = prefix.rfind('.')
    prefix  = prefix[:lastdot]

    if lastdot == -1:
        return []

    funcs  = list(glob.glob('{}*.func.gii' .format(prefix)))
    shapes = list(glob.glob('{}*.shape.gii'.format(prefix)))
    labels = list(glob.glob('{}*.label.gii'.format(prefix)))
    times  = list(glob.glob('{}*.time.gii' .format(prefix)))

    return funcs + shapes + labels + times
