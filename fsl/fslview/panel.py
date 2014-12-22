#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides two classes - the :class:`ControlPanel`, and the
:class:`ViewPanel`.


A :class:`ViewPanel` object is a :class:`wx.Panel` which provides some sort of
view of a collection of :class:`~fsl.data.image.Image` objects, contained
within an :class:`~fsl.data.image.ImageList`.


A :class:`ViewPanel` is also a :class:`~props.HasProperties` instance - any
display configuration options which should be made available available to the
user should be added as :class:`~props.PropertyBase` attributes of the
:class:`ViewPanel` subclass.


See the following for examples of :class:`ViewPanel` subclasses:

  - :class:`~fsl.fslview.views.OrthoPanel`
  - :class:`~fsl.fslview.views.LightBoxPanel`
  - :class:`~fsl.fslview.views.TimeSeriesPanel`


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


import logging
log = logging.getLogger(__name__)


import wx

import props

import fsl.data.image as fslimage

import displaycontext


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
   
    @classmethod
    def hasConfigOptions(cls):
        """Method which returns ``True`` or ``False``, depending upon whether
        this :class:`ViewPanel` has any user-configurable properties.
        """
        return len(cls.getAllProperties()[0]) > 0
 
    
    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
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
