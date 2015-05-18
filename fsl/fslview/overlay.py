#!/usr/bin/env python
#
# overlay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`OverlayList` class, which is a simple but
fundamental class in FSLView - it is a container for all displayed overlays.

Only one ``OverlayList`` ever exists, and it is shared throughout the entire
application.
"""

import logging

import props

import fsl.data.imageio as iio


log = logging.getLogger(__name__)


class OverlayList(props.HasProperties):
    """Class representing a collection of overlays to be displayed together.

    Contains a :class:`props.properties_types.List` property called
    ``overlays``, containing overlay objects (e.g. :class:`.Image` or
    :class:`VTKModel`objects).

    An :class:`OverlayList` object has a few wrapper methods around the
    :attr:`overlays` property, allowing the :class:`OverlayList` to be used
    as if it were a list itself.

    There are no restrictions on the type of objects which may be contained
    in the ``OverlayList``, but all objects must have a few attributes:

      - ``name`` ...
    
      - ``dataSoruce`` ..
    """


    def __validateOverlay(self, atts, overlay):
        return (hasattr(overlay, 'name')      and 
                hasattr(overlay, 'dataSource'))

        
    overlays = props.List(
        listType=props.Object(allowInvalid=False,
                              validateFunc=__validateOverlay))
    """A list of overlay objects to be displayed"""

    
    def __init__(self, overlays=None):
        """Create an ``OverlayList`` object from the given sequence of
        overlays."""
        
        if overlays is None: overlays = []
        self.overlays.extend(overlays)


    def addOverlays(self, fromDir=None, addToEnd=True):
        """Convenience method for interactively adding overlays to this
        :class:`OverlayList`.
        """

        # TODO this only supports volumetric images
        images = iio.interactiveLoadImages(fromDir)
        
        if addToEnd: self.extend(      images)
        else:        self.insertAll(0, images)


    def find(self, name):
        """Returns the first overlay with the given name, or ``None`` if
        there is no overlay with said name.
        """
        for overlay in self.overlays:
            if overlay.name == name:
                return overlay
        return None
            

    # Wrappers around the overlays list property, allowing this
    # OverlayList object to be used as if it is actually a list.
    def __len__(self):
        return self.overlays.__len__()
    
    def __getitem__(self, key):
        return self.overlays.__getitem__(key)
    
    def __iter__(self):
        return self.overlays.__iter__()
    
    def __contains__(self, item):
        return self.overlays.__contains__(item)
    
    def __setitem__(self, key, val):
        return self.overlays.__setitem__(key, val)
    
    def __delitem__(self, key):
        return self.overlays.__delitem__(key)
    
    def index(self, item):
        return self.overlays.index(item)
    
    def count(self, item):
        return self.overlays.count(item)
    
    def append(self, item):
        return self.overlays.append(item)
    
    def extend(self, iterable):
        return self.overlays.extend(iterable)
    
    def pop(self, index=-1):
        return self.overlays.pop(index)
    
    def move(self, from_, to):
        return self.overlays.move(from_, to)
    
    def remove(self, item):
        return self.overlays.remove(item)
    
    def insert(self, index, item):
        return self.overlays.insert(index, item)
    
    def insertAll(self, index, items):
        return self.overlays.insertAll(index, items) 
