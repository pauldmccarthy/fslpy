#!/usr/bin/env python
#
# image.py - Classes for representing 3D/4D images and collections of said
# images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Classes for representing 3D/4D images and collections of said images."""

import os
import logging
import tempfile
import collections
import subprocess as sp
import os.path    as op

import numpy      as np
import nibabel    as nib

import props
import fsl.data.imagefile   as imagefile
import fsl.utils.transform  as transform


log = logging.getLogger(__name__)

# Constants which represent the orientation
# of an axis, in either voxel or world space.
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

    :ivar nibImage:       The :mod:`nibabel` image object.
    
    :ivar data:           A reference to the image data, stored as a
                          :mod`numpy` array.
    
    :ivar shape:          A list/tuple containing the number of voxels
                          along each image dimension.
    
    :ivar pixdim:         A list/tuple containing the size of one voxel
                          along each image dimension.
    
    :ivar voxToWorldMat:  A 4*4 array specifying the affine transformation
                          for transforming voxel coordinates into real world
                          coordinates.

    :ivar worldToVoxMat:  A 4*4 array specifying the affine transformation
                          for transforming real world coordinates into voxel
                          coordinates. 

    :ivar imageFile:      The name of the file that the image was loaded from.
    
    :ivar tempFile:       The name of the temporary file which was created (in
                          the event that the image was large and was gzipped -
                          see :func:`_loadImageFile`).
    """


    imageType = props.Choice(
        collections.OrderedDict([
            ('volume', '3D/4D volume'),
            ('tensor', '3-direction tensor image')]),
        default='volume')
    """This property defines the type of image data."""

    
    name = props.String()
    """The name of this image."""


    data = props.Object()
    """The image data. This is a read-only :mod:`numpy` array - all changes
       to the image data must be via the :meth:`applyChange` method.
    """

    
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

        self.data          = self.nibImage.get_data()
        self.shape         = self.nibImage.get_shape()
        self.pixdim        = self.nibImage.get_header().get_zooms()
        self.voxToWorldMat = np.array(self.nibImage.get_affine())
        self.worldToVoxMat = transform.invert(self.voxToWorldMat)
        
        self.changed       = False

        self.data.flags.writeable = False

        if len(self.shape) < 3 or len(self.shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        # This dictionary may be used to store
        # arbitrary data associated with this image.
        self._attributes = {}

        
    def applyChange(self, indices, newVals, volume=None):
        """Changes the image data according to the indices and new values.
        Any listeners registered on the :attr:`data` property will be
        notified of the change.

        :arg indices: A :mod:`numpy` array  of shape ``N*3`` containing
                      the indices of the voxels to be changed.
        
        :arg newVals: A sequence of values of length ``N`` containing the
                      new voxel values. Or a scalar value, in which case
                      all of the voxels specified by ``indices`` will be
                      set to the scalar.
        
        :arg volume:  If this is a 4D image, the volume index.
        """

        if self.is4DImage() and volume is None:
            raise ValueError('Volume must be specified for 4D images')
        
        xs = indices[:, 0]
        ys = indices[:, 1]
        zs = indices[:, 2]

        data = self.data

        try:
            data.flags.writeable = True
            if self.is4DImage(): data[xs, ys, zs, volume] = newVals
            else:                data[xs, ys, zs]         = newVals
            data.flags.writeable = False
        except:
            data.flags.writeable = False
            raise

        self.changed = True
        self.data    = data
        

    def __hash__(self):
        """Returns a number which uniquely idenfities this :class:`Image`
        object (the result of ``id(self)``).
        """
        return id(self)


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


    def getXFormCode(self):
        """This method returns the code contained in the NIFTI1 header,
        indicating the space to which the (transformed) image is oriented.
        
        """
        sform_code = self.nibImage.get_header()['sform_code']

        # Invalid values
        if   sform_code > 4: code = NIFTI_XFORM_UNKNOWN
        elif sform_code < 0: code = NIFTI_XFORM_UNKNOWN

        # All is well
        else:                code = sform_code

        return int(code)


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
    :class:`Image` objects.

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

    
    def __init__(self, images=None):
        """Create an ImageList object from the given sequence of
        :class:`Image` objects."""
        
        if images is None: images = []

        self.images.extend(images)

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
