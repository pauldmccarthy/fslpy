#!/usr/bin/env python
#
# viewpanel.py - Superclass for FSLView view panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single class, the :class:`ViewPanel`.

A :class:`ViewPanel` object is a :class:`wx.Panel` which provides some sort of
view of a collection of :class:`~fsl.data.image.Image` objects, contained
within an :class:`~fsl.data.image.ImageList`.

See the following classes:

  - `~fsl.fslview.views.OrthoPanel`
  - `~fsl.fslview.views.LightBoxPanel`
  - `~fsl.fslview.views.TimeSeriesPanel`
"""

import wx
import props

import fsl.data.image             as fslimage
import fsl.fslview.displaycontext as displaycontext

class ViewPanel(wx.Panel, props.HasProperties):
    """Superclass for FSLView view panels.

    A :class:`ViewPanel` has the following attributes, intended to be
    used by subclasses:
    
      - :attr:`_imageList`: A reference to the
        :class:`~fsl.data.image.ImageList` instance which contains the images
        to be displayed.
    
      - :attr:`_displayCtx`: A reference to the
        :class:`~fsl.fslview.displaycontext.DisplayContext` instance, which
        contains display related properties about the :attr:`_imageList`.
    
      - :attr:`_name`: A unique name for this :class:`ViewPanel`.
    """

    
    def __init__(self, parent, imageList, displayCtx):
        """Create a :class:`ViewPanel`.

        :arg parent:     The :mod:`wx` parent object of this panel.
        
        :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.
        
        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         instance.
        """
        
        wx.Panel.__init__(self, parent)
        props.HasProperties.__init__(self)

        if not isinstance(imageList, fslimage.ImageList):
            raise TypeError(
                'imageList must be a fsl.data.image.ImageList instance')

        if not isinstance(displayCtx, displaycontext.DisplayContext):
            raise TypeError(
                'displayCtx must be a '
                'fsl.fslview.displaycontext.DisplayContext instance') 
 

        self._imageList  = imageList
        self._displayCtx = displayCtx
        self._name       = '{}_{}'.format(self.__class__.__name__, id(self))

        
    def hasConfigOptions(self):
        """Method which returns ``True`` or ``False``, depending upon whether
        this :class:`ViewPanel` has any user-configurable properties.
        """
        return len(self.getAllProperties()[0]) > 0
