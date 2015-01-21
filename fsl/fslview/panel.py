#!/usr/bin/env python
#
# panel.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides a single class - the :class:`FSLViewPanel`.


A :class:`FSLViewPanel` object is a :class:`wx.Panel` which provides some
sort of view of a collection of :class:`~fsl.data.image.Image` objects,
contained within an :class:`~fsl.data.image.ImageList`.


A :class:`ViewPanel` is also a :class:`~fsl.fslview.actions.ActionProvider`
instance - any actions which are specified during construction are exposed
to the user. Furthermore, any display configuration options which should be
made available available to the user should be added as
:class:`~props.PropertyBase` attributes of the :class:`FSLViewPanel`
subclass.

See the following for examples of :class:`ViewPanel` subclasses:

  - :class:`~fsl.fslview.views.OrthoPanel`
  - :class:`~fsl.fslview.views.LightBoxPanel`
  - :class:`~fsl.fslview.views.TimeSeriesPanel`
  - :class:`~fsl.fslview.controls.ImageListPanel`
  - :class:`~fsl.fslview.controls.ImageDisplayPanel`
  - :class:`~fsl.fslview.controls.LocationPanel`
"""


import logging
log = logging.getLogger(__name__)


import wx

import props

import fsl.data.image as fslimage

import actions
import displaycontext


class FSLViewPanel(wx.Panel, actions.ActionProvider):
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

    
    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 actionz=None):
        """Create a :class:`ViewPanel`.

        :arg parent:     The :mod:`wx` parent object of this panel.
        
        :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.
        
        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         instance.

        :arg actionz:    A dictionary containing ``{name -> function}``
                         actions (see
                         :class:`~fsl.fslview.actions.ActionProvider`).
        """
        
        wx.Panel.__init__(self, parent)
        actions.ActionProvider.__init__(self, imageList, displayCtx, actionz)

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


class ConfigPanel(wx.Panel):

    def __init__(self, parent, target, layout=None):

        
        wx.Panel.__init__(self, parent)
        self._name   = '{}_{}'.format(self.__class__.__name__, id(self))
        self._target = target
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._propPanel = props.buildGUI(self, target, view=layout)

        self._sizer.Add(self._propPanel, flag=wx.EXPAND, proportion=1)

        self.SetSizer(self._sizer)
        self.Layout()
