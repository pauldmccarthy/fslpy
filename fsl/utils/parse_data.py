#!/usr/bin/env python
#
# Support for neuroimage data in argparse
#
# Author: Michiel Cottaar <michiel.cottaar@ndcn.ox.ac.uk
#
"""This module contains support for neuroimaging data in argparse

Argparse is the built-in python library for resolving command line arguments.

The functions in this module can be passed on to the ``type`` argument in the
``ArgumentParser.add_command`` method to interpret command line arguments as
neuroimaging objects (.e.g, NIFTI image files)


.. autosummary::
   :nosignatures:

    Image
    ImageOut
    Mesh
    Atlas
"""


from fsl.data import image, gifti, vtk, atlases
from fsl.utils import path
import argparse


def Image(filename, *args, **kwargs):
    """
    Reads in an image from a NIFTI or Analyze file.

    :arg filename: filename provided by the user
    :return: fsl.data.image.Image object

    All other arguments are passed through to the :class:`.Image` upon
    creation.
    """
    try:
        full_filename = image.addExt(filename)
    except path.PathError as e:
        raise argparse.ArgumentTypeError(*e.args)
    return image.Image(full_filename, *args, **kwargs)


def ImageOut(basename):
    """
    Uses the FSL convention to create a complete image output filename

    :param basename: filename provided by the user
    :return: filename with extension
    """
    return image.addExt(basename, mustExist=False)


def Mesh(filename):
    """
    Reads in a mesh from either a GIFTI (.surf.gii) or a VTK (.vtk) file

    :param filename: filename provided by the user
    :return: GIFTI or VTK sub-class of fsl.data.mesh.Mesh
    """
    try:
        full_filename = path.addExt(filename, ['.surf.gii', '.vtk'])
    except path.PathError as e:
        raise argparse.ArgumentTypeError(*e.args)
    if path.hasExt(full_filename, '.surf.gii'):
        return gifti.GiftiMesh(full_filename)
    else:
        return vtk.VTKMesh(full_filename)


def Atlas(name):
    """
    Reads in the atlas from the FSL standard atlases

    :param name: name of the atlas
    :return: fsl.data.atlases.Atlas representation of an FSL atlas
    """
    atlases.rescanAtlases()
    if not atlases.hasAtlas(name):
        atlas_names = tuple(desc.atlasID for desc in atlases.listAtlases())
        raise argparse.ArgumentTypeError('Requested atlas %r not one of: %r' % (name, atlas_names))
    return atlases.loadAtlas(name)
