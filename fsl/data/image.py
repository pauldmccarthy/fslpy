#!/usr/bin/env python
#
# image.py - Provides the :class:`Image` class, for representing 3D/4D NIFTI
#            images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Nifti` and :class:`Image` classes, for
representing 3D/4D NIFTI1 and NIFTI2 images. The ``nibabel`` package is used
for file I/O.


It is very easy to load a NIFTI image::

    from fsl.data.image import Image
    myimg = Image('MNI152_T1_2mm.nii.gz')


A handful of other functions are also provided for working with image files
and file names:

.. autosummary::
   :nosignatures:

   looksLikeImage
   addExt
   splitExt
   getExt
   removeExt
   defaultExt
   loadIndexedImageFile
"""


import                      os
import os.path           as op
import                      string
import                      logging

import                      six
import numpy             as np

import nibabel           as nib
import nibabel.fileslice as fileslice

import fsl.utils.transform   as transform
import fsl.utils.notifier    as notifier
import fsl.utils.memoize     as memoize
import fsl.utils.path        as fslpath
import fsl.data.constants    as constants
import fsl.data.imagewrapper as imagewrapper


log = logging.getLogger(__name__)


class Nifti(notifier.Notifier):
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


    The ``shape`` attribute may not precisely match the image shape as
    reported in the NIFTI header, because trailing dimensions of size 1 are
    squeezed out. See the :meth:`__determineShape` and :meth:`mapIndices`
    methods.


    **The affine transformation**


    The :meth:`voxToWorldMat` and :meth:`worldToVoxMat` attributes contain
    transformation matrices for transforming between voxel and world
    coordinates. The ``Nifti`` class follows the same process as ``nibabel``
    in selecting the affine (see
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
    can als encapsulate a ``nibabel.analyze.AnalyzeHeader``. In this case:

      - The image voxel orientation is assumed to be R->L, P->A, I->S.

      - The affine will be set to a diagonal matrix with the header pixdims as
        its elements (with the X pixdim negated), and an offset specified by
        the ANALYZE ``origin`` fields. Construction of the affine is handled
        by ``nibabel``.

      - The :meth:`niftiVersion` method will return ``0``.

      - The :meth:`getXFormCode` method will return
        :attr:`.constants.NIFTI_XFORM_ANALYZE`.


    **Notification**


    The ``Nifti`` class implements the :class:`.Notifier` interface -
    listeners may register to be notified on the following topics:

    =============== ========================================================
    ``'transform'`` The affine transformation matrix has changed. This topic
                    will occur when the ``voxToWorldMat`` is changed.
    =============== ========================================================
    """


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

        header                   = header
        origShape, shape, pixdim = self.__determineShape(header)

        if len(shape) < 3 or len(shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        voxToWorldMat = self.__determineTransform(header)
        worldToVoxMat = transform.invert(voxToWorldMat)

        self.header          = header
        self.__shape         = shape
        self.__intent        = header.get('intent_code',
                                          constants.NIFTI_INTENT_NONE)
        self.__origShape     = origShape
        self.__pixdim        = pixdim
        self.__voxToWorldMat = voxToWorldMat
        self.__worldToVoxMat = worldToVoxMat


    def __determineTransform(self, header):
        """Called by :meth:`__init__`. Figures out the voxel-to-world
        coordinate transformation matrix that is associated with this
        ``Nifti`` instance.
        """

        # We have to treat FSL/FNIRT images
        # specially, as FNIRT clobbers the
        # sform section of the NIFTI header
        # to store other data.
        #
        # TODO Nibabel <= 2.1.0 has a bug in header.get
        #      for fields with a value of 0. When this
        #      bug gets fixed, we can replace the if-else
        #      block below with this:
        #
        #          intent = header.get('intent_code', -1)
        #          qform  = header.get('qform_code',  -1)
        #          sform  = header.get('sform_code',  -1)
        #
        if isinstance(header, nib.nifti1.Nifti1Header):
            intent = header['intent_code']
            qform  = header['qform_code']
            sform  = header['sform_code']
        else:
            intent = -1
            qform  = -1
            sform  = -1

        if intent in (constants.FSL_FNIRT_DISPLACEMENT_FIELD,
                      constants.FSL_CUBIC_SPLINE_COEFFICIENTS,
                      constants.FSL_DCT_COEFFICIENTS,
                      constants.FSL_QUADRATIC_SPLINE_COEFFICIENTS):
            log.debug('FNIRT output image detected - using qform matrix')
            voxToWorldMat = np.array(header.get_qform())

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
            voxToWorldMat = transform.scaleOffsetXform(pixdims, 0)

        # Otherwise we let nibabel decide
        # which transform to use.
        else:
            voxToWorldMat = np.array(header.get_best_affine())

        return voxToWorldMat


    def __determineShape(self, header):
        """This method is called by :meth:`__init__`. It figures out the actual
        shape of the image data, and the zooms/pixdims for each data axis. Any
        empty trailing dimensions are squeezed, but the returned shape is
        guaranteed to be at least 3 dimensions. Returns:

         - A sequence/tuple containing the image shape, as reported in the
           header.
         - A sequence/tuple containing the effective image shape.
         - A sequence/tuple containing the zooms/pixdims.
        """

        # The canonicalShape method figures out
        # the data shape that we should use.
        origShape = list(header.get_data_shape())
        shape     = imagewrapper.canonicalShape(origShape)
        pixdims   = list(header.get_zooms())

        # if get_zooms() doesn't return at
        # least len(shape) values, we'll
        # fall back to the pixdim field in
        # the header.
        if len(pixdims) < len(shape):
            pixdims = header['pixdim'][1:]

        pixdims = pixdims[:len(shape)]

        return origShape, shape, pixdims


    def strval(self, key):
        """Returns the specified NIFTI header field, converted to a python
        string, correctly null-terminated, and with non-printable characters
        removed.

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

        try:    val = bytes(val).partition(b'\0')[0]
        except: val = bytes(val)

        val = val.decode('ascii')

        return ''.join([c for c in val if c in string.printable]).strip()


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
        """Returns a tuple containing the image data shape. """
        return tuple(self.__shape)


    @property
    def pixdim(self):
        """Returns a tuple containing the image pixdims (voxel sizes)."""
        return tuple(self.__pixdim)


    @property
    def intent(self):
        """Returns the NIFTI intent code of this image.
        """
        return self.__intent


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


    @property
    def worldToVoxMat(self):
        """Returns a ``numpy`` array of shape ``(4, 4)`` containing an
        affine transformation from world coordinates to voxel coordinates.
        """
        return np.array(self.__worldToVoxMat)


    @property
    def voxToWorldMat(self):
        """Returns a ``numpy`` array of shape ``(4, 4)`` containing an
        affine transformation from voxel coordinates to world coordinates.
        """
        return np.array(self.__voxToWorldMat)


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

        self.__voxToWorldMat = self.__determineTransform(header)
        self.__worldToVoxMat = transform.invert(self.__voxToWorldMat)

        log.debug('Affine changed:\npixdims: '
                  '{}\nsform: {}\nqform: {}'.format(
                      header.get_zooms(),
                      header.get_sform(),
                      header.get_qform()))

        self.notify(topic='transform')


    def mapIndices(self, sliceobj):
        """Adjusts the given slice object so that it may be used to index the
        underlying ``nibabel`` NIFTI image object.

        See the :meth:`__determineShape` method.

        :arg sliceobj: Something that can be used to slice a
                       multi-dimensional array, e.g. ``arr[sliceobj]``.
        """

        # How convenient - nibabel has a function
        # that does the dirty work for us.
        return fileslice.canonical_slicers(sliceobj, self.__origShape)


    # TODO: Remove this method, and use the shape attribute directly
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise. """
        return len(self.__shape) > 3 and self.__shape[3] > 1


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

        # Invalid values
        if code not in range(5):
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


    @memoize.Instanceify(memoize.memoize)
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
        import numpy.linalg as npla
        return npla.det(self.__voxToWorldMat) > 0


    @memoize.Instanceify(memoize.memoize)
    def voxelsToScaledVoxels(self):
        """Returns a transformation matrix which transforms from voxel
        coordinates into scaled voxel coordinates, with a left-right flip
        if the image appears to be stored in neurological order.

        See http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the\
        _format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to\
        _the_transformation_parameters.3F
        """

        shape          = list(self.shape[ :3])
        pixdim         = list(self.pixdim[:3])
        voxToPixdimMat = np.diag(pixdim + [1.0])

        if self.isNeurological():
            x              = (shape[0] - 1) * pixdim[0]
            flip           = transform.scaleOffsetXform([-1, 1, 1], [x, 0, 0])
            voxToPixdimMat = transform.concat(flip, voxToPixdimMat)

        return voxToPixdimMat


    def sameSpace(self, other):
        """Returns ``True`` if the ``other`` image (assumed to be a
        :class:`Nifti` instance) has the same dimensions and is in the
        same space as this image.
        """
        return np.all(np.isclose(self .__shape[:3],
                                 other.__shape[:3]))  and \
               np.all(np.isclose(self .__pixdim[:3],
                                 other.__pixdim[:3])) and \
               np.all(np.isclose(self .__voxToWorldMat,
                                 other.__voxToWorldMat))


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


class Image(Nifti):
    """Class which represents a 3D/4D NIFTI image. Internally, the image is
    loaded/stored using a :mod:`nibabel.nifti1.Nifti1Image` or
    :mod:`nibabel.nifti2.Nifti2Image`, and data access managed by a
    :class:`.ImageWrapper`.


    In addition to the attributes added by the :meth:`Nifti.__init__` method,
    the following attributes/properties are present on an ``Image`` instance
    as properties (https://docs.python.org/2/library/functions.html#property):


    ============== ===========================================================
    ``name``       The name of this ``Image`` - defaults to the image
                   file name, sans-suffix.

    ``dataSource`` The data source of this ``Image`` - the name of the
                   file from where it was loaded, or some other string
                   describing its origin.

    ``nibImage``   A reference to the ``nibabel`` NIFTI image object.

    ``saveState``  A boolean value which is ``True`` if this image is
                   saved to disk, ``False`` if it is in-memory, or has
                   been edited.

    ``dataRange``  The minimum/maximum values in the image. Depending upon
                   the value of the ``calcRange`` parameter to
                   :meth:`__init__`, this may be calculated when the ``Image``
                   is created, or may be incrementally updated as more image
                   data is loaded from disk.
    ============== ===========================================================


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

    ``'dataRange'`` This topic is notified whenever the image data range
                    is changed/adjusted.
    =============== ======================================================
    """


    def __init__(self,
                 image,
                 name=None,
                 header=None,
                 xform=None,
                 loadData=True,
                 calcRange=True,
                 indexed=False,
                 threaded=False,
                 **kwargs):
        """Create an ``Image`` object with the given image data or file name.

        :arg image:     A string containing the name of an image file to load,
                        or a :mod:`numpy` array, or a :mod:`nibabel` image
                        object.

        :arg name:      A name for the image.

        :arg header:    If not ``None``, assumed to be a
                        :class:`nibabel.nifti1.Nifti1Header` or
                        :class:`nibabel.nifti2.Nifti2Header` to be used as the
                        image header. Not applied to images loaded from file,
                        or existing :mod:`nibabel` images.

        :arg xform:     A :math:`4\\times 4` affine transformation matrix
                        which transforms voxel coordinates into real world
                        coordinates. If not provided, and a ``header`` is
                        provided, the transformation in the header is used.
                        If neither a ``xform`` nor a ``header`` are provided,
                        an identity matrix is used.

        :arg loadData:  If ``True`` (the default) the image data is loaded
                        in to memory.  Otherwise, only the image header
                        information is read, and the image data is kept
                        from disk. In either case, the image data is
                        accessed through an :class:`.ImageWrapper` instance.
                        The data may be loaded into memory later on via the
                        :meth:`loadData` method.

        :arg calcRange: If ``True`` (the default), the image range is
                        calculated immediately (vi a call to
                        :meth:`calcRange`). Otherwise, the image range is
                        incrementally updated as more data is read from memory
                        or disk.

        :arg indexed:   If ``True``, and the file is gzipped, it is opened
                        using the :mod:`indexed_gzip` package. Otherwise the
                        file is opened by ``nibabel``. Ignored if ``loadData``
                        is ``True``.

        :arg threaded:  If ``True``, the :class:`.ImageWrapper` will use a
                        separate thread for data range calculation. Defaults
                        to ``False``. Ignored if ``loadData`` is ``True``.

        All other arguments are passed through to the ``nibabel.load`` function
        (if it is called).
        """

        nibImage   = None
        dataSource = None
        fileobj    = None

        if loadData:
            indexed  = False
            threaded = False

        # The image parameter may be the name of an image file
        if isinstance(image, six.string_types):

            image = op.abspath(addExt(image))

            # Use indexed_gzip to open gzip files
            # if requested - this provides fast
            # on-disk access to the compressed
            # data.
            #
            # If using indexed_gzip, we store a
            # ref to the file object - we'll close
            # it when we are destroyed.
            if indexed and image.endswith('.gz'):
                nibImage, fileobj = loadIndexedImageFile(image)

            # Otherwise we let nibabel
            # manage the file reference(s)
            else:
                nibImage  = nib.load(image, **kwargs)

            dataSource = image

        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):

            if xform is None:
                if header is not None: xform = header.get_best_affine()
                else:                  xform = np.identity(4)

            # We default to NIFTI1 and not
            # NIFTI2, because the rest of
            # FSL is not yet NIFTI2 compatible.
            if header is None:
                ctr = nib.nifti1.Nifti1Image

            # But if a nibabel header has been provided,
            # we use the corresponding image type
            if isinstance(header, nib.nifti2.Nifti2Header):
                ctr = nib.nifti2.Nifti2Image
            elif isinstance(header, nib.nifti1.Nifti1Header):
                ctr = nib.nifti1.Nifti1Image
            elif isinstance(header, nib.analyze.AnalyzeHeader):
                ctr = nib.analyze.AnalyzeImage

            nibImage = ctr(image, xform, header=header)

        # otherwise, we assume that it is a nibabel image
        else:
            nibImage = image

        # Figure out the name of this image, if
        # it has not beenbeen explicitly passed in
        if name is None:

            # If this image was loaded
            # from disk, use the file name.
            if isinstance(image, six.string_types):
                name = removeExt(op.basename(image))

            # Or the image was created from a numpy array
            elif isinstance(image, np.ndarray):
                name = 'Numpy array'

            # Or image from a nibabel image
            else:
                name = 'Nibabel image'

        Nifti.__init__(self, nibImage.get_header())

        self.name                = name
        self.__lName             = '{}_{}'.format(id(self), self.name)
        self.__dataSource        = dataSource
        self.__fileobj           = fileobj
        self.__threaded          = threaded
        self.__nibImage          = nibImage
        self.__saveState         = dataSource is not None
        self.__imageWrapper      = imagewrapper.ImageWrapper(self.nibImage,
                                                             self.name,
                                                             loadData=loadData,
                                                             threaded=threaded)

        # Listen to ourself for changes
        # to the voxToWorldMat, so we
        # can update the saveState.
        self.register(self.name, self.__transformChanged, topic='transform')

        if calcRange:
            self.calcRange()

        self.__imageWrapper.register(self.__lName, self.__dataRangeChanged)


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

        self.__nibImage     = None
        self.__imageWrapper = None

        if getattr(self, '__fileobj', None) is not None:
            self.__fileobj.close()


    def getImageWrapper(self):
        """Returns the :class:`.ImageWrapper` instance used to manage
        access to the image data.
        """
        return self.__imageWrapper


    @property
    def dataSource(self):
        """Returns the data source (e.g. file name) that this ``Image`` was
        loaded from (``None`` if this image only exists in memory).
        """
        return self.__dataSource


    @property
    def nibImage(self):
        """Returns a reference to the ``nibabel`` NIFTI image instance.
        """
        return self.__nibImage


    @property
    def saveState(self):
        """Returns ``True`` if this ``Image`` has been saved to disk, ``False``
        otherwise.
        """
        return self.__saveState


    @property
    def dataRange(self):
        """Returns the image data range as a  ``(min, max)`` tuple. If the
        ``calcRange`` parameter to :meth:`__init__` was ``False``, these
        values may not be accurate, and may change as more image data is
        accessed.

        If the data range has not been no data has been accessed,
        ``(None, None)`` is returned.
        """
        if self.__imageWrapper is None: drange = (None, None)
        else:                           drange = self.__imageWrapper.dataRange

        # Fall back to the cal_min/max
        # fields in the NIFTI header
        # if we don't yet know anything
        # about the image data range.
        if drange[0] is None or drange[1] is None:
            drange = (float(self.header['cal_min']),
                      float(self.header['cal_max']))

        return drange


    @property
    def dtype(self):
        """Returns the ``numpy`` data type of the image data. """

        # Get the data type from the
        # first voxel in the image
        coords = [0] * len(self.__nibImage.shape)
        return self.__nibImage.dataobj[tuple(coords)].dtype


    @Nifti.voxToWorldMat.setter
    def voxToWorldMat(self, xform):
        """Overrides the :meth:`Nifti.voxToWorldMat` property setter.
        In ``nibabel``, the header and image affines can easily get
        out of sync when they are modified. The ``Nifti`` implementation
        updates the header, and this implementation makes sure the
        image is also updated.
        """

        Nifti.voxToWorldMat.fset(self, xform)

        xform =     self.voxToWorldMat
        code  = int(self.header['sform_code'])

        self.__nibImage.set_sform(xform, code)


    def __transformChanged(self, *args, **kwargs):
        """Called when the ``voxToWorldMat`` of this :class:`Nifti` instance
        changes. Updates the :attr:`saveState` accordinbgly.
        """
        if self.__saveState:
            self.__saveState = False
            self.notify(topic='saveState')


    def __dataRangeChanged(self, *args, **kwargs):
        """Called when the :class:`.ImageWrapper` data range changes.
        Notifies any listeners of this ``Image`` (registered through the
        :class:`.Notifier` interface) on the ``'dataRange'`` topic.
        """
        self.notify(topic='dataRange')


    def calcRange(self, sizethres=None):
        """Forces calculation of the image data range.

        :arg sizethres: If not ``None``, specifies an image size threshold
                        (total number of bytes). If the number of bytes in
                        the image is greater than this threshold, the range
                        is calculated on a sample (the first volume for a
                        4D image, or slice for a 3D image).
        """

        # The ImageWrapper automatically calculates
        # the range of the specified slice, whenever
        # it gets indexed. All we have to do is
        # access a portion of the data to trigger the
        # range calculation.
        nbytes = np.prod(self.shape) * self.dtype.itemsize

        # If an image size threshold has not been specified,
        # then we'll calculate the full data range right now.
        if sizethres is None or nbytes < sizethres:
            log.debug('{}: Forcing calculation of full '
                      'data range'.format(self.name))
            self.__imageWrapper[:]

        else:
            log.debug('{}: Calculating data range '
                      'from sample'.format(self.name))

            # Otherwise if the number of values in the
            # image is bigger than the size threshold,
            # we'll calculate the range from a sample:
            if len(self.shape) == 3: self.__imageWrapper[:, :, 0]
            else:                    self.__imageWrapper[:, :, :, 0]


    def loadData(self):
        """Makes sure that the image data is loaded into memory.
        See :meth:`.ImageWrapper.loadData`.
        """
        self.__imageWrapper.loadData()


    def save(self, filename=None):
        """Saves this ``Image`` to the specifed file, or the :attr:`dataSource`
        if ``filename`` is ``None``.
        """

        if self.__dataSource is None and filename is None:
            raise ValueError('A file name must be specified')

        if filename is None:
            filename = self.__dataSource

        filename = op.abspath(filename)

        log.debug('Saving {} to {}'.format(self.name, filename))

        # If this Image is not managing its
        # own file object, nibabel does all
        # of the hard work.
        if self.__fileobj is None:
            nib.save(self.__nibImage, filename)

        # Otherwise we've got our own file
        # handle to an IndexedGzipFile
        else:
            # Currently indexed_gzip does not support
            # writing. So we're going to use nibabel
            # to save the image, then close and re-open
            # the file.
            #
            # Unfortunately this means that we'll
            # lose the file index (and fast random
            # access) - I'll fix this when I get a
            # chance to work on indexed_gzip a bit
            # more.
            #
            # Hopefully I should be able to add write
            # support to indexed_gzip, such that it
            # re-builds the index while writing the
            # compressed data. And then be able to
            # transfer the index generated from the
            # write to a new read-only file handle.
            nib.save(self.__nibImage, filename)
            self.__fileobj.close()
            self.__nibImage, self.__fileobj = loadIndexedImageFile(filename)
            self.header = self.__nibImage.get_header()

            # We have to create a new ImageWrapper
            # instance too, as we have just destroyed
            # the nibabel image we gave to the last
            # one.
            self.__imageWrapper.deregister(self.__lName)
            self.__imageWrapper = imagewrapper.ImageWrapper(
                self.nibImage,
                self.name,
                loadData=False,
                dataRange=self.dataRange,
                threaded=self.__threaded)
            self.__imageWrapper.register(self.__lName, self.__dataRangeChanged)

        self.__dataSource = filename
        self.__saveState  = True

        self.notify(topic='saveState')


    def __getitem__(self, sliceobj):
        """Access the image data with the specified ``sliceobj``.

        :arg sliceobj: Something which can slice the image data.
        """

        log.debug('{}: __getitem__ [{}]'.format(self.name, sliceobj))

        return self.__imageWrapper.__getitem__(sliceobj)


    def __setitem__(self, sliceobj, values):
        """Set the image data at ``sliceobj`` to ``values``.

        :arg sliceobj: Something which can slice the image data.
        :arg values:   New image data.

        .. note:: Modifying image data will force the entire image to be
                  loaded into memory if it has not already been loaded.
        """
        values = np.array(values)

        log.debug('{}: __setitem__ [{} = {}]'.format(self.name,
                                                     sliceobj,
                                                     values.shape))

        with self.__imageWrapper.skip(self.__lName):

            oldRange = self.__imageWrapper.dataRange
            self.__imageWrapper.__setitem__(sliceobj, values)
            newRange = self.__imageWrapper.dataRange

        if values.size > 0:

            self.notify(topic='data', value=sliceobj)

            if self.__saveState:
                self.__saveState = False
                self.notify(topic='saveState')

            if not np.all(np.isclose(oldRange, newRange)):
                self.notify(topic='dataRange')


ALLOWED_EXTENSIONS = ['.nii.gz', '.nii', '.img', '.hdr', '.img.gz', '.hdr.gz']
"""The file extensions which we understand. This list is used as the default
if the ``allowedExts`` parameter is not passed to any of the functions
below.
"""


EXTENSION_DESCRIPTIONS = ['Compressed NIFTI images',
                          'NIFTI images',
                          'ANALYZE75 images',
                          'NIFTI/ANALYZE75 headers',
                          'Compressed NIFTI/ANALYZE75 images',
                          'Compressed NIFTI/ANALYZE75 headers']
"""Descriptions for each of the extensions in :data:`ALLOWED_EXTENSIONS`. """


FILE_GROUPS = [('.img',    '.hdr'),
               ('.img.gz', '.hdr.gz')]
"""File suffix groups used by :func:`addExt` to resolve file path
ambiguities - see :func:`fsl.utils.path.addExt`.
"""


PathError = fslpath.PathError
"""Error raised by :mod:`fsl.utils.path` functions when an error occurs.
Made available in this module for convenience.
"""


def looksLikeImage(filename, allowedExts=None):
    """Returns ``True`` if the given file looks like an image, ``False``
    otherwise.

    .. note:: The ``filename`` cannot just be a file prefix - it must
              include the file suffix (e.g. ``myfile.nii.gz``, not
              ``myfile``).

    :arg filename:    The file name to test.

    :arg allowedExts: A list of strings containing the allowed file
                      extensions - defaults to :attr:`ALLOWED_EXTENSIONS`.
    """

    if allowedExts is None: allowedExts = ALLOWED_EXTENSIONS

    # TODO A much more robust approach would be
    #      to try loading the file using nibabel.

    return any([filename.endswith(ext) for ext in allowedExts])


def addExt(prefix, mustExist=True):
    """Adds a file extension to the given file ``prefix``.  See
    :func:`~fsl.utils.path.addExt`.
    """
    return fslpath.addExt(prefix,
                          ALLOWED_EXTENSIONS,
                          mustExist,
                          defaultExt(),
                          fileGroups=FILE_GROUPS)


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


def defaultExt():
    """Returns the default NIFTI file extension that should be used.

    If the ``$FSLOUTPUTTYPE`` variable is set, its value is used.
    Otherwise, ``.nii.gz`` is returned.
    """

    # TODO: Add analyze support.
    options = {
        'NIFTI'      : '.nii',
        'NIFTI_PAIR' : '.img',
        'NIFTI_GZ'   : '.nii.gz',
    }

    outputType = os.environ.get('FSLOUTPUTTYPE', 'NIFTI_GZ')

    return options.get(outputType, '.nii.gz')


def loadIndexedImageFile(filename):
    """Loads the given image file using ``nibabel`` and ``indexed_gzip``.

    Returns a tuple containing the ``nibabel`` NIFTI image, and the open
    ``IndexedGzipFile`` handle.
    """

    import                 threading
    import indexed_gzip as igzip

    log.debug('Loading {} using indexed gzip'.format(filename))

    # guessed_image_type returns a
    # ref to one of the Nifti1Image
    # or Nifti2Image classes.
    ftype = nib.loadsave.guessed_image_type(filename)
    fobj  = igzip.SafeIndexedGzipFile(
        filename=filename,
        spacing=4194304,
        readbuf_size=1048576)

    # See the read_segments
    # function below
    fobj._arrayproxy_lock = threading.Lock()

    fmap = ftype.make_file_map()
    fmap['image'].fileobj = fobj
    image = ftype.from_file_map(fmap)

    return image, fobj


def read_segments(fileobj, segments, n_bytes):
    """This function is used in place of the
    ``nibabel.fileslice.read_segments`` function to ensure thread-safe read
    access to image data via the ``nibabel.arrayproxy.ArrayProxy`` (the
    ``dataobj`` attribute of a ``nibabel`` image).

    The ``nibabel`` implementation uses multiple calls to ``seek`` and
    ``read`` to read segments of data from the file. When accessed by multiple
    threads, these seeks and reads can become intertwined, which causes a read
    from one thread to read data from the seek location requested by the other
    thread.

    This implementation protects the seek/read pairs with a
    ``threading.Lock``, which is added to ``IndexedGzipFile`` instances that
    are created in the :func:`loadIndexedImageFile` function.
    """

    from mmap import mmap

    try:
        # fileobj is a nibabel.openers.ImageOpener - the
        # actual file is available via the fobj attribute
        lock = getattr(fileobj.fobj, '_arrayproxy_lock')

    except:
        return fileslice.orig_read_segments(fileobj, segments, n_bytes)

    if len(segments) == 0:
        if n_bytes != 0:
            raise ValueError("No segments, but non-zero n_bytes")
        return b''
    if len(segments) == 1:
        offset, length = segments[0]

        lock.acquire()
        try:
            fileobj.seek(offset)
            bytes = fileobj.read(length)
        finally:
            lock.release()

        if len(bytes) != n_bytes:
            raise ValueError("Whoops, not enough data in file")
        return bytes

    # More than one segment
    bytes = mmap(-1, n_bytes)
    for offset, length in segments:

        lock.acquire()
        try:
            fileobj.seek(offset)
            bytes.write(fileobj.read(length))
        finally:
            lock.release()

    if bytes.tell() != n_bytes:
        raise ValueError("Oh dear, n_bytes does not look right")
    return bytes


# Monkey-patch the above implementation into nibabel
fileslice.orig_read_segments = fileslice.read_segments
fileslice.read_segments      = read_segments
