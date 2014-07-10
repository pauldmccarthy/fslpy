#!/usr/bin/env python
#
# controlpanel.py - Superclass for FSLView control panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single class, the :class:`ControlPanel`.

A :class:`ControlPanel` object is a :class:`wx.Panel` which allows the
user to configure some aspect of the currently displayed collection of
images (see :class`~fsl.data.image.ImageList`), the display of
that list (see :class:`~fsl.fslview.displaycontext.DisplayContext`),
and/or the display of the individual images (see
:class:`~fsl.fslview.displaycontext.ImageDisplay`).

See the following for examples of :class:`ControlPanel` subclasses:

  - :class:`~fsl.fslview.controls.ImageListPanel`
  - :class:`~fsl.fslview.controls.ImageDisplayPanel`
  - :class:`~fsl.fslview.controls.LocationPanel`
"""


import wx

import fsl.data.image as fslimage

import displaycontext


class ControlPanel(wx.Panel):
    """Superclass for FSLView control panels.
    
    A :class:`ControlPanel` has the following attributes, intended to be
    used by subclasses:
    
      - :attr:`_imageList`: A reference to the
        :class:`~fsl.data.image.ImageList` instance which contains the images
        being displayed.
    
      - :attr:`_displayCtx`: A reference to the
        :class:`~fsl.fslview.displaycontext.DisplayContext` instance, which
        contains display related properties about the :attr:`_imageList`.
    
      - :attr:`_name`: A unique name for this :class:`ControlPanel`. 
    """

    
    def __init__(self, parent, imageList, displayCtx):
        """Create a :class:`ControlPanel`.

        :arg parent:     The :mod:`wx` parent object for this panel.
        
        :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.
        
        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         instance.
        """ 
        wx.Panel.__init__(self, parent)

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
