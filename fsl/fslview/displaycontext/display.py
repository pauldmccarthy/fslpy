#!/usr/bin/env python
#
# display.py - Definitions of the Display and DisplayOpts classes.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides definitions of an important class - the
:class:`Display` class.

A ``Display`` contains a specification for the way in which an
:class:`~fsl.data.image.Image` instance is to be displayed.


..note:: Put a description of the three coordinate systems which
         exist in the system.
"""

import logging

import numpy               as np

import props

import fsl.data.image      as fslimage
import fsl.data.strings    as strings
import fsl.utils.transform as transform


log = logging.getLogger(__name__)


class DisplayOpts(props.SyncableHasProperties):

    def __init__(
            self,
            image,
            display,
            imageList,
            displayCtx,
            parent=None,
            *args,
            **kwargs):
        
        props.SyncableHasProperties.__init__(self, parent, *args, **kwargs)
        
        self.image      = image
        self.display    = display
        self.imageList  = imageList
        self.displayCtx = displayCtx
        self.imageType  = image.imageType
        self.name       = '{}_{}'.format(type(self).__name__, id(self))

        
    def destroy(self):
        pass


class Display(props.SyncableHasProperties):
    """
    """

    
    name = fslimage.Image.name
    """The image name.  This property is bound to the
    :attr:`~fsl.data.image.Image.name` property.
    """

    
    imageType = fslimage.Image.imageType
    """The image data type. This property is bound to the
    :attr:`~fsl.data.image.Image.imageType` property.
    """

    
    enabled = props.Boolean(default=True)
    """Should this image be displayed at all?"""

    
    resolution = props.Real(maxval=10, default=1, clamped=True)
    """Data resolution in world space. The minimum value is set in __init__.""" 
                              
    
    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """If a 4D image, the current volume to display."""


    transform = props.Choice(
        ('affine', 'pixdim', 'id'),
        labels=[strings.choices['Display.transform.affine'],
                strings.choices['Display.transform.pixdim'],
                strings.choices['Display.transform.id']],
        default='pixdim')
    """This property defines how the image should be transformd into the display
    coordinate system.
    
      - ``affine``: Use the affine transformation matrix stored in the image
        (the ``qform``/``sform`` fields in NIFTI1 headers).
                    
      - ``pixdim``: Scale voxel sizes by the ``pixdim`` fields in the image
        header.
    
      - ``id``: Perform no scaling or transformation - voxels will be
        interpreted as :math:`1mm^3` isotropic, with the origin at voxel
        (0,0,0).
    """


    interpolation = props.Choice(
        ('none', 'linear', 'spline'),
        labels=[strings.choices['Display.interpolation.none'],
                strings.choices['Display.interpolation.linear'],
                strings.choices['Display.interpolation.spline']])
    """How the value shown at a real world location is derived from the
    corresponding voxel value(s). 'No interpolation' is equivalent to nearest
    neighbour interpolation.
    """

    
    alpha = props.Percentage(default=100.0)
    """Opacity - 100% is fully opaque, and 0% is fully transparent."""

    
    brightness = props.Percentage()

    
    contrast   = props.Percentage()


    softwareMode = props.Boolean(default=False)
    """If possible, optimise for software-based rendering."""

        
    def is4DImage(self):
        """Returns ``True`` if this image is 4D, ``False`` otherwise.
        """
        return self.image.is4DImage()


    def __init__(self, image, imageList, displayCtx, parent=None):
        """Create a :class:`Display` for the specified image.

        :arg image: A :class:`~fsl.data.image.Image` object.

        :arg parent: 
        """
        
        self.image      = image
        self.imageList  = imageList
        self.displayCtx = displayCtx

        # bind self.name to image.name, so changes
        # in one are propagated to the other
        self.bindProps('name',      image)
        self.bindProps('imageType', image)

        # The display<->* transformation matrices
        # are created in the _transformChanged method
        self.__xforms = {}
        self.__setupTransforms()

        # is this a 4D volume?
        if image.is4DImage():
            self.setConstraint('volume', 'maxval', image.shape[3] - 1)

        self.__oldTransform = None
        self.__transform    = self.transform
        self.__transformChanged()

        # limit resolution to the image dimensions
        self.resolution = min(image.pixdim[:3])
        self.setConstraint('resolution',   'minval', self.resolution)

        # Call the super constructor after our own
        # initialisation, in case the provided parent
        # has different property values to our own,
        # and our values need to be updated
        props.SyncableHasProperties.__init__(
            self,
            parent,
            
            # The name property is implicitly bound
            # through the image object so it doesn't
            # need to be linked between ImageDisplays 
            nobind=['name'],
            
            # These properties cannot be unbound, as
            # they affect the OpenGL representation
            nounbind=['interpolation',
                      'volume',
                      'resolution',
                      'transform',
                      'softwareMode', 
                      'imageType'])

        # Set up listeners after caling Syncabole.__init__,
        # so the callbacks don't get called during synchronisation
        self.addListener(
            'transform',
            'Display_{}'.format(id(self)),
            self.__transformChanged) 
        self.addListener(
            'imageType',
            'Display_{}'.format(id(self)),
            self.__imageTypeChanged)

        # The imageTypeChanged method creates
        # a new DisplayOpts instance - for this,
        # it needs to be able to access this
        # Dispaly instance's parent (so it can
        # subsequently access a parent for the
        # new DisplayOpts instance). Therefore,
        # we do this after calling
        # Syncable.__init__.
        self.__displayOpts = None
        self.__imageTypeChanged()

        
    def __setupTransforms(self):
        """Calculates transformation matrices between all of the possible
        spaces in which the image may be displayed.

        These matrices are accessible via the :meth:`getTransform` method.
        """

        image          = self.image

        voxToIdMat     = np.eye(4)
        voxToPixdimMat = np.diag(list(image.pixdim[:3]) + [1.0])
        voxToAffineMat = image.voxToWorldMat.T
        
        idToVoxMat        = transform.invert(voxToIdMat)
        idToPixdimMat     = transform.concat(idToVoxMat, voxToPixdimMat)
        idToAffineMat     = transform.concat(idToVoxMat, voxToAffineMat)

        pixdimToVoxMat    = transform.invert(voxToPixdimMat)
        pixdimToIdMat     = transform.concat(pixdimToVoxMat, voxToIdMat)
        pixdimToAffineMat = transform.concat(pixdimToVoxMat, voxToAffineMat)

        affineToVoxMat    = image.worldToVoxMat.T
        affineToIdMat     = transform.concat(affineToVoxMat, voxToIdMat)
        affineToPixdimMat = transform.concat(affineToVoxMat, voxToPixdimMat)
        
        self.__xforms['id',  'id']     = np.eye(4)
        self.__xforms['id',  'pixdim'] = idToPixdimMat 
        self.__xforms['id',  'affine'] = idToAffineMat

        self.__xforms['pixdim', 'pixdim'] = np.eye(4)
        self.__xforms['pixdim', 'id']     = pixdimToIdMat
        self.__xforms['pixdim', 'affine'] = pixdimToAffineMat
 
        self.__xforms['affine', 'affine'] = np.eye(4)
        self.__xforms['affine', 'id']     = affineToIdMat
        self.__xforms['affine', 'pixdim'] = affineToPixdimMat 


    def getTransform(self, from_, to, xform=None):
        """Return a matrix which may be used to transform coordinates
        from ``from_`` to ``to``. Valid values for ``from_`` and ``to``
        are:
          - ``id``:      Voxel coordinates
        
          - ``pixdim``:  Voxel coordinates, scaled by voxel dimensions
        
          - ``affine``:  World coordinates, as defined by the NIFTI1
                         ``qform``/``sform``. See
                         :attr:`~fsl.data.image.Image.voxToWorldMat`.
        
          - ``voxel``:   Equivalent to ``id``.
        
          - ``display``: Equivalent to the current value of :attr:`transform`.
        
          - ``world``;   Equivalent to ``affine``.

        If the ``xform`` parameter is provided, and one of ``from_`` or ``to``
        is ``display``, the value of ``xform`` is used instead of the current
        value of :attr:`transform`.
        """

        if xform is None:      xform = self.transform

        if   from_ == 'display': from_ = xform
        elif from_ == 'world':   from_ = 'affine'
        elif from_ == 'voxel':   from_ = 'id'
        
        if   to    == 'display': to    = xform
        elif to    == 'world':   to    = 'affine'
        elif to    == 'voxel':   to    = 'id'

        return self.__xforms[from_, to]

        
    def getDisplayBounds(self):
        """Calculates and returns the min/max values of a 3D bounding box,
        in the display coordinate system, which is big enough to contain
        the image associated with this :class:`ImageDisplay` instance.

        The coordinate system in which the bounding box is defined is
        determined by the current value of the :attr:`transform` property.

        A tuple containing two values is returned, with the first value
        a sequence of three low bounds, and the second value a sequence
        of three high bounds.
        """
        return transform.axisBounds(
            self.image.shape[:3], self.getTransform('voxel', 'display'))


    def getLastTransform(self):
        """Returns the most recent value of the :attr:`transform` property,
        before its current value.
        """
        return self.__oldTransform


    def __transformChanged(self, *a):
        """Called when the :attr:`transform` property is changed."""

        # Store references to the previous display related transformation
        # matrices, just in case anything (hint the DisplayContext object)
        # needs them for any particular reason (hint: so the DisplayContext
        # can preserve the current display location, in terms of image world
        # space, when the transform of the selected image changes)
        self.__oldTransform = self.__transform
        self.__transform    = self.transform
    
    
    def getDisplayOpts(self):
        """
        """

        if (self.__displayOpts           is None) or \
           (self.__displayOpts.imageType != self.imageType):

            if self.__displayOpts is not None:
                self.__displayOpts.destroy()
            
            self.__displayOpts = self.__makeDisplayOpts()
            
        return self.__displayOpts


    def __makeDisplayOpts(self):
        """
        """

        import volumeopts
        import vectoropts
        import maskopts        
        
        if self.getParent() is None:
            oParent = None
        else:
            oParent = self.getParent().getDisplayOpts()

        optsMap = {
            'volume'     : volumeopts.VolumeOpts,
            'rgbvector'  : vectoropts.VectorOpts,
            'linevector' : vectoropts.LineVectorOpts,
            'mask'       : maskopts.  MaskOpts
        }

        optType = optsMap[self.imageType]
        log.debug('Creating DisplayOpts for image {}: {}'.format(
            self.name,
            optType.__name__))
        
        return optType(self.image,
                       self,
                       self.imageList,
                       self.displayCtx,
                       oParent)

    
    def __imageTypeChanged(self, *a):
        """
        """

        # make sure that the display
        # options instance is up to date
        self.getDisplayOpts()
