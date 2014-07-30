#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

def getGLPackage(glVersion=None):

    import OpenGL.GL as gl
    import gl14
    import gl21

    if glVersion is None:
        glVer = gl.glGetString(gl.GL_VERSION).split()[0]
        major, minor = map(int, glVer.split('.'))

    else:
        major, minor = glVersion

    if   major >= 2 and minor >= 1: return gl21
    elif major >= 1 and minor >= 4: return gl14
    else: raise RuntimeError('OpenGL 1.4 or newer is required')
