#!/usr/bin/env python
# 
# image.py - Provides the :class:`Image` class, for representing 3D/4D NIFTI
#            images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`Nifti1` and :class:`Image` classes, for
representing 3D/4D NIFTI1 images. The ``nibabel`` package is used for file
I/O.

.. note:: Currently, only NIFTI1 images are supported.


It is very easy to load a NIFTI image::

    from fsl.data.image import Image
    myimg = Image('MNI152_T1_2mm.nii.gz')


A handful of other functions are also provided for working with image files
and file names:

.. autosummary::
   :nosignatures:

   looksLikeImage
   removeExt
   addExt
   loadIndexedImageFile
"""


import               logging
import os.path    as op

import               six 
import numpy      as np


import fsl.utils.transform   as transform
import fsl.utils.notifier    as notifier
import fsl.utils.path        as fslpath
import fsl.data.constants    as constants
import fsl.data.imagewrapper as imagewrapper


log = logging.getLogger(__name__)


class Nifti1(object):
    """The ``Nifti1`` class is intended to be used as a base class for
    things which either are, or are associated with, a NIFTI1 image.
    The ``Nifti1`` class is intended to represent information stored in
    the header of a NIFTI1 file - if you want to load the data from
    a file, use the :class:`Image` class instead.


    When a ``Nifti1`` instance is created, it adds the following attributes
    to itself:

    
    ================= ====================================================
    ``header``        The :mod:`nibabel.Nifti1Header` object.
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
    ================= ====================================================

    
    .. note:: The ``shape`` attribute may not precisely match the image shape
              as reported in the NIFTI1 header, because trailing dimensions of
              size 1 are squeezed out. See the :meth:`__determineShape` and
              :meth:`mapIndices` methods.
    """

    def __init__(self, header):
        """Create a ``Nifti1`` object.

        :arg header:   A :class:`nibabel.nifti1.Nifti1Header` to be used as 
                       the image header. 
        """

        header                   = header.copy()
        origShape, shape, pixdim = self.__determineShape(header)

        if len(shape) < 3 or len(shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        # We have to treat FSL/FNIRT images
        # specially, as FNIRT clobbers the
        # sform section of the NIFTI header
        # to store other data. The hard coded
        # numbers here are the intent codes
        # output by FNIRT.
        intent = header.get('intent_code', -1)
        if intent in (2006, 2007, 2008, 2009):
            log.debug('FNIRT output image detected - using qform matrix')
            voxToWorldMat = np.array(header.get_qform())

        # Otherwise we let nibabel decide
        # which transform to use.
        else:
            voxToWorldMat = np.array(header.get_best_affine())

        worldToVoxMat = transform.invert(voxToWorldMat)

        self.header        = header
        self.shape         = shape
        self.__origShape   = origShape
        self.pixdim        = pixdim
        self.voxToWorldMat = voxToWorldMat
        self.worldToVoxMat = worldToVoxMat


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

        origShape = list(header.get_data_shape())
        shape     = list(origShape)
        pixdims   = list(header.get_zooms())

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

        # The same goes for the pixdim - if get_zooms()
        # doesn't return at least 3 values, we'll fall
        # back to the pixdim field in the header.
        if len(pixdims) < 3:
            pixdims = header['pixdim'][1:]

        pixdims = pixdims[:len(shape)]
        
        return origShape, shape, pixdims


    def mapIndices(self, sliceobj):
        """Adjusts the given slice object so that it may be used to index the
        underlying ``nibabel.Nifti1Image` object.

        See the :meth:`__determineShape` method.

        :arg sliceobj: Something that can be used to slice a
                       multi-dimensional array, e.g. ``arr[sliceobj]``.
        """

        # How convenient - nibabel has a function
        # that does the dirty work for us.
        import nibabel.fileslice as fileslice
        return fileslice.canonical_slicers(sliceobj, self.__origShape)
 
        
    # TODO: Remove this method, and use the shape attribute directly
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise. """
        return len(self.shape) > 3 and self.shape[3] > 1 

    
    def getXFormCode(self, code=None):
        """This method returns the code contained in the NIFTI1 header,
        indicating the space to which the (transformed) image is oriented.

        The ``code`` parameter may be either ``sform`` (the default) or
        ``qform`` in which case the corresponding matrix is used.

        :returns: one of the following codes:
                    - :data:`~.constants.NIFTI_XFORM_UNKNOWN`
                    - :data:`~.constants.NIFTI_XFORM_SCANNER_ANAT`
                    - :data:`~.constants.NIFTI_XFORM_ALIGNED_ANAT`
                    - :data:`~.constants.NIFTI_XFORM_TALAIRACH`
                    - :data:`~.constants.NIFTI_XFORM_MNI_152`
        """

        if   code is None:     code = 'sform_code'
        elif code == 'sform' : code = 'sform_code'
        elif code == 'qform' : code = 'qform_code'
        else: raise ValueError('code must be None, sform, or qform')

        code = self.header[code]

        # Invalid values
        if   code > 4: code = constants.NIFTI_XFORM_UNKNOWN
        elif code < 0: code = constants.NIFTI_XFORM_UNKNOWN
        
        return int(code)


    def axisMapping(self, xform):
        """Returns the (approximate) correspondence of each axis in the source
        coordinate system to the axes in the destination coordinate system,
        where the source and destinations are defined by the given affine
        transformation matrix.
        """

        import nibabel as nib

        inaxes = [[-1, 1], [-2, 2], [-3, 3]]

        return nib.orientations.aff2axcodes(xform, inaxes)


    def isNeurological(self):
        """Returns ``True`` if it looks like this ``Nifti1`` object is in
        neurological orientation, ``False`` otherwise. This test is purely
        based on the determinent of the voxel-to-mm transformation matrix -
        if it has a positive determinant, the image is assumed to be in
        neurological orientation, otherwise it is assumed to be in
        radiological orientation.

        See http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FLIRT/FAQ#What_is_the\
        _format_of_the_matrix_used_by_FLIRT.2C_and_how_does_it_relate_to\
        _the_transformation_parameters.3F
        """
        import numpy.linalg as npla
        return npla.det(self.voxToWorldMat) > 0


    def getOrientation(self, axis, xform):
        """Returns a code representing the orientation of the specified data
        axis in the coordinate system defined by the given transformation
        matrix.

        :arg xform: A transformation matrix which is assumed to transform
                    coordinates from the image world coordinate system to
                    some other coordinate system.

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
        
        import nibabel as nib
        code = nib.orientations.aff2axcodes(
            xform,
            ((constants.ORIENT_R2L, constants.ORIENT_L2R),
             (constants.ORIENT_A2P, constants.ORIENT_P2A),
             (constants.ORIENT_S2I, constants.ORIENT_I2S)))[axis]

        return code 


class Image(Nifti1, notifier.Notifier):
    """Class which represents a 3D/4D NIFTI1 image. Internally, the image
    is loaded/stored using a :mod:`nibabel.nifti1.Nifti1Image`, and data
    access managed by a :class:`.ImageWrapper`.

    
    In addition to the attributes added by the :meth:`Nifti1.__init__` method,
    the following attributes/properties are present on an ``Image`` instance 
    as properties (https://docs.python.org/2/library/functions.html#property):


    ============== ======================================================
    ``name``       The name of this ``Image`` - defaults to the image
                   file name, sans-suffix.

    ``dataSource`` The data source of this ``Image`` - the name of the
                   file from where it was loaded, or some other string
                   describing its origin.

    ``nibImage``   A reference to the ``nibabel.Nifti1Image`` object.
    
    ``saveState``  A boolean value which is ``True`` if this image is
                   saved to disk, ``False`` if it is in-memory, or has
                   been edited.
    
    ``dataRange``  The minimum/maximum values in the image. Depending upon
                   the value of the ``calcRange`` parameter to
                   :meth:`__init__`, this may be calculated when the ``Image``
                   is created, or may be incrementally updated as more image 
                   data is loaded from disk.
    ============== ======================================================

    
    The ``Image`` class implements the :class:`.Notifier` interface -
    listeners may register to be notified of changes to the above properties,
    by registering on the following _topic_ names (see the :class:`.Notifier`
    class documentation):

    
    =============== ======================================================
    ``'data'``      This topic is notified whenever the image data changes
                    (via the :meth:`__setitem__` method).
    
    ``'saveState'`` This topic is notified whenever the saved state of the
                    image changes (i.e. it is edited, or saved to disk).
    
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
                 indexed=False):
        """Create an ``Image`` object with the given image data or file name.

        :arg image:     A string containing the name of an image file to load, 
                        or a :mod:`numpy` array, or a :mod:`nibabel` image
                        object.

        :arg name:      A name for the image.

        :arg header:    If not ``None``, assumed to be a
                        :class:`nibabel.nifti1.Nifti1Header` to be used as the 
                        image header. Not applied to images loaded from file,
                        or existing :mod:`nibabel` images.

        :arg xform:     A :math:`4\\times 4` affine transformation matrix 
                        which transforms voxel coordinates into real world
                        coordinates. Only used if ``image`` is a ``numpy``
                        array, and ``header`` is ``None``.

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
                        file is opened by ``nibabel``.
        """

        import nibabel as nib

        nibImage   = None
        dataSource = None
        fileobj    = None

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
                nibImage  = nib.load(image)
                
            dataSource = image
 
        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):

            if   header is not None: xform = header.get_best_affine()
            elif xform  is     None: xform = np.identity(4)
                    
            nibImage = nib.nifti1.Nifti1Image(image,
                                              xform,
                                              header=header)
            
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
 
        Nifti1.__init__(self, nibImage.get_header())

        self.name                = name
        self.__dataSource        = dataSource
        self.__fileobj           = fileobj
        self.__nibImage          = nibImage
        self.__saveState         = dataSource is not None
        self.__suppressDataRange = False
        self.__imageWrapper      = imagewrapper.ImageWrapper(self.nibImage,
                                                             self.name,
                                                             loadData=loadData)

        if calcRange:
            self.calcRange()

        self.__imageWrapper.register(
            '{}_{}'.format(id(self), self.name),
            self.__dataRangeChanged) 

        
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
        """Closes any open file handles. """
        if self.__fileobj is not None:
            self.__fileobj.close()
        
    
    @property
    def dataSource(self):
        """Returns the data source (e.g. file name) that this ``Image`` was
        loaded from (``None`` if this image only exists in memory).
        """
        return self.__dataSource

    
    @property
    def nibImage(self):
        """Returns a reference to the ``nibabel.nifti1.Nifti1Image`` instance.
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
        # fields in the NIFTI1 header
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


    def __dataRangeChanged(self, *args, **kwargs):
        """Called when the :class:`.ImageWrapper` data range changes.
        Notifies any listeners of this ``Image`` (registered through the
        :class:`.Notifier` interface) on the ``'dataRange'`` topic.
        """
        if not self.__suppressDataRange:
            self.notify(notifier_topic='dataRange')


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

        import nibabel as nib
        
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

        self.__dataSource = filename
        self.__saveState  = True
        
        self.notify(notifier_topic='saveState')


    def __getitem__(self, sliceobj):
        """Access the image data with the specified ``sliceobj``.

        :arg sliceobj: Something which can slice the image data.
        """


        log.debug('{}: __getitem__ [{}]'.format(self.name, sliceobj))
        
        data = self.__imageWrapper.__getitem__(sliceobj)

        if len(data.shape) > len(self.shape):

            shape = data.shape[:len(self.shape)]
            data  = np.reshape(data, shape)

        return data


    def __setitem__(self, sliceobj, values):
        """Set the image data at ``sliceobj`` to ``values``.

        :arg sliceobj: Something which can slice the image data.
        :arg values:   New image data.

        .. note:: Modifying image data will force the entire image to be 
                  loaded into memory if it has not already been loaded.
        """

        log.debug('{}: __setitem__ [{} = {}]'.format(self.name,
                                                     sliceobj,
                                                     values.shape))

        self.__suppressDataRange = True
        oldRange = self.__imageWrapper.dataRange

        self.__imageWrapper.__setitem__(sliceobj, values)

        newRange = self.__imageWrapper.dataRange
        self.__suppressDataRange = False

        if values.size > 0:

            self.notify(notifier_topic='data')

            if self.__saveState:
                self.__saveState = False
                self.notify(notifier_topic='saveState')

            if not np.all(np.isclose(oldRange, newRange)):
                self.notify(notifier_topic='dataRange') 


# TODO The wx.FileDialog does not    
# seem to handle wildcards with      
# multiple suffixes (e.g. '.nii.gz'),
# so i'm just providing '*.gz'for now
ALLOWED_EXTENSIONS = ['.nii.gz', '.nii', '.img', '.hdr', '.img.gz', '.gz']
"""The file extensions which we understand. This list is used as the default
if the ``allowedExts`` parameter is not passed to any of the functions
below.
"""


EXTENSION_DESCRIPTIONS = ['Compressed NIFTI1 images',
                          'NIFTI1 images',
                          'ANALYZE75 images',
                          'NIFTI1/ANALYZE75 headers',
                          'Compressed NIFTI1/ANALYZE75 images',
                          'Compressed images']
"""Descriptions for each of the extensions in :data:`ALLOWED_EXTENSIONS`. """


DEFAULT_EXTENSION  = '.nii.gz'
"""The default file extension (TODO read this from ``$FSLOUTPUTTYPE``)."""


def looksLikeImage(filename, allowedExts=None):
    """Returns ``True`` if the given file looks like an image, ``False``
    otherwise.

    :arg filename:    The file name to test.
    
    :arg allowedExts: A list of strings containing the allowed file
                      extensions.
    """

    if allowedExts is None: allowedExts = ALLOWED_EXTENSIONS

    # TODO A much more robust approach would be
    #      to try loading the file using nibabel.

    return any([filename.endswith(ext) for ext in allowedExts])


def removeExt(filename):
    """Removes the extension from the given file name. Returns the filename
    unmodified if it does not have a supported extension.

    See :func:`~fsl.utils.path.removeExt`.

    :arg filename: The file name to strip.
    """
    return fslpath.removeExt(filename, ALLOWED_EXTENSIONS)


def addExt(prefix, mustExist=True):
    """Adds a file extension to the given file ``prefix``.

    See :func:`~fsl.utils.path.addExt`.
    """
    return fslpath.addExt(prefix,
                          ALLOWED_EXTENSIONS,
                          mustExist,
                          DEFAULT_EXTENSION)


def loadIndexedImageFile(filename):
    """Loads the given image file using ``nibabel`` and ``indexed_gzip``.

    Returns a tuple containing the ``Nifti1Image``, and the open
    ``IndexedGzipFile`` handle.
    """
    
    import nibabel      as nib
    import indexed_gzip as igzip

    log.debug('Loading {} using indexed gzip'.format(filename))

    fobj = igzip.IndexedGzipFile(
        filename=filename,
        spacing=4194304,
        readbuf_size=131072)

    fmap = nib.Nifti1Image.make_file_map()
    fmap['image'].fileobj = fobj
    image = nib.Nifti1Image.from_file_map(fmap)

    return image, fobj
