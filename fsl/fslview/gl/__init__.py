#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


def bootstrap(glVersion=None):

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
