#!/usr/bin/env python
#
# __init__.py - The fsl.fslview.gl package contains OpenGL data and
# rendering stuff for fslview.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""OpenGL data and rendering stuff for fslview.

This package contains the OpenGL rendering code used by FSLView. It contains a
number of modules which contain logic that is independent of the available
OpenGL version (e.g. the :class:`~fsl.fslview.gl.slicecanvas.SliceCanvas`
class), and also contains a number of sub-packages (currently two) which
contain OpenGL-version-dependent modules that are used by the version
independent ones.

The available OpenGL API version can only be determined once an OpenGL context
has been created, and a display is available for rendering. Therefore, the
package-level :func:`bootstrap` function is called by the version-independent
module classes as needed, to dynamically determine which version-dependent
modules should be loaded.  Users of this package should not need to worry
about any of this - just instantiate the GUI classes provided by the
version-independent modules (e.g. the
:class:`~fsl.fslview.gl.lightboxcanvas.LightBoxCanvas` class) as you would any
other :mod:`wx` widget.
"""


import os

# Using PyOpenGL 3.1 (and OSX Mavericks 10.9.4 on a MacbookPro11,3), the
# OpenGL.contextdata.setValue method throws 'unhashable type' TypeErrors
# unless we set these constants. I don't know why.
if os.environ.get('PYOPENGL_PLATFORM', None) == 'osmesa':
    import OpenGL
    OpenGL.ERROR_ON_COPY  = True 
    OpenGL.STORE_POINTERS = False


def bootstrap(glVersion=None):
    """Imports modules appropriate to the specified OpenGL version.

    The available OpenGL API version can only be queried once an OpenGL
    context is created, and a canvas is available to draw on. This makes
    things a bit complicated, because it means that we are only able to
    choose how to draw things when we actually need to draw them.

    This function should be called after an OpenGL context has been created,
    and a canvas is available for drawing, but before any attempt to draw
    anything.  It will figure out which version-dependent package needs to be
    loaded, and will attach all of the modules contained in said package to
    the :mod:`~fsl.fslview.gl` package.  The version-independent modules may
    then simply access these version-dependent modules through this module.

    :arg glVersion: A tuple containing the desired (major, minor) OpenGL API
                    version to use. If ``None``, the best possible API version
                    will be used.
    """

    import sys
    import OpenGL.GL as gl
    import gl14
    import gl21

    thismod = sys.modules[__name__]

    if hasattr(thismod, '_bootstrapped'):
        return 

    if glVersion is None:
        glVer        = gl.glGetString(gl.GL_VERSION).split()[0]
        major, minor = map(int, glVer.split('.'))
    else:
        major, minor = glVersion

    glpkg = None

    if   major >= 2 and minor >= 1: glpkg = gl21
    elif major >= 1 and minor >= 4: glpkg = gl14
    else: raise RuntimeError('OpenGL 1.4 or newer is required')

    thismod.glimage_funcs  = glpkg.glimage_funcs
    thismod.glcircle_funcs = glpkg.glcircle_funcs
    thismod._bootstrapped  = True


def getWXGLContext():

    import sys
    import wx
    import wx.glcanvas as wxgl

    thismod = sys.modules[__name__]
    
    if not hasattr(thismod, '_wxGLContext'):
        # We can't create a wx GLContext
        # without a wx GLCanvas. But we
        # can create a dummy one, and
        # destroy it immediately after
        # the context has been created
        frame  = wx.Frame(None)
        canvas = wxgl.GLCanvas(frame)

        frame.Show()
        frame.Update()
        wx.Yield()
        
        thismod._wxGLContext = wxgl.GLContext(canvas)
        thismod._wxGLContext.SetCurrent(canvas)
        frame.Destroy()

    return thismod._wxGLContext

    
def getOSMesaContext():

    import sys    
    import OpenGL.GL              as gl
    import OpenGL.raw.osmesa.mesa as osmesa
    import OpenGL.arrays          as glarrays

    thismod = sys.modules[__name__]
    
    if not hasattr(thismod, '_osmesaGLContext'):

        # We follow the same process as for the
        # wx.glcanvas.GLContext, described above
        dummy = glarrays.GLubyteArray.zeros((640, 480, 43))
        thismod._osmesaGLContext = osmesa.OSMesaCreateContext(gl.GL_RGBA, None)
        osmesa.OSMesaMakeCurrent(thismod._osmesaGLContext,
                                 dummy,
                                 gl.GL_UNSIGNED_BYTE,
                                 640,
                                 480) 

    return thismod._osmesaGLContext 


class OSMesaCanvasTarget(object):
    
    def __init__(self, width, height):
        import OpenGL.arrays as glarrays 
        self._width  = width
        self._height = height
        self._buffer = glarrays.GLubyteArray.zeros((height, width, 4))

    def _getSize(self):
        """Returns a tuple containing the canvas width and height."""
        return self._width, self._height

        
    def _setGLContext(self):
        import OpenGL.GL              as gl
        import OpenGL.raw.osmesa.mesa as osmesa
 
        """Configures the GL context to render to this canvas. """
        osmesa.OSMesaMakeCurrent(getOSMesaContext(),
                                 self._buffer,
                                 gl.GL_UNSIGNED_BYTE,
                                 self._width,
                                 self._height)

        
    def _refresh(self):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass

        
    def _postDraw(self):
        """Does nothing, see :method:`_refresh`."""
        pass



    def saveToFile(self, filename):
        """Saves the contents of this canvas as an image, to the specified
        file.
        """
        import OpenGL.GL        as gl
        import numpy            as np
        import matplotlib.image as mplimg
        
        ia  = gl.glReadPixels(
            0, 0,
            self._width, self._height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)
        
        img = np.fromstring(ia, dtype=np.uint8)
        img = img.reshape((self._height, self._width, 4))
        img = np.flipud(img)
        mplimg.imsave(filename, img) 


class WXGLCanvasTarget(object):


    def __init__(self):

        import wx

        self._glReady = False
        self.Bind(wx.EVT_PAINT, self._mainDraw)
    

    def _initGL(self):
        raise NotImplementedError()


    def _draw(self):
        raise NotImplementedError()
 
        
    def _mainDraw(self, *a):

        import wx

        def doInit(*a):
            self._setGLContext()
            self._initGL()
            self._glReady = True
            self._draw()

        if not self._glReady:
            wx.CallAfter(doInit)
            return

        if not self._setGLContext():
            return

        self._draw()

        
    def _getSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()

        
    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas."""
        
        if not self.IsShownOnScreen(): return False
        getWXGLContext().SetCurrent(self)
        return True

        
    def _refresh(self):
        """Triggers a redraw via the :mod:`wx` `Refresh` method."""
        self.Refresh()

        
    def _postDraw(self):
        """Called after the scene has been rendered. Swaps the front/back
        buffers. 
        """
        self.SwapBuffers()
