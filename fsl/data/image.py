#!/usr/bin/env python
# 
# image.py - Provides the :class:`Image` class, for representing 3D/4D NIFTI
#            images.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Provides the :class:`Image` class, for representing 3D/4D NIFTI images.
"""

import               logging
import               tempfile
import               os 
import os.path    as op
import subprocess as sp

import numpy   as np
import nibabel as nib

import props

import fsl.utils.transform as transform
import fsl.data.strings    as strings
import fsl.data.constants  as constants


log = logging.getLogger(__name__)


class Image(props.HasProperties):
    """Class which represents a 3D/4D image. Internally, the image is
    loaded/stored using :mod:`nibabel`.

    In addition to the class-level properties defined below, the following
    attributes are present on an :class:`Image` object:

    :ivar nibImage:       The :mod:`nibabel` image object.

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

    :ivar dataSource:     The name of the file that the image was loaded from.

    :ivar tempFile:       The name of the temporary file which was created (in
                          the event that the image was large and was gzipped -
                          see :func:`_loadImageFile`).
    """


    name = props.String()
    """The name of this image."""


    data = props.Object()
    """The image data. This is a read-only :mod:`numpy` array - all changes
       to the image data must be via the :meth:`applyChange` method.
    """


    saved = props.Boolean(default=False)
    """A read-only property (not enforced) which is ``True`` if the image,
    as stored in memory, is saved to disk, ``False`` otherwise.
    """


    def __init__(self,
                 image,
                 xform=None,
                 name=None,
                 header=None,
                 loadData=True):
        """Initialise an Image object with the given image data or file name.

        :arg image:    A string containing the name of an image file to load, 
                       or a :mod:`numpy` array, or a :mod:`nibabel` image
                       object.

        :arg xform:    A ``4*4`` affine transformation matrix which transforms
                       voxel coordinates into real world coordinates.

        :arg name:     A name for the image.

        :arg header:   If not ``None``, assumed to be a
                       :class:`nibabel.nifti1.Nifti1Header` to be used as the 
                       image header. Not applied to images loaded from file,
                       or existing :mod:`nibabel` images.

        :arg loadData: Defaults to ``True``. If ``False``, the image data is
                       not loaded - this is useful if you're only interested
                       in the header data, as the file will be loaded much
                       more quickly. The image data may subsequently be loaded
                       via the :meth:`loadData` method.
        """

        self.nibImage   = None
        self.dataSource = None
        self.tempFile   = None

        if header is not None:
            header = header.copy()

        # The image parameter may be the name of an image file
        if isinstance(image, basestring):
            
            nibImage, filename = loadImage(addExt(image))
            self.nibImage      = nibImage
            self.dataSource    = op.abspath(image)

            # if the returned file name is not the same as
            # the provided file name, that means that the
            # image was opened from a temporary file
            if filename != image:
                filepref      = removeExt(op.basename(self.dataSource))
                self.tempFile = nibImage.get_filename()
            else:
                filepref      = removeExt(op.basename(self.dataSource))

            if name is None:
                name = filepref
            
            self.name  = name
            self.saved = True
                
        # Or a numpy array - we wrap it in a nibabel image,
        # with an identity transformation (each voxel maps
        # to 1mm^3 in real world space)
        elif isinstance(image, np.ndarray):

            if xform is None:
                if header is None: xform = np.identity(4)
                else:              xform = header.get_best_affine()
            if name  is None: name = 'Numpy array'
            
            self.nibImage  = nib.nifti1.Nifti1Image(image,
                                                    xform,
                                                    header=header)
            self.name      = name
            
        # otherwise, we assume that it is a nibabel image
        else:
            if name  is None:
                name = 'Nibabel image'
            
            self.nibImage = image
            self.name     = name

        self.shape         = self.nibImage.get_shape()
        self.pixdim        = self.nibImage.get_header().get_zooms()
        self.voxToWorldMat = np.array(self.nibImage.get_affine())
        self.worldToVoxMat = transform.invert(self.voxToWorldMat)

        if loadData:
            self.loadData()
        else:
            self.data = None

        if len(self.shape) < 3 or len(self.shape) > 4:
            raise RuntimeError('Only 3D or 4D images are supported')

        log.memory('{}.init ({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        log.memory('{}.del ({})'.format(type(self).__name__, id(self)))
        
        
    def loadData(self):
        """Loads the image data from the file. This method only needs to
        be called if the ``loadData`` parameter passed to :meth:`__init__`
        was ``False``.
        """
        
        data = self.nibImage.get_data()

        # Squeeze out empty dimensions, as
        # 3D image can sometimes be listed
        # as having 4 or more dimensions
        shape = data.shape
        
        for i in reversed(range(len(shape))):
            if shape[i] == 1: data = data.squeeze(axis=i)
            else:             break

        data.flags.writeable = False

        log.debug('Loaded image data ({}) - original '
                  'shape {}, squeezed shape {}'.format(
                      self.name,
                      shape,
                      data.shape))

        self.data   = data
        self.shape  = self.shape[ :len(data.shape)]
        self.pixdim = self.pixdim[:len(data.shape)]
        
        
    def applyChange(self, offset, newVals, vol=None):
        """Changes the image data according to the given new values.
        Any listeners registered on the :attr:`data` property will be
        notified of the change.

        :arg offset:  A tuple of three values, containing the xyz
                      offset of the image region to be changed.
        
        :arg newVals: A 3D numpy array containing the new image values.
        
        :arg vol:     If this is a 4D image, the volume index.
        """
        
        if self.is4DImage() and vol is None:
            raise ValueError('Volume must be specified for 4D images')
        
        data          = self.data
        xlo, ylo, zlo = offset
        xhi           = xlo + newVals.shape[0]
        yhi           = ylo + newVals.shape[1]
        zhi           = zlo + newVals.shape[2]

        try:
            data.flags.writeable = True
            if self.is4DImage(): data[xlo:xhi, ylo:yhi, zlo:zhi, vol] = newVals
            else:                data[xlo:xhi, ylo:yhi, zlo:zhi]      = newVals
            data.flags.writeable = False
            
        except:
            data.flags.writeable = False
            raise

        # Force a notification on the 'data' property
        # by assigning its value back to itself
        self.data  = data
        self.saved = False


    def save(self):
        """Convenience method to save any changes made to the :attr:`data` of 
        this :class:`Image` instance.

        See the :func:`saveImage` function.
        """
        return saveImage(self)
    

    def __hash__(self):
        """Returns a number which uniquely idenfities this :class:`Image`
        object (the result of ``id(self)``).
        """
        return id(self)


    def __str__(self):
        """Return a string representation of this :class:`Image`."""
        return '{}({}, {})'.format(self.__class__.__name__,
                                   self.name,
                                   self.dataSource)

        
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
        if   sform_code > 4: code = constants.NIFTI_XFORM_UNKNOWN
        elif sform_code < 0: code = constants.NIFTI_XFORM_UNKNOWN

        # All is well
        else:                code = sform_code

        return int(code)


    def getWorldOrientation(self, axis):
        """Returns a code representing the orientation of the specified axis
        in world space.

        This method returns one of the following values, indicating the
        direction in which coordinates along the specified axis increase:
          - :attr:`~fsl.data.constants.ORIENT_L2R`:     Left to right
          - :attr:`~fsl.data.constants.ORIENT_R2L`:     Right to left
          - :attr:`~fsl.data.constants.ORIENT_A2P`:     Anterior to posterior
          - :attr:`~fsl.data.constants.ORIENT_P2A`:     Posterior to anterior
          - :attr:`~fsl.data.constants.ORIENT_I2S`:     Inferior to superior
          - :attr:`~fsl.data.constants.ORIENT_S2I`:     Superior to inferior
          - :attr:`~fsl.data.constants.ORIENT_UNKNOWN`: Orientation is unknown

        The returned value is dictated by the XForm code contained in the
        image file header (see the :meth:`getXFormCode` method). Basically,
        if the XForm code is 'unknown', this method will return -1 for all
        axes. Otherwise, it is assumed that the image is in RAS orientation
        (i.e. the X axis increases from left to right, the Y axis increases
        from  posterior to anterior, and the Z axis increases from inferior
        to superior).
        """

        if self.getXFormCode() == constants.NIFTI_XFORM_UNKNOWN:
            return -1

        if   axis == 0: return constants.ORIENT_L2R
        elif axis == 1: return constants.ORIENT_P2A
        elif axis == 2: return constants.ORIENT_I2S

        else: return -1


    def getVoxelOrientation(self, axis):
        """Returns a code representing the (estimated) orientation of the
        specified voxelwise axis.

        See the :meth:`getWorldOrientation` method for a description
        of the return value.
        """
        
        if self.getXFormCode() == constants.NIFTI_XFORM_UNKNOWN:
            return -1 
        
        # the aff2axcodes returns one code for each 
        # axis in the image array (i.e. in voxel space),
        # which denotes the real world direction
        code = nib.orientations.aff2axcodes(
            self.nibImage.get_affine(),
            ((constants.ORIENT_R2L, constants.ORIENT_L2R),
             (constants.ORIENT_A2P, constants.ORIENT_P2A),
             (constants.ORIENT_S2I, constants.ORIENT_I2S)))[axis]
        return code


# TODO The wx.FileDialog does not    
# seem to handle wildcards with      
# multiple suffixes (e.g. '.nii.gz'),
# so i'm just providing '*.gz'for now
ALLOWED_EXTENSIONS = ['.nii.gz', '.nii', '.img', '.hdr', '.img.gz', '.gz']
"""The file extensions which we understand. This list is used as the default
if if the ``allowedExts`` parameter is not passed to any of the functions in
this module.
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


def isSupported(filename, allowedExts=None):
    """
    Returns ``True`` if the given file has a supported extension, ``False``
    otherwise.

    :arg filename:    The file name to test.
    
    :arg allowedExts: A list of strings containing the allowed file
                      extensions.
    """

    if allowedExts is None: allowedExts = ALLOWED_EXTENSIONS

    return any(map(lambda ext: filename.endswith(ext), allowedExts))


def removeExt(filename, allowedExts=None):
    """
    Removes the extension from the given file name. Returns the filename
    unmodified if it does not have a supported extension.

    :arg filename:    The file name to strip.
    
    :arg allowedExts: A list of strings containing the allowed file
                      extensions.    
    """

    if allowedExts is None: allowedExts = ALLOWED_EXTENSIONS

    # figure out the extension of the given file
    extMatches = map(lambda ext: filename.endswith(ext), allowedExts)

    # the file does not have a supported extension
    if not any(extMatches):
        return filename

    # figure out the length of the matched extension
    extIdx = extMatches.index(True)
    extLen = len(allowedExts[extIdx])

    # and trim it from the file name
    return filename[:-extLen]


def addExt(
        prefix,
        mustExist=True,
        allowedExts=None,
        defaultExt=None):
    """Adds a file extension to the given file ``prefix``.

    If ``mustExist`` is False, and the file does not already have a 
    supported extension, the default extension is appended and the new
    file name returned. If the prefix already has a supported extension,
    it is returned unchanged.

    If ``mustExist`` is ``True`` (the default), the function checks to see 
    if any files exist that have the given prefix, and a supported file 
    extension.  A :exc:`ValueError` is raised if:

       - No files exist with the given prefix and a supported extension.
       - More than one file exists with the given prefix, and a supported
         extension.

    Otherwise the full file name is returned.

    :arg prefix:      The file name refix to modify.
    :arg mustExist:   Whether the file must exist or not.
    :arg allowedExts: List of allowed file extensions.
    :arg defaultExt:  Default file extension to use.
    """

    if allowedExts is None: allowedExts = ALLOWED_EXTENSIONS
    if defaultExt  is None: defaultExt  = DEFAULT_EXTENSION

    if not mustExist:

        # the provided file name already
        # ends with a supported extension 
        if any(map(lambda ext: prefix.endswith(ext), allowedExts)):
            return prefix

        return prefix + defaultExt

    # If the provided prefix already ends with a
    # supported extension , check to see that it exists
    if any(map(lambda ext: prefix.endswith(ext), allowedExts)):
        extended = [prefix]
        
    # Otherwise, make a bunch of file names, one per
    # supported extension, and test to see if exactly
    # one of them exists.
    else:
        extended = map(lambda ext: prefix + ext, allowedExts)

    exists = map(op.isfile, extended)

    # Could not find any supported file
    # with the specified prefix
    if not any(exists):
        raise ValueError(
            'Could not find a supported file with prefix {}'.format(prefix))

    # Ambiguity! More than one supported
    # file with the specified prefix
    if len(filter(bool, exists)) > 1:
        raise ValueError('More than one file with prefix {}'.format(prefix))

    # Return the full file name of the
    # supported file that was found
    extIdx = exists.index(True)
    return extended[extIdx]


def loadImage(filename):
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

        msg = strings.messages['image.loadImage.decompress']
        msg = msg.format(realFilename, mbytes, filename)

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

    log.debug('Loading image from {}'.format(filename))
    
    return nib.load(filename), filename


def saveImage(image, fromDir=None):
    """Convenience function for interactively saving changes to an image.

    If the :mod:`wx` package is available, a dialog is popped up, prompting
    the user to select a destination. Or, if the image has been loaded 
    from a file, the user is prompted to confirm that they want to overwrite  
    the image.


    :param image:         The :class:`.Image` instance to be saved.

    :param str fromDir:   Directory in which the file dialog should start.
                          If ``None``, the most recently visited directory
                          (via this method) is used, or the directory from
                          the given image, or the current working directory.

    :raise ImportError:  if :mod:`wx` is not present.
    :raise RuntimeError: if a :class:`wx.App` has not been created.
    """

    if image.saved:
        return
    
    import wx

    app = wx.GetApp()

    if app is None:
        raise RuntimeError('A wx.App has not been created') 

    lastDir = getattr(saveImage, 'lastDir', None)

    if lastDir is None:
        if image.dataSource is None: lastDir = os.getcwd()
        else:                        lastDir = op.dirname(image.dataSource)

    # TODO make image.name safe (spaces to 
    # underscores, filter non-alphanumeric)
    if image.dataSource is None: filename = image.name
    else:                        filename = op.basename(image.dataSource)

    filename = removeExt(filename)

    saveLastDir = False
    if fromDir is None:
        fromDir = lastDir
        saveLastDir = True

    dlg = wx.FileDialog(app.GetTopWindow(),
                        message=strings.titles['image.saveImage.dialog'],
                        defaultDir=fromDir,
                        defaultFile=filename, 
                        style=wx.FD_SAVE)

    if dlg.ShowModal() != wx.ID_OK: return False

    if saveLastDir: saveImage.lastDir = lastDir

    path     = dlg.GetPath()
    nibImage = image.nibImage

    if not isSupported(path):
        path = addExt(path, False)

    # this is an image which has been
    # loaded from a file, and ungzipped
    # to a temporary location
    try:
        if image.tempFile is not None:

            # if selected path is same as original path,
            # save to both temp file and to path

            # else, if selected path is different from
            # original path, save to temp file and to
            # new path, and update the path

            # actually, the two behaviours just described
            # are identical
            log.warn('Saving large images is not yet functional')
            pass

        # this is just a normal image
        # which has been loaded from
        # a file, or an in-memory image
        else:

            log.debug('Saving image ({}) to {}'.format(image, path))

            nib.save(nibImage, path)
            image.dataSource = path
            
    except Exception as e:

        msg = strings.messages['image.saveImage.error'].format(e.msg)
        log.warn(msg)
        wx.MessageDialog(app.GetTopWindow(),
                         message=msg,
                         style=wx.OK | wx.ICON_ERROR).ShowModal()
        return

    image.saved = True
