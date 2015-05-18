#!/usr/bin/env python
#
# displaycontext.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import sys
import logging

import props

import fsl.utils.transform as transform
import display             as fsldisplay
import                        volumeopts


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

        props.SyncableHasProperties.__init__(self, parent)
        
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

        
    def getDisplay(self, overlay):
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
                dParent = self.getParent().getDisplay(overlay)

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

        Ensures that a :class:`.Display` and :class:`.DisplayOpts` object
        exists for every image, updates the :attr:`bounds` property, makes
        sure that the :attr:`overlayOrder` property is consistent, and updates
        constraints on the :attr:`selectedOverlay` property.
        """

        # Ensure that a Display object
        # exists for every overlay
        for overlay in self.__overlayList:

            # The getDisplay method
            # will create a Display object
            # if one does not already exist
            display = self.getDisplay(overlay)
            opts    = display.getDisplayOpts()

            # Register a listener on the DisplayOpts
            # object for every overlay - if any
            # DisplayOpts properties change, the
            # overlay display bounds may have changed,
            # so we need to know when this happens.
            opts.addGlobalListener(self.__name,
                                   self.__displayOptsChanged,
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

            
    def __displayOptsChanged(self, value, valid, opts, name):
        """Called when the :class:`.DisplayOpts` properties of any overlay
        change. Updates the :attr:`bounds` property.
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

        display = opts.display

        if display.getOverlay() != self.getSelectedOverlay():
            self.__updateBounds()
            return

        # If the currently selected overlay is an Image, and its
        # transformation matrix property has changed, we want the
        # current display location to be preserved, in terms of
        # the corresponding image world coordinates.
        if not isinstance(opts, volumeopts.ImageOpts):
            return
        
        # Calculate the image world location using
        # the old display<-> world transform, then
        # transform it back to the new world->display
        # transform. 
        imgWorldLoc = transform.transform(
            [self.location.xyz],
            opts.getTransform(opts.getLastTransform(), 'world'))[0]
        newDispLoc  = transform.transform(
            [imgWorldLoc],
            opts.getTransform('world', 'display'))[0]

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
            opts    = display.getDisplayOpts()
            lo, hi  = opts   .getDisplayBounds()

            for ax in range(3):

                if lo[ax] < minBounds[ax]: minBounds[ax] = lo[ax]
                if hi[ax] > maxBounds[ax]: maxBounds[ax] = hi[ax]

        self.bounds[:] = [minBounds[0], maxBounds[0],
                          minBounds[1], maxBounds[1],
                          minBounds[2], maxBounds[2]]
 
            
    def __boundsChanged(self, *a):
        """Called when the :attr:`bounds` property changes.

        Updates the constraints on the :attr:`location` property.
        """

        self.location.setLimits(0, self.bounds.xlo, self.bounds.xhi)
        self.location.setLimits(1, self.bounds.ylo, self.bounds.yhi)
        self.location.setLimits(2, self.bounds.zlo, self.bounds.zhi)
