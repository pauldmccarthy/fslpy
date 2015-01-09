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

Two methods of OpenGL usage are supported:

  - On-screen display of a scene using a :class:`wx.glcanvas.GLCanvas` canvas.

  - Off-screen renering of a scene using OSMesa.

Two super classes are provided for each of these cases:

 - The :class:`WXGLCanvasTarget` class for on-screen rendering using
   :mod:`wx`.

 - The :class:`OSMesaCanvasTarget` class for off-screen rendering using
   OSMesa.
"""

import            logging 
import            os
import os.path as op
import            OpenGL


log = logging.getLogger(__name__)


# Make PyOpenGL throw an error, instead of implicitly
# converting, if we pass incorrect types to OpenGL functions.
OpenGL.ERROR_ON_COPY = True 


# Using PyOpenGL 3.1 (and OSX Mavericks 10.9.4 on a MacbookPro11,3), the
# OpenGL.contextdata.setValue method throws 'unhashable type' TypeErrors
# unless we set STORE_POINTERS to False. I don't know why.
if os.environ.get('PYOPENGL_PLATFORM', None) == 'osmesa':
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

    if   major >= 2 and minor >= 1:
        verstr = '2.1'
        glpkg  = gl21
    elif major >= 1 and minor >= 4:
        verstr = '1.4'
        glpkg  = gl14
    else: raise RuntimeError('OpenGL 1.4 or newer is required')

    # The gl21 implementation depends on a
    # few extensions - if they're not present,
    # fall back to the gl14 implementation
    if glpkg == gl21:

        import OpenGL.extensions as glexts

        exts = ['GL_ARB_texture_rg',
                'GL_EXT_gpu_shader4']
        
        exts = map(glexts.hasExtension, exts)
        
        if not all(exts):
            verstr = '1.4'
            glpkg = gl14

    log.debug('Using OpenGL {} implementation'.format(verstr))

    thismod.glimage_funcs  = glpkg.glimage_funcs
    thismod._bootstrapped  = True


def getWXGLContext():
    """Create and return a GL context object for rendering to a
    :class:`wx.glcanvas.GLCanvas` canvas.

    If a context object has already been created, it is returned.
    Otherwise, one is created and returned.
    """

    import sys
    import wx
    import wx.glcanvas as wxgl

    thismod = sys.modules[__name__]
    
    if not hasattr(thismod, '_wxGLContext'):

        # This is a ridiculous problem.  We can't create a
        # wx GLContext without a wx GLCanvas. But we can
        # create a dummy one, and destroy it immediately
        # after the context has been created.  An excuse 
        # to display a splash screen ...
        splashfile  = op.join(op.dirname(__file__), 'splash.png')
        frame = wx.SplashScreen(
            wx.Bitmap(splashfile, wx.BITMAP_TYPE_PNG),
            wx.SPLASH_CENTRE_ON_SCREEN | wx.SPLASH_NO_TIMEOUT,
            -1,
            None)
        canvas = wxgl.GLCanvas(frame)
        canvas.SetSize((0, 0))

        # Even worse - on Linux/GTK,the canvas
        # has to visible before we are able to
        # set it as the target of the GL context
        frame.Update()
        frame.Show()
        wx.Yield()
        
        thismod._wxGLContext = wxgl.GLContext(canvas)
        thismod._wxGLContext.SetCurrent(canvas)
        
        wx.CallAfter(frame.Close)


    return thismod._wxGLContext

    
def getOSMesaContext():
    """Create and return a GL context object for off-screen rendering using
    OSMesa.
    """

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
    """Superclass for canvas objects which support off-screen rendering using
    OSMesa.
    """
    
    def __init__(self, width, height, bgColour=(0, 0, 0, 255)):
        """Creates an off-screen buffer to be used as the render target.

        :arg width:    Width in pixels
        :arg height:   Height in pixels
        :arg bgColour: Background colour as an RGBA tuple
                       (e.g. (255, 255, 255, 255))
        """
        import OpenGL.arrays as glarrays 
        self._width    = width
        self._height   = height 
        self._bgColour = bgColour 
        self._buffer   = glarrays.GLubyteArray.zeros((height, width, 4))

        
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

        
    def _refresh(self, *a):
        """Does nothing. This canvas is for static (i.e. unchanging) rendering.
        """
        pass

        
    def _postDraw(self):
        """Does nothing, see :method:`_refresh`."""
        pass


    def _draw(self):
        """Must be provided by subclasses."""
        raise NotImplementedError()


    def draw(self):
        """Calls the :meth:`_draw` method, which must be provided by
        subclasses.
        """

        import OpenGL.GL as gl
        
        self._initGL()
        self._setGLContext()
        gl.glClearColor(*self._bgColour)
        self._draw()

        
    def getBitmap(self):
        """Return a (width*height*4) shaped numpy array containing the
        rendered scene as an RGBA bitmap. The bitmap will be full of
        zeros if the scene has not been drawn (via a call to
        :meth:`draw`).
        """
        import OpenGL.GL        as gl
        import numpy            as np

        self._setGLContext()
        
        bmp = gl.glReadPixels(
            0, 0,
            self._width, self._height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE)
        
        bmp = np.fromstring(bmp, dtype=np.uint8)
        bmp = bmp.reshape((self._height, self._width, 4))
        bmp = np.flipud(bmp)

        return bmp


    def saveToFile(self, filename):
        """Saves the contents of this canvas as an image, to the specified
        file.
        """
        import matplotlib.image as mplimg
        mplimg.imsave(filename, self.getBitmap()) 


class WXGLCanvasTarget(object):
    """Superclass for :class:`wx.glcanvas.GLCanvas` objects objects.

    It is assumed that subclasses of this superclass are also subclasses of
    :class:`wx.glcanvas.GLCanvas`
    """


    def __init__(self):
        """Binds :attr:`wx.EVT_PAINT` events to the :meth:`_mainDraw` method.
        """

        import wx

        self._glReady = False
        self.Bind(wx.EVT_PAINT, self._mainDraw)
    

    def _initGL(self):
        """Must be implemented by subclasses.

        This method should perform any OpenGL data initialisation required for
        rendering.
        """
        raise NotImplementedError()


    def _draw(self):
        """Must be implemented by subclasses.

        This method should implement the OpenGL drawing logic.
        """
        raise NotImplementedError()
 
        
    def _mainDraw(self, *a):
        """Called on :attr:`wx.EVT_PAINT` events.

        This method calls :meth:`_initGL` if it has not already been called.
        Otherwise, it calls the subclass :meth:`_draw` method.
        """

        import wx

        def doInit(*a):
            self._initGL()
            self._glReady = True
            self._draw()

        if not self._glReady:
            wx.CallAfter(doInit)
            return

        self._draw()

        
    def _getSize(self):
        """Returns the current canvas size. """
        return self.GetClientSize().Get()

        
    def _setGLContext(self):
        """Configures the GL context for drawing to this canvas.

        This method should be called before any OpenGL operations related to
        this canvas take place (e.g. texture/data creation, drawing, etc).
        """
        if not self.IsShownOnScreen(): return False
        getWXGLContext().SetCurrent(self)
        return True

        
    def _refresh(self, *a):
        """Triggers a redraw via the :mod:`wx` `Refresh` method."""
        self.Refresh()

        
    def _postDraw(self):
        """Called after the scene has been rendered. Swaps the front/back
        buffers. 
        """
        self.SwapBuffers()
