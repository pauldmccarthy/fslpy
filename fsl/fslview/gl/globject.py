#!/usr/bin/env python
#
# globject.py - Mapping between fsl.data.image types and OpenGL
# representations.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module defines the :class:`GLObject` class, which is a superclass for
all 2D representations of objects in OpenGL.

This module also provides the :func:`createGLObject` function, which provides
mappings between :class:`~fsl.data.image.Image` types, and their corresponding
OpenGL representation.
"""


import numpy as np


def createGLObject(image, display):
    """Create :class:`GLObject` instance for the given
    :class:`~fsl.data.image.Image` instance.

    :arg image:   A :class:`~fsl.data.image.Image` instance.
    :arg display: A :class:`~fsl.fslview.displaycontext.Display` instance.
    """

    import fsl.fslview.gl.glvolume     as glvolume
    import fsl.fslview.gl.glmask       as glmask
    import fsl.fslview.gl.glrgbvector  as glrgbvector
    import fsl.fslview.gl.gllinevector as gllinevector

    _objectmap = {
        'volume'     : glvolume    .GLVolume,
        'mask'       : glmask      .GLMask,
        'rgbvector'  : glrgbvector .GLRGBVector,
        'linevector' : gllinevector.GLLineVector
    } 

    ctr = _objectmap.get(display.imageType, None)

    if ctr is not None: return ctr(image, display)
    else:               return None


class GLObject(object):
    """The :class:`GLObject` class is a superclass for all 2D OpenGL
    objects.
    """

    def __init__(self):
        """Create a :class:`GLObject`.  The constructor adds one attribute to
        this instance, ``name``, which is simply a unique name for this
        instance.

        Subclass implementations must call this method, and should also
        perform any necessary OpenGL initialisation, such as creating
        textures.
        """

        self.name = '{}_{}'.format(type(self).__name__, id(self))
        self.__updateListeners = {}

        
    def addUpdateListener(self, name, listener):
        """Adds a listener function which will be called whenever this
        ``GLObject`` representation changes.

        The listener function must accept a single parameter, which is
        a reference to this ``GLObject``.
        """
        self.__updateListeners[name] = listener

        
    def removeUpdateListener(self, name):
        """Removes a listener previously registered via
        :meth:`addUpdateListener`.
        """
        self.__updateListeners.pop(name, None)


    def onUpdate(self):
        """This method must be called by subclasses whenever the GL object
        representation changes - it notifies any registered listeners of the
        change.
        """
        for name, listener in self.__updateListeners.items():
            listener(self)


    def getDisplayBounds(self):
        raise NotImplementedError('The getDisplayBounds method must be '
                                  'implemented by GLObject subclasses')


    def getDataResolution(self, xax, yax):
        return None

    
    def setAxes(self, xax, yax):
        """This method is called when the display orientation for this
        :class:`GLObject` changes. It should perform any necessary updates to
        the GL data (e.g. regenerating/moving vertices).
        """
        raise NotImplementedError()

    
    def destroy(self):
        """This method is called when this :class:`GLObject` is no longer
        needed.
        
        It should perform any necessary cleaning up, such as deleting texture
        handles.
        """
        raise NotImplementedError()

    
    def preDraw(self):
        """This method is called at the start of a draw routine.

        It should perform any initialisation which is required before one or
        more calls to the :meth:`draw` method are made, such as binding and
        configuring textures.
        """
        raise NotImplementedError()

    
    def draw(self, zpos, xform=None):
        """This method should draw a view of this :class:`GLObject` at the
        given Z position, which specifies the position along the screen
        depth axis.

        If the ``xform`` parameter is provided, it should be applied to the
        model view transformation before drawing.
        """
        raise NotImplementedError()


    def drawAll(self, zposes, xforms):
        """This method should do the same as multiple calls to the
        :meth:`draw` method, one for each of the Z positions and
        transformation matrices contained in the ``zposes`` and
        ``xforms`` arrays.

        In some circumstances (hint: the
        :class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas`),
        better performance may be achievbed in combining multiple
        renders, rather than doing it with separate calls to :meth:`draw`.

        The default implementation does exactly this, so this method
        need only be overridden for subclasses which are able to get
        better performance by combining the draws.
        """
        for (zpos, xform) in zip(zposes, xforms):
            self.draw(zpos, xform)


    def postDraw(self):
        """This method is called after the :meth:`draw` method has been called
        one or more times.

        It should perform any necessary cleaning up, such as unbinding
        textures.
        """
        raise NotImplementedError()


class GLSimpleObject(GLObject):
    """The ``GLSimpleObject`` class is a convenience superclass for simple
    rendering tasks (probably fixed-function) which require no setup or
    initialisation/management of GL memory or state. All subclasses need to
    do is implement the :meth:`GLObject.draw` method.

    Subclasses should not assume that any of the other methods will ever
    be called.

    On calls to :meth:`draw`, the following attributes will be available on
    ``GLSimpleObject`` instances:

      - ``xax``: Index of the display coordinate system axis that corresponds
                 to the horizontal screen axis.
      - ``yax``: Index of the display coordinate system axis that corresponds
                 to the vertical screen axis.
    """

    def __init__(self):
        GLObject.__init__(self)

    def setAxes(self, xax, yax):
        self.xax =  xax
        self.yax =  yax
        self.zax = 3 - xax - yax


    def destroy(self): pass
    def preDraw( self): pass
    def postDraw(self): pass


class GLImageObject(GLObject):
    """The ``GLImageObject` class is the superclass for all GL representations
    of :class:`~fsl.data.image.Image` instances.
    """
    
    def __init__(self, image, display):
        """Create a ``GLImageObject``.

        This constructor adds the following attributes to this instance:
        
          - ``image``:       A reference to the image.
          - ``display``:     A reference to the display.
          - ``displayOpts``: A reference to the image type-specific display
                             options.

        :arg image:   The :class:`~fsl.data.image.Image` instance
        :arg display: An associated
                      :class:`~fsl.fslview.displaycontext.Display` instance.
        """
        
        GLObject.__init__(self)
        self.image       = image
        self.display     = display
        self.displayOpts = display.getDisplayOpts()


    def getDisplayBounds(self):
        return self.display.getDisplayBounds()


    def getDataResolution(self, xax, yax):

        image   = self.image
        display = self.display
        res     = display.resolution 
        
        if display.transform in ('id', 'pixdim'):

            pixdim = np.array(image.pixdim[:3])
            steps  = [res, res, res] / pixdim
            res    = image.shape[:3] / steps
            
            return np.array(res.round(), dtype=np.uint32)
        
        else:
            lo, hi = display.getDisplayBounds()
            minres = int(round(((hi - lo) / res).min()))
            return [minres] * 3
