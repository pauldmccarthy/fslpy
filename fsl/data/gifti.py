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
     extractGiftiSurface
"""


import os.path as op

import fsl.utils.path as fslpath
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
        data using the  :func:`extractGiftiSurface` function.

        :arg infile: A GIFTI surface file
        """

        import nibabel as nib

        surfimg           = nib.load(infile)
        vertices, indices = extractGiftiSurface(surfimg)

        mesh.TriangleMesh.__init__(self, vertices, indices)

        name   = fslpath.removeExt(op.basename(infile), ALLOWED_EXTENSIONS)
        infile = op.abspath(infile)

        self.name       = name
        self.dataSource = infile
        self.surfImg    = surfimg


ALLOWED_EXTENSIONS = ['.surf.gii', '.gii']
"""List of file extensions that a file containing Gifti surface data
is expected to have.
"""


EXTENSION_DESCRIPTIONS = ['GIFTI surface file', 'GIFTI surface file']
"""A description for each of the :data:`ALLOWED_EXTENSIONS`.
"""


def extractGiftiSurface(surfimg):
    """Extracts surface data from the given ``nibabel.gifti.GiftiImage``.

    The image is expected to contain the following``<DataArray>`` elements:

      - one comprising ``NIFTI_INTENT_POINTSET`` data (the surface vertices)
      - one comprising ``NIFTI_INTENT_TRIANGLE`` data (vertex indices
        defining the triangles).

    A ``ValueError`` will be raised if this is not the case.

    :arg surfimg: A ``GiftiImage`` containing surface data.

    :returns:     A tuple containing these values:

                   - A :math:`N\\times 3` ``numpy`` array containing :math:`N`
                     vertices.
    
                   - A :math:`M\\times 3` ``numpy`` array containing the 
                     vertex indices for :math:`M` triangles.
    """

    from nibabel import gifti

    codes    = gifti.gifti.intent_codes.code
    
    indices  = None
    vertices = None
    
    for darray in surfimg.darrays:
        
        if darray.intent == codes['pointset']:
            
            if vertices is not None:
                raise ValueError('multiple arrays with intent "{}"'.format(
                    darray.intent))
            
            vertices = darray.data
            
        elif darray.intent == codes['triangle']:
            if indices is not None:
                raise ValueError('multiple arrays with intent "{}"'.format(
                    darray.intent))
            
            indices = darray.data
            
    if vertices is None:
        raise ValueError('no array with intent "pointset" found')
    
    if indices is None:
        raise ValueError('no array witbh intent "triangle"found')
    
    return vertices, indices
