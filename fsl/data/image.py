#!/usr/bin/env python
#
# image.py - Classes for representing 3D/4D images and collections of said
# images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Classes for representing 3D/4D images and collections of said images."""

import os
import sys
import logging
import tempfile
import collections
import subprocess         as sp
import os.path            as op

import numpy              as np
import numpy.linalg       as linalg
import nibabel            as nib

import props

import fsl.data.imagefile as imagefile


log = logging.getLogger(__name__)

# Constants which represent the orientation of an axis,
# in either voxel or world space.
ORIENT_UNKNOWN = -1
ORIENT_L2R     = 0
ORIENT_R2L     = 1
ORIENT_P2A     = 2
ORIENT_A2P     = 3
ORIENT_I2S     = 4
ORIENT_S2I     = 5

# Constants from the NIFTI1 specification that define
# the 'space' in which an image is assumed to be.
NIFTI_XFORM_UNKNOWN      = 0
NIFTI_XFORM_SCANNER_ANAT = 1
NIFTI_XFORM_ALIGNED_ANAT = 2
NIFTI_XFORM_TALAIRACH    = 3
NIFTI_XFORM_MNI_152      = 4

def _loadImageFile(filename):
    """Given the name of an image file, loads it using nibabel.

    If the file is large, and is gzipped, it is decompressed to a temporary
    location, so that it can be memory-mapped.  A tuple is returned,
    consisting of the nibabel image object, and the name of the file that it
    was loaded from (either the passed-in file name, or the name of the
    temporary decompressed file).
    """

    # If we have a GUI, we can display a dialog
    # message. Otherwise we print a log message
    haveGui = False
    try:
        import wx
        if wx.GetApp() is not None: 
            haveGui = True
    except:
        pass

    realFilename = filename
    mbytes = op.getsize(filename) / 1048576.0

    # The mbytes limit is arbitrary
    if filename.endswith('.nii.gz') and mbytes > 512:

        unzipped, filename = tempfile.mkstemp(suffix='.nii')

        unzipped = os.fdopen(unzipped)

        msg = '{} is a large file ({} MB) - decompressing ' \
              'to {}, to allow memory mapping...'.format(realFilename,
                                                         mbytes,
                                                         filename)

        if not haveGui:
            log.info(msg)
        else:
            busyDlg = wx.BusyInfo(msg, wx.GetTopLevelWindows()[0])

        gzip = ['gzip', '-d', '-c', realFilename]
        log.debug('Running {} > {}'.format(' '.join(gzip), filename))

        # If the gzip call fails, revert to loading from the gzipped file
        try:
            sp.call(gzip, stdout=unzipped)
            unzipped.close()

        except OSError as e:
            log.warn('gzip call failed ({}) - cannot memory '
                     'map file: {}'.format(e, realFilename),
                     exc_info=True)
            unzipped.close()
            os.remove(filename)
            filename = realFilename

        if haveGui:
            busyDlg.Destroy()

    return nib.load(filename), filename


class Image(props.HasProperties):
    """Class which represents a 3D/4D image. Internally, the image is
    loaded/stored using :mod:`nibabel`.

    Arbitrary data may be associated with an :class:`Image` object, via the
    :meth:`getAttribute` and :meth:`setAttribute` methods (which are just
    front end wrappers around an internal ``dict`` object).

    The following attributes are present on an :class:`Image` object:

    :ivar nibImage:      The :mod:`nibabel` image object.
    
    :ivar data:          A reference to the image data, stored as a
                         :mod`numpy` array.
    
    :ivar shape:         A list/tuple containing the number of voxels
                         along each image dimension.
    
    :ivar pixdim:        A list/tuple containing the size of one voxel
                         along each image dimension.
    
    :ivar voxToWorldMat: A 4*4 array specifying the affine transformation
                         for transforming voxel coordinates into real world
                         coordinates.
    
    :ivar worldToVoxMat: A 4*4 array specifying the affine transformation
                         for transforming real world coordinates into voxel
                         coordinates.
    
    :ivar imageFile:     The name of the file that the image was loaded from.
    
    :ivar tempFile:      The name of the temporary file which was created (in
                         the event that the image was large and was gzipped -
                         see :func:`_loadImageFile`).
    """


    imageType = props.Choice(
        collections.OrderedDict([
            ('volume', '3D/4D volume'),
            ('circle', '3D/4D volume, where voxels are drawn as circles'),
            ('tensor', '3-direction tensor image')]),
        default='volume')
    """This property defines the type of image data."""

    
    transform = props.Choice(
        collections.OrderedDict([
            ('affine', 'Use qform/sform transformation matrix'),
            ('pixdim', 'Use pixdims only'),
            ('id',     'Do not use qform/sform or pixdims')]),
        default='pixdim')
    """This property defines how the image should be transformd into real world
    space.
    
      - ``affine``: Use the affine transformation matrix stored in the image
        (the ``qform``/``sform`` fields in NIFTI1 headers).
                    
      - ``pixdim``: Scale voxel sizes by the ``pixdim`` fields in the image
        header.
    
      - ``id``: Perform no scaling or transformation - voxels will be
        interpreted as :math:`1mm^3` isotropic, with the origin at voxel
        (0,0,0).
    """

    
    name = props.String()
    """The name of this image."""
    
        
    def __init__(self, image):
        """Initialise an Image object with the given image data or file name.

        :arg image: A string containing the name of an image file to load, or
                    a :mod:`numpy` array, or a :mod:`nibabel` image object.
        """

        # The image parameter may be the name of an image file
        if isinstance(image, basestring):
            
            nibImage, filename = _loadImageFile(imagefile.addExt(image))
            self.nibImage      = nibImage
            self.imageFile     = image

            # if the returned file name is not the same as
            # the provided file name, that means that the
            # image was opened from a temporary file
            if filename != image:
                self.name     = op.basename(self.imageFile)
                self.tempFile = nibImage.get_filename()
            else:
                self.name     = op.basename(self.imageFile)
                
        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):
            
            self.nibImage  = nib.nifti1.Nifti1Image(image, np.identity(4))
            self.name      = 'Numpy array'
            self.tempFile  = None
            self.imageFile = None
            
        # otherwise, we assume that it is a nibabel image
        else:
            self.nibImage  = image
            self.name      = 'Nibabel image'
            self.tempFile  = None
            self.imageFile = None 

        self.data     = self.nibImage.get_data()
        self.shape    = self.nibImage.get_shape()
        self.pixdim   = self.nibImage.get_header().get_zooms()

        self.addListener(
            'transform',
            '{}_{}'.format(self.__class__.__name__, self.name),
            self._transformChanged)

        self._transformChanged()

        if len(self.shape) < 3 or len(self.shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        # This dictionary may be used to store
        # arbitrary data associated with this image.
        self._attributes = {}


    def __str__(self):
        """Return a string representation of this :class:`Image`."""
        return '{}("{}")'.format(self.__class__.__name__, self.imageFile)

        
    def __repr__(self):
        """See the :meth:`__str__` method."""
        return self.__str__()


    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return len(self.shape) > 3 and self.shape[3] > 1 


    def _transformChanged(self, *a):
        """This method is called when the :attr:`transform` property value
        changes. It updates the :attr:`voxToWorldMat`, :attr:`worldToVoxMat`,
        and :attr:`pixdim` attributes to reflect the new transformation
        type.
        """

        if self.transform == 'affine':
            voxToWorldMat = self.nibImage.get_affine()
        elif self.transform == 'pixdim':
            pixdim        = self.nibImage.get_header().get_zooms()
            voxToWorldMat = np.diag([pixdim[0], pixdim[1], pixdim[2], 1.0])
        elif self.transform == 'id':
            voxToWorldMat = np.identity(4)

        self.voxToWorldMat = np.array(voxToWorldMat, dtype=np.float32)
        self.worldToVoxMat = linalg.inv(self.voxToWorldMat)

        self.voxToWorldMat = self.voxToWorldMat.transpose()
        self.worldToVoxMat = self.worldToVoxMat.transpose()

        if self.transform == 'affine':
            pixdim = [self.axisLength(ax) / self.shape[ax] for ax in range(3)]
        elif self.transform == 'pixdim':
            pixdim = self.nibImage.get_header().get_zooms()
        elif self.transform == 'id':
            pixdim = [1.0, 1.0, 1.0]

        self.pixdim = pixdim
 
        # for pixdim/identity transformations, we want the world
        # location (0, 0, 0) to map to voxel location (0, 0, 0)
        if self.transform in ['pixdim', 'id']:
            for i in range(3):
                self.voxToWorldMat[3, i] =  self.pixdim[i] * 0.5
                self.worldToVoxMat[3, i] = -0.5
 
        log.debug('Image {} transformation matrix changed: {}'.format(
            self.name, self.voxToWorldMat))
        log.debug('Inverted matrix: {}'.format(self.worldToVoxMat)) 


    def imageBounds(self, axis):
        """Return the bounds (min, max) of the image, in real world


        The returned bounds give the coordinates, along the specified axis, of
        a bounding box which contains the entire image.
        """

        x, y, z = self.shape[:3]

        x -= 0.5
        y -= 0.5
        z -= 0.5

        points = np.zeros((8, 3), dtype=np.float32)

        points[0, :] = [-0.5, -0.5, -0.5]
        points[1, :] = [-0.5, -0.5,  z]
        points[2, :] = [-0.5,  y,   -0.5]
        points[3, :] = [-0.5,  y,    z]
        points[4, :] = [x,    -0.5, -0.5]
        points[5, :] = [x,    -0.5,  z]
        points[6, :] = [x,     y,   -0.5]
        points[7, :] = [x,     y,    z]


        tx = self.voxToWorld(points)

        lo = tx[:, axis].min()
        hi = tx[:, axis].max()

        return (lo, hi)

        
    def axisLength(self, axis):
        """Return the length, in real world units, of the specified axis.
        """
        
        points          = np.zeros((2, 3), dtype=np.float32)
        points[:]       = [-0.5, -0.5, -0.5]
        points[1, axis] = self.shape[axis] - 0.5 

        tx = self.voxToWorld(points)

        # euclidean distance between each boundary point
        return sum((tx[0, :] - tx[1, :]) ** 2) ** 0.5


    def worldToVox(self, p, axes=None):
        """Transforms the given set of points in voxel coordinates to points
        in world coordinates, according to the current :attr:`transform`.

        The returned array is either a :class:`numpy.float64` array, or a
        single ``float`` value, depending on the input. There is no guarantee
        that the returned array of voxel coordinates is within the bounds of
        the image shape. Parameters:
        
        :arg p:    N*A array, where N is the number of points, and A
                   is the number of axes to consider (default: 3).
        
        :arg axes: If ``None``, it is assumed that the input p is a N*3
                   array, with each point being specified by x,y,z
                   coordinates. If a single value in the range (0-2),
                   it is assumed that p is a 1D array. Or, if a
                   sequence of 2 or 3 values, p must be an array of
                   N*2 or N*3, respectively.
        """

        voxp = self._transform(p, self.worldToVoxMat, axes)
        voxp = np.array(voxp, dtype=np.float64)

        if voxp.size == 1: return voxp[0]
        else:              return voxp


    def voxToWorld(self, p, axes=None):
        """Transforms the given set of points in world coordinates to
        points in voxel coordinates, according to the current
        :attr:`transform`.

        The returned array is either a :class:`numpy.float64` array,
        or a single ``float`` value, depending on the input. See the
        :meth:`worldToVox` method for more details.
        """

        worldp = self._transform(p, self.voxToWorldMat, axes)

        if worldp.size == 1: return float(worldp)
        else:                return worldp


    def getXFormCode(self):
        """This method returns the code contained in the NIFTI1 header,
        indicating the space to which the (transformed) image is oriented.
        
        """
        sform_code = self.nibImage.get_header()['sform_code']
        qform_code = self.nibImage.get_header()['qform_code']

        # if the qform and sform codes don't
        # match, I don't know what to do
        if   sform_code != qform_code: return NIFTI_XFORM_UNKNOWN

        # Invalid values
        elif sform_code > 4:           return NIFTI_XFORM_UNKNOWN
        elif sform_code < 0:           return NIFTI_XFORM_UNKNOWN

        # All is well
        else:                          return sform_code


    def getWorldOrientation(self, axis):
        """Returns a code representing the orientation of the specified axis
        in world space.

        This method returns one of the following values, indicating the
        direction in which coordinates along the specified axis increase:
          - :attr:`~fsl.data.image.ORIENT_L2R`:     Left to right
          - :attr:`~fsl.data.image.ORIENT_R2L`:     Right to left
          - :attr:`~fsl.data.image.ORIENT_A2P`:     Anterior to posterior
          - :attr:`~fsl.data.image.ORIENT_P2A`:     Posterior to anterior
          - :attr:`~fsl.data.image.ORIENT_I2S`:     Inferior to superior
          - :attr:`~fsl.data.image.ORIENT_S2I`:     Superior to inferior
          - :attr:`~fsl.data.image.ORIENT_UNKNOWN`: Orientation is unknown

        The returned value is dictated by the XForm code contained in the
        image file header (see the :meth:`getXFormCode` method). Basically,
        if the XForm code is 'unknown', this method will return -1 for all
        axes. Otherwise, it is assumed that the image is in RAS orientation
        (i.e. the X axis increases from left to right, the Y axis increases
        from  posterior to anterior, and the Z axis increases from inferior
        to superior).
        """

        if self.getXFormCode() == NIFTI_XFORM_UNKNOWN:
            return -1

        if   axis == 0: return ORIENT_L2R
        elif axis == 1: return ORIENT_P2A
        elif axis == 2: return ORIENT_I2S

        else: return -1


    def getVoxelOrientation(self, axis):
        """Returns a code representing the (estimated) orientation of the
        specified voxelwise axis.

        See the :meth:`getWorldOrientation` method for a description
        of the return value.
        """
        
        if self.getXFormCode() == NIFTI_XFORM_UNKNOWN:
            return -1 
        
        # the aff2axcodes returns one code for each 
        # axis in the image array (i.e. in voxel space),
        # which denotes the real world direction
        code = nib.orientations.aff2axcodes(self.nibImage.get_affine(),
                                            ((ORIENT_R2L, ORIENT_L2R),
                                             (ORIENT_A2P, ORIENT_P2A),
                                             (ORIENT_S2I, ORIENT_I2S)))[axis]
        return code

        
    def _transform(self, p, a, axes):
        """Used by the :meth:`worldToVox` and :meth:`voxToWorld` methods.
        
        Transforms the given set of points ``p`` according to the given affine
        transformation ``a``. The transformed points are returned as a
        :class:``numpy.float64`` array.
        """

        p = self._fillPoints(p, axes)
        t = np.zeros((len(p), 3), dtype=np.float64)

        x = p[:, 0]
        y = p[:, 1]
        z = p[:, 2]

        t[:, 0] = x * a[0, 0] + y * a[1, 0] + z * a[2, 0] + a[3, 0]
        t[:, 1] = x * a[0, 1] + y * a[1, 1] + z * a[2, 1] + a[3, 1]
        t[:, 2] = x * a[0, 2] + y * a[1, 2] + z * a[2, 2] + a[3, 2]

        if axes is None: axes = [0, 1, 2]

        return t[:, axes]


    def _fillPoints(self, p, axes):
        """Used by the :meth:`_transform` method. Turns the given array p into
        a N*3 array of x,y,z coordinates. The array p may be a 1D array, or an
        N*2 or N*3 array.
        """

        if not isinstance(p, collections.Iterable): p = [p]
        
        p = np.array(p)

        if axes is None: return p

        if not isinstance(axes, collections.Iterable): axes = [axes]

        if p.ndim == 1:
            p = p.reshape((len(p), 1))

        if p.ndim != 2:
            raise ValueError('Points array must be either one or two '
                             'dimensions')

        if len(axes) != p.shape[1]:
            raise ValueError('Points array shape does not match specified '
                             'number of axes')

        newp = np.zeros((len(p), 3), dtype=p.dtype)

        for i, ax in enumerate(axes):
            newp[:, ax] = p[:, i]

        return newp

        
    def getAttribute(self, name):
        """Retrieve the attribute with the given name.

        :raise KeyError: if there is no attribute with the given name.
        """
        return self._attributes[name]

    def delAttribute(self, name):
        """Delete and return the value of the attribute with the given name.

        :raise KeyError: if there is no attribute with the given name.
        """
        return self._attributes.pop(name)

        
    def setAttribute(self, name, value):
        """Set an attribute with the given name and the given value."""
        self._attributes[name] = value
        
        log.debug('Attribute set on {}: {} = {}'.format(
            self.name, name, str(value)))


class ImageList(props.HasProperties):
    """Class representing a collection of images to be displayed together.

    Contains a :class:`props.properties_types.List` property containing
    :class:`Image` objects, and some other properties on which listeners may
    register themselves to be notified when the properties of the image
    collection changes (e.g. image bounds).

    An :class:`ImageList` object has a few wrapper methods around the
    :attr:`images` property, allowing the :class:`ImageList` to be used
    as if it were a list itself.
    """

    def _validateImage(self, atts, images):
        """Returns ``True`` if all objects in the given ``images`` list are
        :class:`Image` objects, ``False`` otherwise.
        """
        return all(map(lambda img: isinstance(img, Image), images))


    images = props.List(validateFunc=_validateImage, allowInvalid=False)
    """A list of :class:`Image` objects. to be displayed"""

    
    bounds = props.Bounds(ndims=3)
    """This property contains the min/max values of
    a bounding box (in real world coordinates) which
    is big enough to contain all of the images in the
    :attr:`images` list. This property shouid be
    read-only, but I don't have a way to enforce it
    (yet). 
    """

    
    def __init__(self, images=None):
        """Create an ImageList object from the given sequence of
        :class:`Image` objects."""
        
        if images is None: images = []

        self.images = images

        self.addListener(
            'images',
            self.__class__.__name__,
            self._imageListChanged)

        # initialise image bounds
        self._imageListChanged()

        # set the _lastDir attribute,
        # used by the addImages method
        if len(images) == 0: self._lastDir = os.getcwd()
        else:                self._lastDir = op.dirname(images[-1].imageFile)


    def addImages(self, fromDir=None, addToEnd=True):
        """Convenience method for interactively adding images to this
        :class:`ImageList`.

        If the :mod:`wx` package is available, pops up a file dialog
        prompting the user to select one or more images to append to the
        image list.

        :param str fromDir:   Directory in which the file dialog should start.
                              If ``None``, the most recently visited directory
                              (via this method) is used, or a directory from
                              an already loaded image, or the current working
                              directory.

        :param bool addToEnd: If True (the default), the new images are added
                              to the end of the list. Otherwise, they are added
                              to the beginning of the list.

        Returns: True if images were successfully added, False if no images
        were added.
        
        :raise ImportError:  if :mod:`wx` is not present.
        :raise RuntimeError: if a :class:`wx.App` has not been created.

        """
        import wx

        app = wx.GetApp()

        if app is None:
            raise RuntimeError('A wx.App has not been created')

        saveLastDir = False
        if fromDir is None:
            fromDir = self._lastDir
            saveLastDir = True

        # TODO wx wildcard handling is buggy,
        # so i'm disabling it for now
        # wildcard = imagefile.wildcard()
        dlg = wx.FileDialog(app.GetTopWindow(),
                            message='Open image file',
                            defaultDir=fromDir,
                            # wildcard=wildcard,
                            style=wx.FD_OPEN | wx.FD_MULTIPLE)

        if dlg.ShowModal() != wx.ID_OK: return False

        paths         = dlg.GetPaths()
        images        = map(Image, paths)

        if saveLastDir: self._lastDir = op.dirname(paths[-1])

        if addToEnd: self.extend(      images)
        else:        self.insertAll(0, images)

        return True


    def _imageListChanged(self, *a):
        """Called whenever an item is added or removed from the :attr:`images`
        list. Registers listeners with the properties of each image, and
        calls the :meth:`_updateImageBounds` method.
        """ 
        
        for img in self.images:

            # This may be called multiple times on each image,
            # but it doesn't matter, as any listener which has
            # previously been registered with an image will
            # just be replaced by the new one here.
            img.addListener(
                'transform',
                self.__class__.__name__,
                self._updateImageBounds)

        self._updateImageBounds()

    
    def _updateImageBounds(self, *a):
        """Called whenever an item is added or removed from the
        :attr:`images` list, or an image property changes. Updates
        the :attr:`bounds` property.
        """

        if len(self.images) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]

        for img in self.images:

            for ax in range(3):

                lo, hi = img.imageBounds(ax)

                if lo < minBounds[ax]: minBounds[ax] = lo
                if hi > maxBounds[ax]: maxBounds[ax] = hi

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]]


    # Wrappers around the images list property, allowing this
    # ImageList object to be used as if it is actually a list.
    def __len__(     self):               return self.images.__len__()
    def __getitem__( self, key):          return self.images.__getitem__(key)
    def __iter__(    self):               return self.images.__iter__()
    def __contains__(self, item):         return self.images.__contains__(item)
    def __setitem__( self, key, val):     return self.images.__setitem__(key,
                                                                         val)
    def __delitem__( self, key):          return self.images.__delitem__(key)
    def index(       self, item):         return self.images.index(item)
    def count(       self, item):         return self.images.count(item)
    def append(      self, item):         return self.images.append(item)
    def extend(      self, iterable):     return self.images.extend(iterable)
    def pop(         self, index=-1):     return self.images.pop(index)
    def move(        self, from_, to):    return self.images.move(from_, to)
    def insert(      self, index, item):  return self.images.insertAll(index,
                                                                       item)
    def insertAll(   self, index, items): return self.images.insertAll(index,
                                                                       items) 
