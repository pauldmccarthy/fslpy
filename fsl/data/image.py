#!/usr/bin/env python
#
# image.py - Provides the :class:`Image` class, for representing 3D/4D NIFTI
#            images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Nifti` and :class:`Image` classes, for
representing NIFTI1 and NIFTI2 images. The ``nibabel`` package is used
for file I/O.


It is very easy to load a NIFTI image::

    from fsl.data.image import Image
    myimg = Image('MNI152_T1_2mm.nii.gz')


A handful of other functions are also provided for working with image files
and file names:

.. autosummary::
   :nosignatures:

   canonicalShape
   looksLikeImage
   addExt
   splitExt
   getExt
   removeExt
   defaultExt
"""


import                    os
import os.path         as op
import itertools       as it
import collections.abc as abc
import                    json
import                    string
import                    logging
import                    tempfile

from pathlib import Path
from typing  import Union

import numpy             as np
import nibabel           as nib
import nibabel.fileslice as fileslice

import fsl.utils.meta        as meta
import fsl.utils.deprecated  as deprecated
import fsl.transform.affine  as affine
import fsl.utils.notifier    as notifier
import fsl.utils.naninfrange as nir
import fsl.utils.memoize     as memoize
import fsl.utils.path        as fslpath
import fsl.utils.bids        as fslbids
import fsl.data.constants    as constants


PathLike    = Union[str, Path]
ImageSource = Union[PathLike, nib.Nifti1Image, np.ndarray, 'Image']


log = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = ['.nii.gz', '.nii', '.img', '.hdr', '.img.gz', '.hdr.gz']
"""The file extensions which we understand. This list is used as the default
if the ``allowedExts`` parameter is not passed to any of the ``*Ext``
functions, or the :func:`looksLikeImage` function.
"""


EXTENSION_DESCRIPTIONS = ['Compressed NIFTI images',
                          'NIFTI images',
                          'ANALYZE75 images',
                          'NIFTI/ANALYZE75 headers',
                          'Compressed NIFTI/ANALYZE75 images',
                          'Compressed NIFTI/ANALYZE75 headers']
"""Descriptions for each of the extensions in :data:`ALLOWED_EXTENSIONS`. """


FILE_GROUPS = [('.hdr',    '.img'),
               ('.hdr.gz', '.img.gz')]
"""File suffix groups used by :func:`addExt` to resolve file path
ambiguities - see :func:`fsl.utils.path.addExt`.
"""


PathError = fslpath.PathError
"""Error raised by :mod:`fsl.utils.path` functions when an error occurs.
Made available in this module for convenience.
"""


class DataManager:
    """The ``DataManager`` defines an interface which may be used by
    :class:`Image` instances for managing access and modification of
    data in a ``nibabel.Nifti1Image`` image.
    """


    def copy(self, nibImage : nib.Nifti1Image):
        """Return a copy of this ``DataManager``, associated with the
        given ``nibImage``,
        """
        raise NotImplementedError()


    @property
    def dataRange(self):
        """Return the image minimum/maximum data values as a ``(min, max)``
        tuple.
        """
        raise NotImplementedError()


    @property
    def editable(self):
        """Return ``True`` if the image data can be modified, ``False``
        otherwise. The default implementation returns ``True``.
        """
        return True


    def __getitem__(self, slc):
        """Return data at ``slc``. """
        raise NotImplementedError()


    def __setitem__(self, slc, val):
        """Set data at ``slc`` to ``val``. """
        raise NotImplementedError()



class Nifti(notifier.Notifier, meta.Meta):
    """The ``Nifti`` class is intended to be used as a base class for
    things which either are, or are associated with, a NIFTI image.
    The ``Nifti`` class is intended to represent information stored in
    the header of a NIFTI file - if you want to load the data from
    a file, use the :class:`Image` class instead.


    When a ``Nifti`` instance is created, it adds the following attributes
    to itself:


    ================= ====================================================
    ``header``        The :mod:`nibabel` NIFTI1/NIFTI2/Analyze header
                      object.

    ``shape``         A list/tuple containing the number of voxels along
                      each image dimension.

    ``realShape``     A list/tuple containing the actual image data shape
                      - see notes below.

    ``pixdim``        A list/tuple containing the length of one voxel
                      along each image dimension.

    ``voxToWorldMat`` A 4*4 array specifying the affine transformation
                      for transforming voxel coordinates into real world
                      coordinates.

    ``worldToVoxMat`` A 4*4 array specifying the affine transformation
                      for transforming real world coordinates into voxel
                      coordinates.

    ``intent``        The NIFTI intent code specified in the header (or
                      :attr:`.constants.NIFTI_INTENT_NONE` for Analyze
                      images).
    ================= ====================================================


    The ``header`` field may either be a ``nifti1``, ``nifti2``, or
    ``analyze`` header object. Make sure to take this into account if you are
    writing code that should work with all three. Use the :meth:`niftiVersion`
    property if you need to know what type of image you are dealing with.


    **Image dimensionality**


    By default, the ``Nifti`` and ``Image`` classes "normalise" the
    dimensionality of an image to always have at least 3 dimensions, and so
    that trailing dimensions of length 1 are removed.  Therefore, the
    ``shape`` attribute may not precisely match the image shape as reported in
    the NIFTI header, because trailing dimensions of size 1 are squeezed
    out. The actual image data shape can be queried via the :meth:`realShape`
    property. Note also that the :class:`Image` class expects data
    access/slicing to be with respect to the normalised shape, not the real
    shape. See the :meth:`__determineShape` method and the
    :func:`canonicalSliceObj` function for more details.


    **Affine transformations**


    The ``Nifti`` class is aware of three coordinate systems:

      - The ``voxel`` coordinate system, used to access image data

      - The ``world`` coordinate system, where voxel coordinates are
        transformed into a millimetre coordinate system, defined by the
        ``sform`` and/or ``qform`` elements of the NIFTI header.

      - The ``fsl`` coordinate system, where voxel coordinates are scaled by
        the ``pixdim`` values in the NIFTI header, and the X axis is inverted
        if the voxel-to-world affine has a positive determinant.


    The :meth:`getAffine` method is a simple means of acquiring an affine
    which will transform between any of these coordinate systems.


    See `here <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the_format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to_the_transformation_parameters.3F>`_
    for more details on the ``fsl`` coordinate system.


    The ``Nifti`` class follows the same process as ``nibabel`` in determining
    the ``voxel`` to ``world`` affine (see
    http://nipy.org/nibabel/nifti_images.html#the-nifti-affines):


     1. If ``sform_code != 0`` ("unknown") use the sform affine; else
     2. If ``qform_code != 0`` ("unknown") use the qform affine; else
     3. Use the fall-back affine.


    However, the *fall-back* affine used by the ``Nifti`` class differs to
    that used by ``nibabel``. In ``nibabel``, the origin (world coordinates
    (0, 0, 0)) is set to the centre of the image. Here in the ``Nifti``
    class, we set the world coordinate orign to be the corner of the image,
    i.e. the corner of voxel (0, 0, 0).


    You may change the ``voxToWorldMat`` of a ``Nifti`` instance (unless it
    is an Analyze image). When you do so:

     - Only the ``sform`` of the underlying ``Nifti1Header`` object is changed

     - The ``qform`` is not modified.

     - If the ``sform_code`` was previously set to ``NIFTI_XFORM_UNKNOWN``,
       it is changed to ``NIFTI_XFORM_ALIGNED_ANAT``. Otherwise, the
       ``sform_code`` is not modified.


    **ANALYZE support**


    A ``Nifti`` instance expects to be passed either a
    ``nibabel.nifti1.Nifti1Header`` or a ``nibabel.nifti2.Nifti2Header``, but
    can also encapsulate a ``nibabel.analyze.AnalyzeHeader``. In this case:

      - The image voxel orientation is assumed to be R->L, P->A, I->S.

      - The affine will be set to a diagonal matrix with the header pixdims as
        its elements (with the X pixdim negated), and an offset specified by
        the ANALYZE ``origin`` fields. Construction of the affine is handled
        by ``nibabel``.

      - The :meth:`niftiVersion` method will return ``0``.

      - The :meth:`getXFormCode` method will return
        :attr:`.constants.NIFTI_XFORM_ANALYZE`.


    **Metadata**


    The ``Image`` class inherits from the :class:`.Meta` class - its methods
    can be used to store and query any meta-data associated with the image.


    **Notification**


    The ``Nifti`` class implements the :class:`.Notifier` interface -
    listeners may register to be notified on the following topics:

    =============== ========================================================
    ``'transform'`` The affine transformation matrix has changed. This topic
                    will occur when the :meth:`voxToWorldMat` is changed.
    ``'header'``    A header field has changed. This will occur when the
                    :meth:`intent` is changed.
    =============== ========================================================
    """  # noqa


    def __init__(self, header):
        """Create a ``Nifti`` object.

        :arg header: A :class:`nibabel.nifti1.Nifti1Header`,
                     :class:`nibabel.nifti2.Nifti2Header`, or
                     ``nibabel.analyze.AnalyzeHeader`` to be used as the
                     image header.
        """

        # Nifti2Header is a sub-class of Nifti1Header,
        # and Nifti1Header a sub-class of AnalyzeHeader,
        # so we only need to test for the latter.
        if not isinstance(header, nib.analyze.AnalyzeHeader):
            raise ValueError('Unrecognised header: {}'.format(header))

        origShape, shape, pixdim = Nifti.determineShape(header)
        voxToWorldMat            = Nifti.determineAffine(header)
        affines, isneuro         = Nifti.generateAffines(voxToWorldMat,
                                                         shape,
                                                         pixdim)

        self.__header         = header
        self.__shape          = shape
        self.__origShape      = origShape
        self.__pixdim         = pixdim
        self.__affines        = affines
        self.__isNeurological = isneuro


    def __del__(self):
        """Clears the reference to the ``nibabel`` header object. """
        self.__header = None


    @staticmethod
    def determineShape(header):
        """This method is called by :meth:`__init__`. It figures out the actual
        shape of the image data, and the zooms/pixdims for each data axis. Any
        empty trailing dimensions are squeezed, but the returned shape is
        guaranteed to be at least 3 dimensions. Returns:

         - A sequence/tuple containing the image shape, as reported in the
           header.
         - A sequence/tuple containing the effective image shape.
         - A sequence/tuple containing the zooms/pixdims.
        """

        # The canonicalShape function figures out
        # the data shape that we should use.
        origShape = list(header.get_data_shape())
        shape     = canonicalShape(origShape)
        pixdims   = list(header.get_zooms())

        # if get_zooms() doesn't return at
        # least len(shape) values, we'll
        # fall back to the pixdim field in
        # the header.
        if len(pixdims) < len(shape):
            pixdims = header['pixdim'][1:]

        pixdims = pixdims[:len(shape)]

        # should never happen, but if we only
        # have zoom values for the original
        # (< 3D) shape, pad them with 1s.
        if len(pixdims) < len(shape):
            pixdims = pixdims + [1] * (len(shape) - len(pixdims))

        return origShape, shape, pixdims


    @staticmethod
    def determineAffine(header):
        """Called by :meth:`__init__`. Figures out the voxel-to-world
        coordinate transformation matrix that is associated with this
        ``Nifti`` instance.
        """

        # We have to treat FSL/FNIRT images
        # specially, as FNIRT clobbers the
        # sform section of the NIFTI header
        # to store other data.
        intent = header.get('intent_code', -1)
        qform  = header.get('qform_code',  -1)
        sform  = header.get('sform_code',  -1)

        # FNIRT non-linear coefficient files
        # clobber the sform/qform/intent
        # and pixdims of the nifti header,
        # so we can't correctly place it in
        # the world coordinate system. See
        # $FSLDIR/src/fnirt/fnirt_file_writer.cpp
        # and fsl.transform.nonlinear for more
        # details.
        if intent in (constants.FSL_DCT_COEFFICIENTS,
                      constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
                      constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS,
                      constants.FSL_TOPUP_CUBIC_SPLINE_COEFFICIENTS,
                      constants.FSL_TOPUP_QUADRATIC_SPLINE_COEFFICIENTS):

            log.debug('FNIRT coefficient field detected - generating affine')

            # Knot spacing is stored in the pixdims
            # (specified in terms of reference image
            # voxels), and reference image pixdims
            # are stored as intent code parameters.
            # If we combine the two, we can at least
            # get the shape/size of the coefficient
            # field about right
            knotpix       =  header.get_zooms()[:3]
            refpix        = (header.get('intent_p1', 1) or 1,
                             header.get('intent_p2', 1) or 1,
                             header.get('intent_p3', 1) or 1)
            voxToWorldMat = affine.concat(
                affine.scaleOffsetXform(refpix,  0),
                affine.scaleOffsetXform(knotpix, 0))

        # If the qform or sform codes are unknown,
        # then we can't assume that the transform
        # matrices are valid. So we fall back to a
        # pixdim scaling matrix.
        #
        # n.b. For images like this, nibabel returns
        # a scaling matrix where the centre voxel
        # corresponds to world location (0, 0, 0).
        # This goes against the NIFTI spec - it
        # should just be a straight scaling matrix.
        elif qform == 0 and sform == 0:
            pixdims       = header.get_zooms()
            voxToWorldMat = affine.scaleOffsetXform(pixdims, 0)

        # Otherwise we let nibabel decide
        # which transform to use.
        else:
            voxToWorldMat = np.array(header.get_best_affine())

        return voxToWorldMat


    @staticmethod
    def generateAffines(voxToWorldMat, shape, pixdim):
        """Called by :meth:`__init__`, and the :meth:`voxToWorldMat` setter.
        Generates and returns a dictionary containing affine transformations
        between the ``voxel``, ``fsl``, and ``world`` coordinate
        systems. These affines are accessible via the :meth:`getAffine`
        method.

        :arg voxToWorldMat: The voxel-to-world affine transformation
        :arg shape:         Image shape (number of voxels along each dimension
        :arg pixdim:        Image pixdims (size of one voxel along each
                            dimension)
        :returns:           A tuple containing:

                             - a dictionary of affine transformations between
                               each pair of coordinate systems
                             - ``True`` if the image is to be considered
                               "neurological", ``False`` otherwise - see the
                               :meth:`isNeurological` method.
        """

        import numpy.linalg as npla

        affines = {}
        shape             = list(shape[ :3])
        pixdim            = list(pixdim[:3])
        voxToScaledVoxMat = np.diag(pixdim + [1.0])
        isneuro           = npla.det(voxToWorldMat) > 0

        if isneuro:
            x                 = (shape[0] - 1) * pixdim[0]
            flip              = affine.scaleOffsetXform([-1, 1, 1],
                                                        [ x, 0, 0])
            voxToScaledVoxMat = affine.concat(flip, voxToScaledVoxMat)

        affines['fsl',   'fsl']   = np.eye(4)
        affines['voxel', 'voxel'] = np.eye(4)
        affines['world', 'world'] = np.eye(4)
        affines['voxel', 'world'] = voxToWorldMat
        affines['world', 'voxel'] = affine.invert(voxToWorldMat)
        affines['voxel', 'fsl']   = voxToScaledVoxMat
        affines['fsl',   'voxel'] = affine.invert(voxToScaledVoxMat)
        affines['fsl',   'world'] = affine.concat(affines['voxel', 'world'],
                                                  affines['fsl',   'voxel'])
        affines['world', 'fsl']   = affine.concat(affines['voxel',   'fsl'],
                                                  affines['world', 'voxel'])

        return affines, isneuro


    @staticmethod
    def identifyAffine(image, xform, from_=None, to=None):
        """Attempt to identify the source or destination space for the given
        affine.

        ``xform`` is assumed to be an affine transformation which can be used
        to transform coordinates between two coordinate systems associated with
        ``image``.

        If one of ``from_`` or ``to`` is provided, the other will be derived.
        If neither are provided, both will be derived. See the
        :meth:`.Nifti.getAffine` method for details on the valild values that
        ``from_`` and ``to`` may take.

        :arg image: :class:`.Nifti` instance associated with the affine.

        :arg xform: ``(4, 4)`` ``numpy`` array encoding an affine
                    transformation

        :arg from_: Label specifying the coordinate system which ``xform``
                    takes as input

        :arg to:    Label specifying the coordinate system which ``xform``
                    produces as output

        :returns:   A tuple containing:
                      - A label for the ``from_`` coordinate system
                      - A label for the ``to`` coordinate system
        """

        if (from_ is not None) and (to is not None):
            return from_, to

        if from_ is not None: froms = [from_]
        else:                 froms = ['voxel', 'fsl', 'world']
        if to    is not None: tos   = [to]
        else:                 tos   = ['voxel', 'fsl', 'world']

        for from_, to in it.product(froms, tos):

            candidate = image.getAffine(from_, to)

            if np.all(np.isclose(candidate, xform)):
                return from_, to

        raise ValueError('Could not identify affine')


    def strval(self, key):
        """Returns the specified NIFTI header field, converted to a python
        string, with non-printable characters removed.

        This method is used to sanitise some NIFTI header fields. The default
        Python behaviour for converting a sequence of bytes to a string is to
        strip all termination characters (bytes with value of ``0x00``) from
        the end of the sequence.

        This default behaviour does not handle the case where a sequence of
        bytes which did contain a long string is subsequently overwritten with
        a shorter string - the short string will be terminated, but that
        termination character will be followed by the remainder of the
        original string.
        """

        val = self.header[key]

        try:              val = bytes(val).partition(b'\0')[0]
        except Exception: val = bytes(val)

        val = [chr(c) for c in val]
        val = ''.join(c for c in val if c in string.printable).strip()

        return val


    @property
    def header(self):
        """Return a reference to the ``nibabel`` header object. """
        return self.__header


    @header.setter
    def header(self, header):
        """Replace the ``nibabel`` header object managed by this ``Nifti``
        with a new header. The new header must have the same dimensions,
        voxel size, and orientation as the old one.
        """
        new = Nifti(header)
        if not (self.sameSpace(new) and self.ndim == new.ndim):
            raise ValueError('Incompatible header')
        self.__header = header


    @property
    def niftiVersion(self):
        """Returns the NIFTI file version:

           - ``0`` for ANALYZE
           - ``1`` for NIFTI1
           - ``2`` for NIFTI2
        """

        # nib.Nifti2 is a subclass of Nifti1,
        # and Nifti1 a subclass of Analyze,
        # so we have to check in order
        if   isinstance(self.header, nib.nifti2.Nifti2Header):   return 2
        elif isinstance(self.header, nib.nifti1.Nifti1Header):   return 1
        elif isinstance(self.header, nib.analyze.AnalyzeHeader): return 0

        else: raise RuntimeError('Unrecognised header: {}'.format(self.header))


    @property
    def shape(self):
        """Returns a tuple containing the normalised image data shape.  The
        image shape is at least three dimensions, and trailing dimensions of
        length 1 are squeezed out.
        """
        return tuple(self.__shape)


    @property
    def realShape(self):
        """Returns a tuple containing the image data shape, as reported in
        the NIfTI image header.
        """
        return tuple(self.__origShape)


    @property
    def ndim(self):
        """Returns the number of dimensions in this image. This number may not
        match the number of dimensions specified in the NIFTI header, as
        trailing dimensions of length 1 are ignored. But it is guaranteed to be
        at least 3.
        """
        return len(self.__shape)


    @property
    def pixdim(self):
        """Returns a tuple containing the image pixdims (voxel sizes)."""
        return tuple(self.__pixdim)


    @property
    def intent(self):
        """Returns the NIFTI intent code of this image. """
        return self.header.get('intent_code', constants.NIFTI_INTENT_NONE)


    @property
    def niftiDataType(self):
        """Returns the NIFTI data type code of this image. """
        dt = self.header.get('datatype', constants.NIFTI_DT_UNKNOWN)

        return int(dt)


    @property
    def niftiDataTypeSize(self):
        """Returns the number of bits per voxel, according to the NIfTI
        data type. Returns ``None`` if the data type is not recognised.
        """
        sizes = {
            constants.NIFTI_DT_BINARY        : 1,
            constants.NIFTI_DT_UNSIGNED_CHAR : 8,
            constants.NIFTI_DT_SIGNED_SHORT  : 16,
            constants.NIFTI_DT_SIGNED_INT    : 32,
            constants.NIFTI_DT_FLOAT         : 32,
            constants.NIFTI_DT_COMPLEX       : 64,
            constants.NIFTI_DT_DOUBLE        : 64,
            constants.NIFTI_DT_RGB           : 24,
            constants.NIFTI_DT_UINT8         : 8,
            constants.NIFTI_DT_INT16         : 16,
            constants.NIFTI_DT_INT32         : 32,
            constants.NIFTI_DT_FLOAT32       : 32,
            constants.NIFTI_DT_COMPLEX64     : 64,
            constants.NIFTI_DT_FLOAT64       : 64,
            constants.NIFTI_DT_RGB24         : 24,
            constants.NIFTI_DT_INT8          : 8,
            constants.NIFTI_DT_UINT16        : 16,
            constants.NIFTI_DT_UINT32        : 32,
            constants.NIFTI_DT_INT64         : 64,
            constants.NIFTI_DT_UINT64        : 64,
            constants.NIFTI_DT_FLOAT128      : 128,
            constants.NIFTI_DT_COMPLEX128    : 128,
            constants.NIFTI_DT_COMPLEX256    : 256,
            constants.NIFTI_DT_RGBA32        : 32}
        return sizes.get(self.niftiDataType, None)


    @intent.setter
    def intent(self, val):
        """Sets the NIFTI intent code of this image. """
        # analyze has no intent
        if (self.niftiVersion > 0) and (val != self.intent):
            self.header.set_intent(val, allow_unknown=True)
            self.notify(topic='header')


    @property
    def xyzUnits(self):
        """Returns the NIFTI XYZ dimension unit code. """

        # analyze images have no unit field
        if self.niftiVersion == 0:
            return constants.NIFTI_UNITS_MM

        # The nibabel get_xyzt_units returns labels,
        # but we want the NIFTI codes. So we use
        # the (undocumented) nifti1.unit_codes field
        # to convert back to the raw codes.
        units = self.header.get_xyzt_units()[0]
        units = nib.nifti1.unit_codes[units]
        return units


    @property
    def timeUnits(self):
        """Returns the NIFTI time dimension unit code. """

        # analyze images have no unit field
        if self.niftiVersion == 0:
            return constants.NIFTI_UNITS_SEC

        # See xyzUnits
        units = self.header.get_xyzt_units()[1]
        units = nib.nifti1.unit_codes[units]
        return units


    def getAffine(self, from_, to):
        """Return an affine transformation which can be used to transform
        coordinates from ``from_`` to ``to``.

        Valid values for the ``from_`` and ``to`` arguments are:

         - ``'voxel'``: The voxel coordinate system
         - ``'world'``: The world coordinate system, as defined by the image
           sform/qform
         - ``'fsl'``: The FSL coordinate system (scaled voxels, with a
           left-right flip if the sform/qform has a positive determinant)

        :arg from_: Source coordinate system
        :arg to:    Destination coordinate system
        :returns:   A ``numpy`` array of shape ``(4, 4)``
        """
        from_ = from_.lower()
        to    = to   .lower()

        if from_ not in ('voxel', 'fsl', 'world') or \
           to    not in ('voxel', 'fsl', 'world'):
            raise ValueError('Invalid source/reference spaces: "{}" -> "{}".'
                             'Recognised spaces are "voxel", "fsl", and '
                             '"world"'.format(from_, to))

        return np.copy(self.__affines[from_, to])


    @property
    def worldToVoxMat(self):
        """Returns a ``numpy`` array of shape ``(4, 4)`` containing an
        affine transformation from world coordinates to voxel coordinates.
        """
        return self.getAffine('world', 'voxel')


    @property
    def voxToWorldMat(self):
        """Returns a ``numpy`` array of shape ``(4, 4)`` containing an
        affine transformation from voxel coordinates to world coordinates.
        """
        return self.getAffine('voxel', 'world')


    @voxToWorldMat.setter
    def voxToWorldMat(self, xform):
        """Update the ``voxToWorldMat``. The ``worldToVoxMat`` value is also
        updated. This will result in notification on the ``'transform'``
        topic.
        """

        # Can't do much with
        # an analyze image
        if self.niftiVersion == 0:
            raise Exception('voxToWorldMat cannot be '
                            'changed for an ANALYZE image')

        header    = self.header
        sformCode = int(header['sform_code'])

        if sformCode == constants.NIFTI_XFORM_UNKNOWN:
            sformCode = constants.NIFTI_XFORM_ALIGNED_ANAT

        header.set_sform(xform, code=sformCode)

        affines, isneuro = Nifti.generateAffines(xform,
                                                 self.shape,
                                                 self.pixdim)

        self.__affines        = affines
        self.__isNeurological = isneuro

        log.debug('Affine changed:\npixdims: '
                  '%s\nsform: %s\nqform: %s',
                  header.get_zooms(),
                  header.get_sform(),
                  header.get_qform())

        self.notify(topic='transform')


    @property
    def voxToScaledVoxMat(self):
        """Returns a transformation matrix which transforms from voxel
        coordinates into scaled voxel coordinates, with a left-right flip
        if the image appears to be stored in neurological order.

        See http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the\
        _format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to\
        _the_transformation_parameters.3F
        """
        return self.getAffine('voxel', 'fsl')


    @property
    def scaledVoxToVoxMat(self):
        """Returns a transformation matrix which transforms from scaled voxels
        into voxels, the inverse of the :meth:`voxToScaledVoxMat` transform.
        """
        return self.getAffine('fsl', 'voxel')


    @deprecated.deprecated('3.9.0', '4.0.0', 'Use canonicalSliceObj instead')
    def mapIndices(self, sliceobj):
        """Deprecated - use :func:`canonicalSliceObj` instead. """
        return fileslice.canonical_slicers(sliceobj, self.__origShape)


    def getXFormCode(self, code=None):
        """This method returns the code contained in the NIFTI header,
        indicating the space to which the (transformed) image is oriented.

        The ``code`` parameter may be either ``sform`` (the default) or
        ``qform`` in which case the corresponding matrix is used.

        :returns: one of the following codes:
                    - :data:`~.constants.NIFTI_XFORM_UNKNOWN`
                    - :data:`~.constants.NIFTI_XFORM_SCANNER_ANAT`
                    - :data:`~.constants.NIFTI_XFORM_ALIGNED_ANAT`
                    - :data:`~.constants.NIFTI_XFORM_TALAIRACH`
                    - :data:`~.constants.NIFTI_XFORM_MNI_152`
                    - :data:`~.constants.NIFTI_XFORM_TEMPLATE_OTHER`
                    - :data:`~.constants.NIFTI_XFORM_ANALYZE`
        """

        if self.niftiVersion == 0:
            return constants.NIFTI_XFORM_ANALYZE

        if   code == 'sform' : code = 'sform_code'
        elif code == 'qform' : code = 'qform_code'
        elif code is not None:
            raise ValueError('code must be None, sform, or qform')

        if code is not None:
            code = self.header[code]

        # If the caller did not specify
        # a code, we check both. If the
        # sform is present, we return it.
        # Otherwise, if the qform is
        # present, we return that.
        else:

            sform_code = self.header['sform_code']
            qform_code = self.header['qform_code']

            if   sform_code != constants.NIFTI_XFORM_UNKNOWN: code = sform_code
            elif qform_code != constants.NIFTI_XFORM_UNKNOWN: code = qform_code

        # Invalid code (the maxmimum NIFTI_XFORM_*
        # code value is 5 at present)
        if code not in range(6):
            code = constants.NIFTI_XFORM_UNKNOWN

        return int(code)


    # TODO Check what has worse performance - hashing
    #      a 4x4 array (via memoizeMD5), or the call
    #      to aff2axcodes. I'm guessing the latter,
    #      but am not 100% sure.
    @memoize.Instanceify(memoize.memoizeMD5)
    def axisMapping(self, xform):
        """Returns the (approximate) correspondence of each axis in the source
        coordinate system to the axes in the destination coordinate system,
        where the source and destinations are defined by the given affine
        transformation matrix.
        """

        inaxes = [[-1, 1], [-2, 2], [-3, 3]]

        return nib.orientations.aff2axcodes(xform, inaxes)


    def isNeurological(self):
        """Returns ``True`` if it looks like this ``Nifti`` object has a
        neurological voxel orientation, ``False`` otherwise. This test is
        purely based on the determinant of the voxel-to-mm transformation
        matrix - if it has a positive determinant, the image is assumed to
        be in neurological orientation, otherwise it is assumed to be in
        radiological orientation.

        ..warning:: This method will return ``True`` for images with an
                    unknown orientation (e.g. the ``sform_code`` and
                    ``qform_code`` are both set to ``0``). Therefore, you
                    must check the orientation via the :meth:`getXFormCode`
                    before trusting the result of this method.

        See http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the\
        _format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to\
        _the_transformation_parameters.3F
        """
        return self.__isNeurological


    def sameSpace(self, other):
        """Returns ``True`` if the ``other`` image (assumed to be a
        :class:`Nifti` instance) has the same dimensions and is in the
        same space as this image.
        """
        return np.all(np.isclose(self .shape[:3],
                                 other.shape[:3]))  and \
               np.all(np.isclose(self .pixdim[:3],
                                 other.pixdim[:3])) and \
               np.all(np.isclose(self .voxToWorldMat,
                                 other.voxToWorldMat))


    def getOrientation(self, axis, xform):
        """Returns a code representing the orientation of the specified
        axis in the input coordinate system of the given transformation
        matrix.

        :arg xform: A transformation matrix which is assumed to transform
                    coordinates from some coordinate system (the one
                    which you want an orientation for) into the image
                    world coordinate system.

                    For example, if you pass in the voxel-to-world
                    transformation matrix, you will get an orientation
                    for axes in the voxel coordinate system.

        This method returns one of the following values, indicating the
        direction in which coordinates along the specified axis increase:

          - :attr:`~.constants.ORIENT_L2R`:     Left to right
          - :attr:`~.constants.ORIENT_R2L`:     Right to left
          - :attr:`~.constants.ORIENT_A2P`:     Anterior to posterior
          - :attr:`~.constants.ORIENT_P2A`:     Posterior to anterior
          - :attr:`~.constants.ORIENT_I2S`:     Inferior to superior
          - :attr:`~.constants.ORIENT_S2I`:     Superior to inferior
          - :attr:`~.constants.ORIENT_UNKNOWN`: Orientation is unknown

        The returned value is dictated by the XForm code contained in the
        image file header (see the :meth:`getXFormCode` method). Basically, if
        the XForm code is *unknown*, this method will return
        ``ORIENT_UNKNOWN`` for all axes. Otherwise, it is assumed that the
        image is in RAS orientation (i.e. the X axis increases from left to
        right, the Y axis increases from posterior to anterior, and the Z axis
        increases from inferior to superior).
        """

        if self.getXFormCode() == constants.NIFTI_XFORM_UNKNOWN:
            return constants.ORIENT_UNKNOWN

        code = nib.orientations.aff2axcodes(
            xform,
            ((constants.ORIENT_R2L, constants.ORIENT_L2R),
             (constants.ORIENT_A2P, constants.ORIENT_P2A),
             (constants.ORIENT_S2I, constants.ORIENT_I2S)))[axis]

        return code


    def adjust(self, pixdim=None, shape=None, origin=None):
        """Return a new ``Nifti`` object with the specified ``pixdim`` or
        ``shape``. The affine of the new ``Nifti`` is adjusted accordingly.

        Only one of ``pixdim`` or ``shape`` can be specified.

        See :func:`.affine.rescale` for the meaning of the ``origin`` argument.

        Only the spatial dimensions may be adjusted - use the functions in
        the :mod:`.image.resample` module if you need to adjust non-spatial
        dimensions.

        :arg pixdim: New voxel dimensions
        :arg shape:  New image shape
        :arg origin: Voxel grid alignment - either ``'centre'`` (the default)
                     or ``'corner'``
        :returns:    A new ``Nifti`` object based on this one, with adjusted
                     pixdims, shape and affine.
        """

        if ((pixdim is not None) and (shape is not None)) or \
           ((pixdim is     None) and (shape is     None)):
            raise ValueError('Exactly one of pixdim or '
                             'shape must be specified')

        if shape is not None: ndim = len(shape)
        else:                 ndim = len(pixdim)

        # We only allow adjustment of
        # the spatial dimensions
        if ndim != 3:
            raise ValueError('Three dimensions must be specified')

        oldShape  = np.array(self.shape[ :ndim])
        oldPixdim = np.array(self.pixdim[:ndim])
        newShape  = shape
        newPixdim = pixdim

        # if pixdims were specified,
        # convert them into a shape,
        # and vice versa
        if newPixdim is not None:
            newShape = oldShape * (oldPixdim / newPixdim)
        else:
            newPixdim = oldPixdim * (oldShape / newShape)

        # Rescale the voxel-to-world affine
        xform = affine.rescale(oldShape, newShape, origin)
        xform = affine.concat(self.getAffine('voxel', 'world'), xform)

        # Now that we've got our spatial
        # scaling/offset matrix, pad the
        # new shape/pixdims with those
        # from any non-spatial dimensions
        newShape  = list(newShape)  + list(self.shape[ 3:])
        newPixdim = list(newPixdim) + list(self.pixdim[3:])

        # And create the new header
        # and we're away
        header = self.header.copy()
        header.set_data_shape(newShape)
        header.set_zooms(     newPixdim)
        header.set_sform(     xform)
        header.set_qform(     xform)
        return Nifti(header)


class Image(Nifti):
    """Class which represents a NIFTI image. Internally, the image is
    loaded/stored using a :mod:`nibabel.nifti1.Nifti1Image` or
    :mod:`nibabel.nifti2.Nifti2Image`. This class adds functionality for
    loading metadata from JSON sidecar files, and for keeping track of
    modifications to the image data.


    In addition to the attributes added by the :meth:`Nifti.__init__` method,
    the following attributes/properties are present on an ``Image`` instance
    as properties (https://docs.python.org/2/library/functions.html#property):


    ============== ===========================================================
    ``name``       The name of this ``Image`` - defaults to the image
                   file name, sans-suffix.

    ``dataSource`` The data source of this ``Image`` - the name of the
                   file from where it was loaded, or some other string
                   describing its origin.

    ``dataRange``  The ``(min, max)`` image data values.

    ``nibImage``   A reference to the ``nibabel`` NIFTI image object.

    ``saveState``  A boolean value which is ``True`` if this image is
                   saved to disk, ``False`` if it is in-memory, or has
                   been edited.
    ============== ===========================================================


    *Data access*


    The ``Image`` class supports access to and assignment of the image data
    via the ``[]`` slice operator, e.g.::

        img             = Image('image.nii.gz')
        val             = img[20, 30, 25]
        img[30, 40, 20] = 999

    Internally, the image data is managed using one of the following methods:

     1. For read-only access, the ``Image`` class delegates to the
        underlying ``nibabel.Nifti1Image`` instance, accessing the data
        via the ``Nifti1Image.dataobj`` attribute.  Refer to
        https://nipy.org/nibabel/nibabel_images.html#the-image-data-array for
        more details.

     2. As soon as any data is modified, the ``Image`` class will
        load the image data as a numpy array into memory and will maintain its
        own reference to the array for subsequent access. Note that this
        array is entirely independent of any array that is cached by
        the underlying ``nibabel.Nifti1Image`` object (refer to
        https://nipy.org/nibabel/images_and_memory.html)

     3. The ``nibabel.Nifti1Image`` class does not support indexing of image
        data with boolean mask arrays (e.g. ``image[mask > 0]``). If an
        attempt is made to access image data in this way, the ``Image`` class
        will be loaded into memory in the same way as described in point 2
        above.

     4. For more complicated requirements, a :class:`DataManager`,
        implementing custom data access management logic, can be provided when
        an ``Image`` is created. If a ``DataManager`` is provided, an
        internal reference to the data (see 2 above) will **not** be created or
        maintained.


    It is also possible to obtain a reference to a numpy array containing
    the image data via the :meth:`data` method. However, modifications to
    the returned array:

      - will not result in any notifications (described below)
      - will not affect the value of :meth:`saveState`
      - have undefined semantics when a custom :class:`DataManager` is in use


    *Image dimensionality*


    The ``Image`` class abstracts away trailing image dimensions of length 1.
    This means that if the header for a NIFTI image specifies that the image
    has four dimensions, but the fourth dimension is of length 1, you do not
    need to worry about indexing that fourth dimension. However, all NIFTI
    images will be presented as having at least three dimensions, so if your
    image header specifies a third dimension of length 1, you will still
    need provide an index of 0 for that dimensions, for all data accesses.


    *Notification of changes to an Image*


    The ``Image`` class adds some :class:`.Notifier` topics to those which are
    already provided by the :class:`Nifti` class - listeners may register to
    be notified of changes to the above properties, by registering on the
    following _topic_ names (see the :class:`.Notifier` class documentation):


    =============== ======================================================
    ``'data'``      This topic is notified whenever the image data changes
                    (via the :meth:`__setitem__` method). The indices/
                    slices of the portion of data that was modified is
                    passed to registered listeners as the notification
                    value (see :meth:`.Notifier.notify`).

    ``'saveState'`` This topic is notified whenever the saved state of the
                    image changes (i.e. data or ``voxToWorldMat`` is
                    edited, or the image saved to disk).

    ``'dataRange'`` Deprecated - No notifications are made on this topic.
    =============== ======================================================
    """


    def __init__(self,
                 image      : ImageSource      = None,
                 name       : str              = None,
                 header     : nib.Nifti1Header = None,
                 xform      : np.ndarray       = None,
                 loadData   : bool             = None,
                 calcRange  : bool             = None,
                 threaded   : bool             = None,
                 dataSource : PathLike         = None,
                 loadMeta   : bool             = False,
                 dataMgr    : DataManager      = None,
                 **kwargs):
        """Create an ``Image`` object with the given image data or file name.

        :arg image:      A string containing the name of an image file to load,
                         or a Path object pointing to an image file, or a
                         :mod:`numpy` array, or a :mod:`nibabel` image object,
                         or an ``Image`` object. If not provided, a ``header``
                         and a ``dataMgr`` must be provided.

        :arg name:       A name for the image.

        :arg header:     If not ``None``, assumed to be a
                         :class:`nibabel.nifti1.Nifti1Header` or
                         :class:`nibabel.nifti2.Nifti2Header` to be used as the
                         image header. Not applied to images loaded from file,
                         or existing :mod:`nibabel` images.

        :arg xform:      A :math:`4\\times 4` affine transformation matrix
                         which transforms voxel coordinates into real world
                         coordinates. If not provided, and a ``header`` is
                         provided, the transformation in the header is used.
                         If neither a ``xform`` nor a ``header`` are provided,
                         an identity matrix is used. If both a ``xform`` and a
                         ``header`` are provided, the ``xform`` is used in
                         preference to the header transformation.

        :arg loadData:   Deprecated, has no effect

        :arg calcRange:  Deprecated, has no effect

        :arg threaded:   Deprecated, has no effect

        :arg dataSource: If ``image`` is not a file name, this argument may be
                         used to specify the file from which the image was
                         loaded.

        :arg loadMeta:   If ``True``, any metadata contained in JSON sidecar
                         files is loaded and attached to this ``Image`` via
                         the :class:`.Meta` interface. if ``False``, metadata
                         can be loaded at a later stage via the
                         :func:`loadMeta` function. Defaults to ``False``.

        :arg dataMgr:    Object implementing the :class:`DataManager`
                         interface, for managing access to the image data.

        All other arguments are passed through to the ``nibabel.load`` function
        (if it is called).
        """

        if threaded is not None:
            deprecated.warn('Image(threaded)', vin='3.9.0', rin='4.0.0',
                            msg='The threaded option has no effect')
        if loadData is not None:
            deprecated.warn('Image(loadData)', vin='3.9.0', rin='4.0.0',
                            msg='The loadData option has no effect')
        if calcRange is not None:
            deprecated.warn('Image(calcRange)', vin='3.9.0', rin='4.0.0',
                            msg='The calcRange option has no effect')

        nibImage = None
        saved    = False

        # Take a copy of the header if one has
        # been provided
        #
        # NOTE: Nifti extensions are copied by
        # reference, which may cause issues in
        # the future.
        if header is not None:
            header = header.copy()

        # if a header and xform are provided,
        # make sure the xform gets used. Does
        # not apply to ANALYZE images,
        if header is not None and \
           xform  is not None and \
           isinstance(header, nib.nifti1.Nifti1Header):
            sform = int(header.get_sform(True)[1])
            qform = int(header.get_qform(True)[1])
            header.set_sform(xform, code=sform)
            header.set_qform(xform, code=qform)

        # The image parameter may be the name of an image file
        if isinstance(image, (str, Path)):
            # resolve path to source if it is a sym-link
            image      = Path(image).resolve()
            image      = op.abspath(addExt(image))
            nibImage   = nib.load(image, **kwargs)
            header     = nibImage.header
            dataSource = image
            saved      = True

        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):

            if xform is None:
                if header is not None: xform = header.get_best_affine()
                else:                  xform = np.identity(4)

            # default to NIFTI1 if FSLOUTPUTTYPE
            # is not set, just to be safe.
            if header is None:
                outputType = os.environ.get('FSLOUTPUTTYPE', 'NIFTI_GZ')
                if 'NIFTI2' in outputType: ctr = nib.Nifti2Image
                else:                      ctr = nib.Nifti1Image

            # make sure that the data type is correct,
            # in case this header was passed in from
            # a different image
            if header is not None:
                header.set_data_dtype(image.dtype)

            # But if a nibabel header has been provided,
            # we use the corresponding image type
            if isinstance(header, nib.nifti2.Nifti2Header):
                ctr = nib.nifti2.Nifti2Image
            elif isinstance(header, nib.nifti1.Nifti1Header):
                ctr = nib.nifti1.Nifti1Image
            elif isinstance(header, nib.analyze.AnalyzeHeader):
                ctr = nib.analyze.AnalyzeImage

            nibImage = ctr(image, xform, header=header)
            header   = nibImage.header

        # If it's an Image object, we
        # just take the nibabel image
        elif isinstance(image, Image):
            nibImage = image.nibImage
            header   = image.header

        # otherwise, we assume that
        # it is a nibabel image
        elif image is not None:
            nibImage = image
            header   = nibImage.header

        # If an image is not provided,
        # a DataManager must be provided
        elif dataMgr is None:
            raise ValueError('A DataManager must be provided '
                             'if an image is not provided')

        if header is None:
            raise ValueError('Could not identify/create NIfTI header')

        # Figure out the name of this image, if
        # it has not been explicitly passed in
        if name is None:

            # If this image was loaded
            # from disk, use the file name.
            if isinstance(image, (str, Path)):
                name = removeExt(op.basename(image))

            # Or the image was created from a numpy array
            elif isinstance(image, np.ndarray):
                name = 'Numpy array'

            # Or image from a nibabel image
            else:
                name = 'Nibabel image'

        Nifti.__init__(self, header)

        self.name         = name
        self.__lName      = f'{id(self)}_{self.name}'
        self.__dataSource = dataSource
        self.__nibImage   = nibImage
        self.__saveState  = saved
        self.__dataMgr    = dataMgr
        self.__dataRange  = None
        self.__data       = None

        # Listen to ourself for changes
        # to header attributse so we
        # can update the saveState.
        self.register(self.name, self.__headerChanged, topic='transform')
        self.register(self.name, self.__headerChanged, topic='header')

        # try and load metadata
        # from JSON sidecar files
        if self.dataSource is not None and loadMeta:
            try:
                self.updateMeta(loadMetadata(self))
            except Exception as e:
                log.warning('Failed to load metadata for %s: %s',
                            self.dataSource, e)


    def __hash__(self):
        """Returns a number which uniquely idenfities this ``Image`` instance
        (the result of ``id(self)``).
        """
        return id(self)


    def __str__(self):
        """Return a string representation of this ``Image`` instance."""
        return '{}({}, {})'.format(self.__class__.__name__,
                                   self.name,
                                   self.dataSource)


    def __repr__(self):
        """See the :meth:`__str__` method."""
        return self.__str__()


    def __del__(self):
        """Closes any open file handles, and clears some references. """

        # Nifti class may have
        # been GC'd at shutdown
        if Nifti is not None:
            Nifti.__del__(self)
        self.__nibImage = None
        self.__dataMgr  = None
        self.__data     = None


    @deprecated.deprecated('3.9.0', '4.0.0',
                           'The Image class no longer uses an ImageWrapper')
    def getImageWrapper(self):
        """Returns the :class:`.ImageWrapper` instance used to manage
        access to the image data.
        """
        return None


    @property
    def dataManager(self):
        """Return the :class:`.DataManager` associated with this ``Image``,
        if one was specified when it was created.
        """
        return self.__dataMgr


    @property
    def dataSource(self):
        """Returns the data source (e.g. file name) that this ``Image`` was
        loaded from (``None`` if this image only exists in memory).
        """
        return self.__dataSource


    @property
    def nibImage(self):
        """Returns a reference to the ``nibabel`` NIFTI image instance.
        Note that if the image data has been modified through this ``Image``,
        it will be out of sync with what is returned by the ``nibabel`` object,
        until a call to :meth:`save` is made.
        """
        return self.__nibImage


    @property
    def data(self):
        """Returns the image data as a ``numpy`` array. The shape of the
        returned array is normalised - it will have at least three dimensions,
        and any trailing dimensions of length 1 will be squeezed out.  See
        :meth:`Nifti.shape` and :meth:`Nifti.realShape`.

        .. warning:: Calling this method may cause the entire image to be
                     loaded into memory.
        """

        if self.__dataMgr is not None:
            return self[:]

        # The internal cache has real image shape -
        # this makes code in __getitem__ easier,
        # as it can use the real shape regardless
        # of how the data is accessed
        if self.__data is None:
            self.__data = self.nibImage.dataobj[:]

        return self.__data.reshape(self.shape)


    @property
    def inMemory(self):
        """Returns ``True`` if the image data has been loaded into memory,
        ``False``otherwise. This does not reflect whether the underlying
        ``nibabel.Nifti1Image`` object has loaded the image data into
        memory. However, if all data access takes place through the ``Image``
        class, the underlying ``nibabel`` image will not use a cache.

        If custom ``DataManager`` has loaded the data, this method will always
        return ``False``.
        """
        return self.__data is not None


    @property
    def saveState(self):
        """Returns ``True`` if this ``Image`` has been saved to disk, ``False``
        otherwise.
        """
        return self.__saveState


    @property
    def dataRange(self):
        """Returns the minimum/maxmimum image data values. """

        if   self.__dataMgr   is not None: return self.__dataMgr.dataRange
        elif self.__dataRange is not None: return self.__dataRange

        self.__dataRange = nir.naninfrange(self.data)
        return self.__dataRange


    @property
    def dtype(self):
        """Returns the ``numpy`` data type of the image data. """

        # Get the data type from the
        # first voxel in the image
        coords = [0] * len(self.shape)
        return self[tuple(coords)].dtype


    @property
    def nvals(self):
        """Returns the number of values per voxel in this image. This will
        usually be 1, but may be 3 or 4, for images of type
        ``NIFTI_TYPE_RGB24`` or ``NIFTI_TYPE_RGBA32``.
        """

        nvals = len(self.dtype)
        if nvals == 0: return 1
        else:          return nvals


    @property
    def iscomplex(self):
        """Returns ``True`` if this image has a complex data type, ``False``
        otherwise.
        """
        return np.issubdtype(self.dtype, np.complexfloating)


    @property
    def editable(self):
        """Return ``True`` if the image data can be modified, ``False``
        otherwise. Delegates to :meth:`DataManager.editable` if a
        :class:`DataManager` is in use.
        """
        if self.__dataMgr is not None: return self.__dataMgr.editable
        else:                          return True


    @Nifti.voxToWorldMat.setter
    def voxToWorldMat(self, xform):
        """Overrides the :meth:`Nifti.voxToWorldMat` property setter.
        In ``nibabel``, the header and image affines can easily get
        out of sync when they are modified. The ``Nifti`` implementation
        updates the header, and this implementation makes sure the
        image is also updated.
        """

        Nifti.voxToWorldMat.fset(self, xform)

        if self.__nibImage is None:
            return

        xform =     self.voxToWorldMat
        code  = int(self.header['sform_code'])

        self.__nibImage.set_sform(xform, code)


    def __headerChanged(self, *args, **kwargs):
        """Called when header properties of this :class:`Nifti` instance
        changes. Updates the :attr:`saveState` accordinbgly.
        """
        if self.__saveState:
            self.__saveState = False
            self.notify(topic='saveState')


    @deprecated.deprecated('3.9.0', '4.0.0', 'calcRange has no effect')
    def calcRange(self, *args, **kwargs):
        """Deprecated, has no effect """


    @deprecated.deprecated('3.9.0', '4.0.0', 'loadData has no effect')
    def loadData(self):
        """Deprecated, has no effect """


    def save(self, filename=None):
        """Saves this ``Image`` to the specifed file, or the :attr:`dataSource`
        if ``filename`` is ``None``.

        Note that calling ``save`` on an image with modified data will cause
        the entire image data to be loaded into memory if it has not already
        been loaded.
        """

        import fsl.utils.imcp as imcp

        if self.__dataSource is None and filename is None:
            raise ValueError('A file name must be specified')

        if self.__nibImage is None:
            raise ValueError('Cannot save images without an '
                             'associated nibabel object')

        if filename is None:
            filename = self.__dataSource

        filename = op.abspath(filename)

        # make sure the extension is specified
        if not looksLikeImage(filename):
            filename = addExt(filename, mustExist=False)

        log.debug('Saving %s to %s', self.name, filename)

        # We save the image out to a temp file,
        # then close the old image, move the
        # temp file to the real destination,
        # then re-open the file. This is done
        # to ensure that all references to the
        # old file are destroyed.
        tmphd, tmpfname = tempfile.mkstemp(suffix=getExt(filename))
        os.close(tmphd)

        try:
            # First of all, the nibabel object won't know
            # about any image data modifications, so if
            # any have occurred, we need to create a new
            # nibabel image using our copy of the data,
            # and the old header.
            #
            # Assuming here that analyze/nifti1/nifti2
            # nibabel classes have an __init__ which
            # expects (data, affine, header)
            if not self.saveState:
                self.__nibImage = type(self.__nibImage)(self.data,
                                                        affine=None,
                                                        header=self.header)
                self.header     = self.__nibImage.header

            nib.save(self.__nibImage, tmpfname)

            # Copy to final destination,
            # and reload from there
            imcp.imcp(tmpfname, filename, overwrite=True)

            self.__nibImage = nib.load(filename)
            self.header     = self.__nibImage.header

        finally:
            os.remove(tmpfname)

        # Because we've created a new nibabel image,
        # we may have to create a new DataManager
        # instance too, as we have just destroyed
        # the nibabel image we gave to the last one.
        if self.__dataMgr is not None:
            self.__dataMgr = self.__dataMgr.copy(self.nibImage)

        self.__dataSource = filename
        self.__saveState  = True

        self.notify(topic='saveState')


    def __getitem__(self, slc):
        """Access the image data with the specified ``slc``.

        :arg slc: Something which can slice the image data.
        """

        log.debug('%s: __getitem__ [%s]', self.name, slc)

        # Make the slice object compatible
        # with the actual image shape - e.g.
        # an underlying 2D image is presented
        # as having 3 dimensions.
        shape              = self.shape
        realShape          = self.realShape
        slc                = canonicalSliceObj(   slc, shape)
        fancy              = isValidFancySliceObj(slc, shape)
        expNdims, expShape = expectedShape(       slc, shape)
        slc                = canonicalSliceObj(   slc, realShape)

        # The nibabel arrayproxy does not support
        # boolean mask-based (a.k.a. "fancy")
        # indexing. If we are given a mask, we
        # force-load the image data into memory.
        if all((fancy,
                self.__dataMgr is None,
                self.__data    is None)):
            log.debug('Fancy slice detected - force-loading image '
                      'data  into memory (%s)', self.name)
            self.data

        if   self.__dataMgr is not None: data = self.__dataMgr[slc]
        elif self.__data    is not None: data = self.__data[slc]
        else:                            data = self.__nibImage.dataobj[slc]

        # Make sure that the result has the
        # shape that the caller is expecting.
        if fancy: data = data.reshape((data.size, ))
        else:     data = data.reshape(expShape)

        # If expNdims == 0, we should
        # return a scalar. If expNdims
        # == 0, but data.size != 1,
        # something is wrong somewhere
        # (and is not being handled
        # here).
        if expNdims == 0 and data.size == 1:

            # Funny behaviour with numpy scalar arrays.
            # data[()] returns a numpy scalar (which is
            # what we want). But data.item() returns a
            # python scalar. And if the data is a
            # ndarray with 0 dims, data[0] will raise
            # an error!
            data = data[()]

        return data


    def __setitem__(self, slc, values):
        """Set the image data at ``slc`` to ``values``.

        :arg slc:    Something which can slice the image data.
        :arg values: New image data.

        .. note:: Modifying image data may force the entire image to be
                  loaded into memory if it has not already been loaded.
        """

        if not self.editable:
            raise RuntimeError('Image is not editable')

        values = np.array(values)

        if values.size == 0:
            return

        log.debug('%s: __setitem__ [%s = %s]', self.name, slc, values.shape)

        realShape = self.realShape
        slc       = canonicalSliceObj(slc, realShape)

        # If the image shape does not match its
        # 'display' shape (either less three
        # dims, or  has trailing dims of length
        # 1), we might need to re-shape the
        # values to prevent numpy from raising
        # an error in the assignment below.
        if realShape != self.shape:

            expNdims, expShape = expectedShape(slc, realShape)

            # If we are slicing a scalar, the
            # assigned value has to be scalar.
            if expNdims == 0 and isinstance(values, abc.Sequence):

                if len(values) > 1:
                    raise IndexError('Invalid assignment: [{}] = {}'.format(
                        slc, len(values)))

                values = np.array(values).flatten()[0]

            # Make sure that the values
            # have a compatible shape.
            else:
                values = np.array(values)
                if values.shape != expShape:
                    values = values.reshape(expShape)

        # Use DataManager to manage data
        # access if one has been specified
        if self.__dataMgr is not None:
            self.__dataMgr[slc] = values

        # Use an internal numpy array
        # to persist data changes
        else:
            # force-load data - see the data() method
            # Reset data range whenever the data is
            # modified - see dataRange() method
            if self.__data is None:
                self.data
            self.__data[slc] = values
            self.__dataRange = None

        # Notify that data has changed/image is not saved
        self.notify(topic='data', value=slc)
        if self.__saveState:
            self.__saveState = False
            self.notify(topic='saveState')


def canonicalShape(shape):
    """Calculates a *canonical* shape, how the given ``shape`` should
    be presented. The shape is forced to be at least three dimensions,
    with any other trailing dimensions of length 1 ignored.
    """

    shape = list(shape)

    # Squeeze out empty dimensions, as
    # 3D image can sometimes be listed
    # as having 4 or more dimensions
    for i in reversed(range(len(shape))):
        if shape[i] == 1: shape = shape[:i]
        else:             break

    # But make sure the shape
    # has at 3 least dimensions
    if len(shape) < 3:
        shape = shape + [1] * (3 - len(shape))

    return shape


def isValidFancySliceObj(sliceobj, shape):
    """Returns ``True`` if the given ``sliceobj`` is a valid and fancy slice
    object.

    ``nibabel`` refers to slice objects as "fancy" if they comprise anything
    but tuples of integers and simple ``slice`` objects. The ``Image`` class
    supports an additional type of "fancy" slicing, where the ``sliceobj`` is
    a boolean ``numpy`` array of the same shape as the image.

    This function returns ``True`` if the given ``sliceobj`` adheres to these
    requirements, ``False`` otherwise.
    """

    # We only support boolean numpy arrays
    # which have the same shape as the image
    return (isinstance(sliceobj, np.ndarray) and
            sliceobj.dtype == bool           and
            np.prod(sliceobj.shape) == np.prod(shape))


def canonicalSliceObj(sliceobj, shape):
    """Returns a canonical version of the given ``sliceobj``. See the
    ``nibabel.fileslice.canonical_slicers`` function.
    """

    # Fancy slice objects must have
    # the same shape as the data
    if isValidFancySliceObj(sliceobj, shape):
        return sliceobj.reshape(shape)

    else:

        if not isinstance(sliceobj, tuple):
            sliceobj = (sliceobj,)

        if len(sliceobj) > len(shape):
            sliceobj = sliceobj[:len(shape)]

        return nib.fileslice.canonical_slicers(sliceobj, shape)


def expectedShape(sliceobj, shape):
    """Given a slice object, and the shape of an array to which
    that slice object is going to be applied, returns the expected
    shape of the result.

    .. note:: It is assumed that the ``sliceobj`` has been passed through
              the :func:`canonicalSliceObj` function.

    :arg sliceobj: Something which can be used to slice an array
                   of shape ``shape``.

    :arg shape:    Shape of the array being sliced.

    :returns:      A tuple containing:

                     - Expected number of dimensions of the result

                     - Expected shape of the result (or ``None`` if
                       ``sliceobj`` is fancy).
    """

    if isValidFancySliceObj(sliceobj, shape):
        return 1, None

    # Truncate some dimensions from the
    # slice object if it has too many
    # (e.g. trailing dims of length 1).
    elif len(sliceobj) > len(shape):
        sliceobj = sliceobj[:len(shape)]

    # Figure out the number of dimensions
    # that the result should have, given
    # this slice object.
    expShape = []

    for i in range(len(sliceobj)):

        # Each dimension which has an
        # int slice will be collapsed
        if isinstance(sliceobj[i], int):
            continue

        start = sliceobj[i].start
        stop  = sliceobj[i].stop

        if start is None: start = 0
        if stop  is None: stop  = shape[i]

        stop = min(stop, shape[i])

        expShape.append(stop - start)

    return len(expShape), expShape


def loadMetadata(image):
    """Searches for and loads any sidecar JSON files associated with the given
    :class:`.Image`.

    If the image looks to be part of a BIDS data set,
    :func:`.bids.loadMetadata` is used. Otherwise, if a JSON file with the same
    file prefix is present alongside the image, it is directly loaded.

    :arg image: :class:`.Image` instance
    :returns:   Dict containing any metadata that was loaded.
    """

    if image.dataSource is None:
        return {}

    filename = image.dataSource
    basename = op.basename(removeExt(filename))
    dirname  = op.dirname(filename)

    if fslbids.isBIDSFile(image.dataSource) and \
       fslbids.inBIDSDir( image.dataSource):
        return fslbids.loadMetadata(image.dataSource)

    jsonfile = op.join(dirname, '{}.json'.format(basename))
    if op.exists(jsonfile):
        with open(jsonfile, 'rt') as f:
            return json.load(f, strict=False)

    return {}


def looksLikeImage(filename, allowedExts=None):
    """Returns ``True`` if the given file looks like a NIFTI image, ``False``
    otherwise.

    .. note:: The ``filename`` cannot just be a file prefix - it must
              include the file suffix (e.g. ``myfile.nii.gz``, not
              ``myfile``).

    :arg filename:    The file name to test.

    :arg allowedExts: A list of strings containing the allowed file
                      extensions - defaults to :attr:`ALLOWED_EXTENSIONS`.
    """

    if allowedExts is None:
        allowedExts = ALLOWED_EXTENSIONS

    return fslpath.hasExt(filename, allowedExts)


def addExt(prefix, mustExist=True, unambiguous=True):
    """Adds a file extension to the given file ``prefix``.  See
    :func:`~fsl.utils.path.addExt`.
    """
    try:
        return fslpath.addExt(prefix,
                              allowedExts=ALLOWED_EXTENSIONS,
                              mustExist=mustExist,
                              defaultExt=defaultExt(),
                              fileGroups=FILE_GROUPS,
                              unambiguous=unambiguous)
    except fslpath.PathError as e:
        # hacky: if more than one file with
        # the prefix exists, we emit a
        # warning, because in most cases
        # this is a bad thing.
        if str(e).startswith('More than'):
            log.warning(e)
        raise e


def splitExt(filename):
    """Splits the base name and extension for the given ``filename``.  See
    :func:`~fsl.utils.path.splitExt`.
    """
    return fslpath.splitExt(filename, ALLOWED_EXTENSIONS)


def getExt(filename):
    """Gets the extension for the given file name.  See
    :func:`~fsl.utils.path.getExt`.
    """
    return fslpath.getExt(filename, ALLOWED_EXTENSIONS)


def removeExt(filename):
    """Removes the extension from the given file name. See
    :func:`~fsl.utils.path.removeExt`.
    """
    return fslpath.removeExt(filename, ALLOWED_EXTENSIONS)


def fixExt(filename, **kwargs):
    """Fix the extension of ``filename``.

    For example, if a file name is passed in as ``file.nii.gz``, but the
    file is actually ``file.nii``, this function will fix the file name.

    If ``filename`` already exists, it is returned unchanged.

    All other arguments are passed through to :func:`addExt`.
    """
    if op.exists(filename):
        return filename
    else:
        return addExt(removeExt(filename), **kwargs)


def defaultExt():
    """Returns the default NIFTI file extension that should be used.

    If the ``$FSLOUTPUTTYPE`` variable is set, its value is used.
    Otherwise, ``.nii.gz`` is returned.
    """

    options = {
        'NIFTI'          : '.nii',
        'NIFTI2'         : '.nii',
        'NIFTI_GZ'       : '.nii.gz',
        'NIFTI2_GZ'      : '.nii.gz',
        'NIFTI_PAIR'     : '.img',
        'NIFTI2_PAIR'    : '.img',
        'NIFTI_PAIR_GZ'  : '.img.gz',
        'NIFTI2_PAIR_GZ' : '.img.gz',
    }

    outputType = os.environ.get('FSLOUTPUTTYPE', 'NIFTI_GZ')

    return options.get(outputType, '.nii.gz')
