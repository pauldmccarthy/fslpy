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

A :class:`ViewPanel` is also a :class:`~props.HasProperties` instance - any
display configuration options which should be made available available to the
user should be added as :class:`~props.PropertyBase` attributes of the
:class:`ViewPanel` subclass.

See the following for examples of :class:`ViewPanel` subclasses:

  - :class:`~fsl.fslview.views.OrthoPanel`
  - :class:`~fsl.fslview.views.LightBoxPanel`
  - :class:`~fsl.fslview.views.TimeSeriesPanel`
"""


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

      - :attr:`_glContext: A :class:`wx.glcanvas.GLContext` instance, if
        this :class:`ViewPanel` uses OpenGL, or ``None`` if it doesn't.

    Subclasses which use OpenGL to render their view must override the
    :meth:`isGLView` method to return ``True``.
    """ 
   
    @classmethod
    def isGLView(cls):
        """Method which returns ``True`` or ``False``, depending upon whether
        this :class:`ViewPanel` uses OpenGL.

        The default implementation returns ``False``. Subclasses which use
        OpenGL must override this subclass to return ``True``. 
        """
        return False

        
    @classmethod
    def hasConfigOptions(cls):
        """Method which returns ``True`` or ``False``, depending upon whether
        this :class:`ViewPanel` has any user-configurable properties.
        """
        return len(cls.getAllProperties()[0]) > 0
 
    
    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 glContext=None,
                 glVersion=None):
        """Create a :class:`ViewPanel`.

        :arg parent:     The :mod:`wx` parent object of this panel.
        
        :arg imageList:  A :class:`~fsl.data.image.ImageList` instance.
        
        :arg displayCtx: A :class:`~fsl.fslview.displaycontext.DisplayContext`
                         instance.
        
        :arg glContext:  A :class:`wx.glcanvas.GLContext` instance. If this
                         :class:`ViewPanel` uses OpenGL, it should use the
                         provided context. If the provided context is ``None``
                         this :class:`ViewPanel` should create its own
                         context, and store it as an attribute called
                         :attr:`_glContext`. If this :class:`ViewPanel` does
                         not use OpenGL, this parameter can be ignored.

        :arg glVersion:  A tuple containing the desired (major, minor) OpenGL
                         API version to use. If None, the best possible
                         version given the available hardware is used.
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

        if self.isGLView():
            self._glContext = glContext
            self._glVersion = glVersion
        else:
            self._glContext = None
            self._glVersion = None
