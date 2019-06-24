#!/usr/bin/env python
#
# utils.py - Miscellaneous utility functions
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is home to some miscellaneous utility functions for working
with the data types defined in the :mod:`fsl.data` package.
"""


import os.path as op
import numpy   as np

def guessType(path):
    """A convenience function which, given the name of a file or directory,
    attempts to figure out a suitable data type.

    Returns a tuple containing two values - a type which should be able to
    load the path, and the path itself, possibly adjusted. If the type
    is unrecognised, the first tuple value will be ``None``.
    """

    import fsl.utils.path           as fslpath
    import fsl.data.image           as fslimage
    import fsl.data.vtk             as fslvtk
    import fsl.data.gifti           as fslgifti
    import fsl.data.freesurfer      as fslfs
    import fsl.data.mghimage        as fslmgh
    import fsl.data.bitmap          as fslbmp
    import fsl.data.featimage       as featimage
    import fsl.data.melodicimage    as melimage
    import fsl.data.dtifit          as dtifit
    import fsl.data.melodicanalysis as melanalysis
    import fsl.data.featanalysis    as featanalysis

    # Support files opened via fsleyes:// URL
    if path.startswith('fsleyes://'):
        path = path[10:]

    path = op.abspath(path)

    # Accept images sans-extension
    try:
        path = fslimage.addExt(path, mustExist=True)
    except fslimage.PathError:
        pass

    if op.isfile(path):

        # Some types are easy - just check the extensions
        if fslpath.hasExt(path.lower(), fslvtk.ALLOWED_EXTENSIONS):
            return fslvtk.VTKMesh, path
        elif fslpath.hasExt(path.lower(), fslgifti.ALLOWED_EXTENSIONS):
            return fslgifti.GiftiMesh, path
        elif fslfs.isGeometryFile(path):
            return fslfs.FreesurferMesh, path
        elif fslpath.hasExt(path.lower(), fslmgh.ALLOWED_EXTENSIONS):
            return fslmgh.MGHImage, path
        elif fslpath.hasExt(path.lower(), fslbmp.BITMAP_EXTENSIONS):
            return fslbmp.Bitmap, path

        # Other specialised image types
        elif melanalysis .isMelodicImage(path):
            return melimage.MelodicImage, path
        elif featanalysis.isFEATImage(   path):
            return featimage.FEATImage,   path
        elif fslimage.looksLikeImage(path):
            return fslimage.Image, path

    # Analysis directory?
    elif op.isdir(path):
        if melanalysis.isMelodicDir(path):
            return melimage.MelodicImage, path
        elif featanalysis.isFEATDir(path):
            return featimage.FEATImage, path
        elif dtifit.isDTIFitPath(path):
            return dtifit.DTIFitTensor, path

    # Otherwise, I don't
    # know what to do
    return None, path


def makeWriteable(array):
    """Updates the given ``numpy.array`` so that it is writeable. If this
    is not possible, a copy is created and returned.
    """
    try:
        # Versions of numpy prior to 1.16 will
        # happily mutate a bytes array, whcih
        # is supposed to be immutable. So if
        # is the case, let's force a copy.
        if isinstance(array.base, bytes):
            raise ValueError()

        # In versions of numpy 1.16 and newer,
        # setting the WRITEABLE flag on an
        # immutable array will cause a
        # ValueError to be raised
        array.flags['WRITEABLE'] = True

    except ValueError:
        array = np.array(array)
    return array
