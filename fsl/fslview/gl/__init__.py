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

 - slicecanvas_draw
 - lightboxcanvas_draw
 - glimagedata

"""


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

    thismod.slicecanvas_draw    = glpkg.slicecanvas_draw
    thismod.lightboxcanvas_draw = glpkg.lightboxcanvas_draw
    thismod.glimagedata         = glpkg.glimagedata
    thismod._bootstrapped       = True
