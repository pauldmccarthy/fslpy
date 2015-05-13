#!/usr/bin/env python
#
# displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging

import props

import fsl.data.image      as fslimage
import fsl.utils.transform as transform

import display as fsldisplay


log = logging.getLogger(__name__)


class DisplayContext(props.SyncableHasProperties):
    """Contains a number of properties defining how an :class:`.OverlayList`
    is to be displayed.
    """

    
    selectedOverlay = props.Int(minval=0, default=0, clamped=True)
    """Index of the currently 'selected' overlay.

    Note that this index is in relation to the
    :class:`.OverlayList`, rather than to the :attr:`overlayOrder`
    list.

    If you're interested in the currently selected overlay, you must also
    listen for changes to the :attr:`.OverlayList.images` list as, if the list
    changes, the :attr:`selectedOverlay` index may not change, but the overlay
    to which it points may be different.
    """


    location = props.Point(ndims=3, labels=('X', 'Y', 'Z'))
    """The location property contains the currently selected
    3D location (xyz) in the current display coordinate system.
    """

    
    bounds = props.Bounds(ndims=3)
    """This property contains the min/max values of a bounding box (in display
    coordinates) which is big enough to contain all of the overlays in the
    :attr:`overlays` list. This property shouid be read-only, but I don't have
    a way to enforce it (yet).
    """


    volume = props.Int(minval=0, maxval=0, default=0, clamped=True)
    """The volume property contains the currently selected volume across the 4D
    overlays in the :class:`.OverlayList`.  This property is only relevant for
    4D overlays in the overlay list.
    """


    overlayOrder = props.List(props.Int())
    """A list of indices into the :attr:`.OverlayList.overlays`
    list, defining the order in which the overlays are to be displayed.

    See the :meth:`getOrderedOverlays` method.
    """


    def __init__(self, overlayList, parent=None):
        """Create a :class:`DisplayContext` object.

        :arg overlayList: A :class:`.OverlayList` instance.

        :arg parent: Another :class`DisplayContext` instance to be used
        as the parent of this instance.
        """

        props.SyncableHasProperties.__init__(self, parent, nounbind=('volume'))
        
        self.__overlayList = overlayList
        self.__name         = '{}_{}'.format(self.__class__.__name__, id(self))

        # Keep track of the overlay list
        # length so we can do some things in the
        # _overlayListChanged method
        self.__prevOverlayListLen = 0

        # Ensure that a Display object exists
        # for every overlay, and that the display
        # bounds property is initialised
        self.__displays = {}
        self.__overlayListChanged()

        overlayList.addListener('overlays',
                                self.__name,
                                self.__overlayListChanged)
        self.addListener(       'bounds',
                                self.__name,
                                self.__boundsChanged)
        self.addListener(       'volume',
                                self.__name,
                                self.__volumeChanged)

        
    def getDisplayProperties(self, overlay):
        """Returns the display property object (e.g. a :class:`.Display`
        object) for the specified overlay (or overlay index).

        If a :class:`Display` object does not exist for the given overlay,
        one is created.
        """

        if isinstance(overlay, int):
            overlay = self.__overlayList[overlay]

        try:
            display = self.__displays[overlay]
                
        except KeyError:
                
            if self.getParent() is None:
                dParent = None
            else:
                dParent = self.getParent().getDisplayProperties(overlay)

            display = fsldisplay.Display(overlay,
                                         self.__overlayList,
                                         self,
                                         dParent)
            self.__displays[overlay] = display
        
        return display

    
    def selectOverlay(self, overlay):
        self.selectedOverlay = self.__overlayList.index(overlay)

    
    def getSelectedOverlay(self):
        """Returns the currently selected overlay object,
        or ``None`` if there are no overlays.
        """
        if len(self.__overlayList) == 0: return None
        return self.__overlayList[self.selectedOverlay]

    
    def getOverlayOrder(self, overlay):
        """Returns the order in which the given overlay (or an index into
        the :class:`.OverlayList` list) should be displayed
        (see the :attr:`overlayOrder property).
        """
        if not isinstance(overlay, int):
            overlay = self.__overlayList.index(overlay)
            
        return self.overlayOrder.index(overlay)

    
    def getOrderedOverlays(self):
        """Returns a list of overlay objects from
        the :class:`.OverlayList` list, sorted into the order
        that they are to be displayed.
        """
        return [self.__overlayList[idx] for idx in self.overlayOrder]


    def __overlayListChanged(self, *a):
        """Called when the :attr:`.OverlayList.overlays` property
        changes.

        Ensures that a :class:`.Display` object exists for every image,
        and updates the constraints on the :attr:`selectedOverlay` and
        :attr:`volume` properties.
        """

        # Ensure that a Display object
        # exists for every overlay
        for overlay in self.__overlayList:

            # The getDisplayProperties method
            # will create a Display object
            # if one does not already exist
            display = self.getDisplayProperties(overlay)

            # Register a listener with the transform property
            # of every overlay display so that when it changes,
            # we can update the display bounds, and preserve
            # the current display location so that it is in
            # terms of the world location of the currently
            # selected overlay
            # 
            # This listener may be registered multiple times
            # on each overlay, but it doesn't matter, as any
            # listener which has previously been registered
            # with an overlay display will just be replaced
            # by the new one here.
            display.addListener(
                'transform',
                self.__class__.__name__,
                self.__transformChanged,
                overwrite=True)

        # Ensure that the overlayOrder
        # property is valid ...
        # 
        # If overlays have been added to
        # the overlay list, add indices
        # for them to the overlayOrder list
        if len(self.overlayOrder) < len(self.__overlayList):
            self.overlayOrder.extend(range(len(self.overlayOrder),
                                           len(self.__overlayList)))

        # Otherwise, if overlays have been removed
        # from the overlay list, remove the corresponding
        # indices from the overlayOrder list
        elif len(self.overlayOrder) > len(self.__overlayList):
            for idx in range(len(self.__overlayList),
                             len(self.overlayOrder)):
                self.overlayOrder.remove(idx)

        # Ensure that the bounds property is accurate
        self.__updateBounds()

        # If the overlay list was empty,
        # and is now non-empty, centre
        # the currently selected location
        if (self.__prevOverlayListLen == 0) and (len(self.__overlayList) > 0):
            
            # initialise the location to be
            # the centre of the world
            b = self.bounds
            self.location.xyz = [
                b.xlo + b.xlen / 2.0,
                b.ylo + b.ylen / 2.0,
                b.zlo + b.zlen / 2.0]
            
        self.__prevOverlayListLen = len(self.__overlayList)
 
        # Limit the selectedOverlay property
        # so it cannot take a value greater
        # than len(overlayList)-1
        nOverlays = len(self.__overlayList)
        if nOverlays > 0:
            self.setConstraint('selectedOverlay', 'maxval', nOverlays - 1)
        else:
            self.setConstraint('selectedOverlay', 'maxval', 0)

        # Limit the volume property so it cannot
        # take a value greater than the longest
        # 4D volume in the overlay list
        maxvols = 0

        # TODO This only works with Image types
        for overlay in self.__overlayList:

            if not isinstance(overlay, fslimage.Image):
                raise RuntimeError('Non-volumetric types not supported yet')
            
            if not overlay.is4DImage():
                continue

            if overlay.shape[3] > maxvols:
                maxvols = overlay.shape[3]

        if maxvols > 0:
            self.setConstraint('volume', 'maxval', maxvols - 1)
        else:
            self.setConstraint('volume', 'maxval', 0)


    def __transformChanged(self, xform, valid, display, propName):
        """Called when the
        :attr:`.Display.transform property
        changes for any overlay in the :class:`.OverlayList`. Sets the 
        :attr:`location` property, so that the selected world
        location is preserved, in the new display coordinate system.
        """

        # This check is ugly, and is required due to
        # an ugly circular relationship which exists
        # between parent/child DCs and the transform/
        # location properties:
        # 
        # 1. When the transform property of a child DC
        #    Display object changes (this should always 
        #    be due to user input), that change is 
        #    propagated to the parent DC Display object.
        #
        # 2. This results in the DC._transformChanged
        #    method (this method) being called on the
        #    parent DC.
        #
        # 3. Said method correctly updates the DC.location
        #    property, so that the world location of the
        #    selected image is preserved.
        #
        # 4. This location update is propagated back to
        #    the child DC.location property, which is
        #    updated to have the new correct location
        #    value.
        #
        # 5. Then, the child DC._transformChanged method
        #    is called, which goes and updates the child
        #    DC.location property to contain a bogus
        #    value.
        #
        # So this test is in place to prevent this horrible
        # circular loop behaviour from occurring. If the
        # location properties are synced, and contain the
        # same value, we assume that they don't need to be
        # updated again, and escape from ths system.
        if self.getParent() is not None and self.isSyncedToParent('location'):
            if self.getParent().location == self.location:
                return

        if display.getOverlay() != self.getSelectedOverlay():
            self.__updateBounds()
            return

        # Calculate the image world location using
        # the old display<-> world transform, then
        # transform it back to the new world->display
        # transform
        
        imgWorldLoc = transform.transform(
            [self.location.xyz],
            display.getTransform(display.getLastTransform(), 'world'))[0]
        newDispLoc  = transform.transform(
            [imgWorldLoc],
            display.getTransform('world', 'display'))[0]

        # Update the display coordinate 
        # system bounds, and the location
        self.__updateBounds()
        self.location.xyz = newDispLoc


    def __updateBounds(self, *a):
        """Called when the overlay list changes, or when any overlay display
        transform is changed. Updates the :attr:`bounds` property.
        """

        if len(self.__overlayList) == 0:
            minBounds = [0.0, 0.0, 0.0]
            maxBounds = [0.0, 0.0, 0.0]
            
        else:
            minBounds = 3 * [ sys.float_info.max]
            maxBounds = 3 * [-sys.float_info.max]

        for ovl in self.__overlayList:

            display = self.__displays[ovl]
            lo, hi  = display.getDisplayBounds()

            for ax in range(3):

                if lo[ax] < minBounds[ax]: minBounds[ax] = lo[ax]
                if hi[ax] > maxBounds[ax]: maxBounds[ax] = hi[ax]

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]]
 
    
    def __volumeChanged(self, *a):
        """Called when the :attr:`volume` property changes.

        Propagates the change on to the :attr:`.Display.volume` property
        for each overlay in the :class:`.OverlayList`.
        """

        for ovl in self.__overlayList:

            display = self.__displays[ovl]
            
            # The volume property for each should
            # be clamped to the possible value for that
            # image, so we don't need to check if the
            # current volume value is valid for each image
            display.volume = self.volume

            
    def __boundsChanged(self, *a):
        """Called when the :attr:`bounds` property changes.

        Updates the constraints on the :attr:`location` property.
        """

        self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
        self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
        self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)
