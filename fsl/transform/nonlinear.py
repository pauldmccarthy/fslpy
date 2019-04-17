#!/usr/bin/env python
#
# nonlinear.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import numpy as np

import fsl.data.image as fslimage

from . import affine


class NonLinearTransform(fslimage.Image):
    """Class which represents a FNIRT non-linear transformation
    """

    def __init__(self, *args, **kwargs):
        """
        """
        src      = kwargs.pop('src',       None)
        ref      = kwargs.pop('ref',       None)
        srcSpace = kwargs.pop('srceSpace', 'fsl')
        refSpace = kwargs.pop('refSpace',  'fsl')

        fslimage.Image.__init__(self, *args, **kwargs)

        if src is not None: src = src .header.copy()
        if ref is not None: ref = ref .header.copy()
        else:               ref = self.header.copy()

        self.__src      = src
        self.__ref      = ref
        self.__srcSpace = srcSpace
        self.__refSpace = refSpace


    @property
    def src(self):
        return self.__src


    @property
    def ref(self):
        return self.__ref


    @property
    def srcSpace(self):
        return self.__srcSpace


    @property
    def refSpace(self):
        return self.__refSpace


class DisplacementField(NonLinearTransform):
    """Class which represents a FNIRT displacement field which, at each voxel,
    contains an absolute or relative displacement from a source space to a
    reference space.
    """

    def __init__(self, *args, **kwargs):
        """
        """

        dispType = kwargs.pop('dispType',  None)

        NonLinearTransform.__init__(self, *args, **kwargs)

        self.__dispType = dispType


    @property
    def displacementType(self):
        if self.__dispType is None:
            self.__dispType = detectDisplacementType(self)
        return self.__dispType


    @property
    def absolute(self):
        return self.displacementType == 'absolute'


    @property
    def relative(self):
        return self.displacementType == 'relative'



def detectDisplacementType(field):
    """Attempt to automatically determine whether a displacement field is
    specified in absolute or relative coordinates.

    :arg field: A :class:`DisplacementField`

    :returns:   ``'absolute'`` if it looks like ``field`` contains absolute
                displacements, ``'relative'`` otherwise.
    """

    # This test is based on the assumption
    # that a displacement field containing
    # absolute oordinates will have a greater
    # standard deviation than one which
    # contains relative coordinates.
    absdata = field[:]
    reldata = convertDisplacementType(field, 'relative')
    stdabs  = absdata.std(axis=(0, 1, 2)).sum()
    stdrel  = reldata.std(axis=(0, 1, 2)).sum()

    if stdabs > stdrel: return 'absolute'
    else:               return 'relative'


def convertDisplacementType(field, dispType=None):
    """Convert a displacement field between storing absolute and relative
    displacements.
    """

    if dispType is None:
        if field.displacementType == 'absolute': dispType = 'relative'
        else:                                    dispType = 'absolute'

    # Regardless of the conversion direction,
    # we need the coordinates of every voxel
    # in the reference FSL coordinate system.
    dx, dy, dz = field.shape[:3]
    v2fsl      = field.getAffine('voxel', field.srcSpace)
    coords     = np.meshgrid(np.arange(dx),
                             np.arange(dy),
                             np.arange(dz), indexing='ij')
    coords     = np.array(coords).transpose((1, 2, 3, 0))
    coords     = affine.transform(coords.reshape((-1, 3)), v2fsl)
    coords     = coords.reshape((dx, dy, dz, 3))

    # If converting from relative to absolute,
    # we just add the voxel coordinates to
    # (what is assumed to be) the relative shift.
    # Or, to convert from absolute to relative,
    # we subtract the reference image voxels.
    if   dispType == 'absolute': return field.data + coords
    elif dispType == 'relative': return field.data - coords


def convertDisplacementSpace(field, src, from_, to, ref=None, dispType=None):
    """Adjust the source and/or reference spaces of the given displacement
    field.
    """

    if ref      is None: ref      = field
    if dispType is None: dispType = field.displacementType

    # Get the field in absolute
    # coordinates if necessary
    fieldcoords = field.data
    if field.relative: srccoords = convertDisplacementType(field)
    else:              srccoords = fieldcoords

    # Now transform those source
    # coordinates  from the original
    # source space to the source
    # space specified by "from_"
    srcmat    = src.getAffine(field.srcSpace, from_)
    srccoords = srccoords.reshape((-1, 3))
    srccoords = affine.transform(srccoords, srcmat)

    # If we have been asked to return
    # an absolute displacement, the
    # reference "to" coordinate system
    #  is irrelevant - we're done.
    if dispType == 'absolute':
        fieldcoords = srccoords

    # Otherwise our displacement field
    # will contain relative displacements
    # betwee the reference image "to"
    # coordinate system and the source
    # image "from_" coordinate system.
    # We need to re-calculate the relative
    # displacements from source "from_"
    # space into reference "to" space.
    else:
        refmat      = ref.getAffine(field.refSpace, to)
        refcoords   = fieldcoords.reshape((-1, 3))
        refcoords   = affine.transform(refcoords, refmat)
        fieldcoords = srccoords - refcoords

    return DisplacementField(
        fieldcoords.reshape(field.shape),
        header=field.header,
        src=src,
        ref=ref,
        srcSpace=from_,
        refSpace=to,
        dispType=dispType)
