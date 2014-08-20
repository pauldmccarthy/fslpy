#!/usr/bin/env python
#
# shaders.py - Convenience functions for managing vertex/fragment shaders.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""Convenience for managing vertex and fragment shader source code.

The :mod:`shaders` module provides convenience functions for accessing the
vertex and fragment shader source files used to render different types of GL
objects.

All shader programs and associated files are assumed to be located in the same
directory as this module (i.e. the :mod:`fsl.fslview.gl.gl21` package).

When a shader file is loaded, a simple preprocessor is applied to the source -
any lines of the form '#pragma include filename', will be replaced with the
contents of the specified file.
"""

import logging
log = logging.getLogger(__name__)

import os.path as op

import fsl.fslview.gl.glimage  as glimage
import fsl.fslview.gl.glcircle as glcircle

    
def getVertexShader(globj):
    """Returns the vertex shader source for the given GL object."""
    return _getShader(globj, 'vert')

    
def getFragmentShader(globj):
    """Returns the fragment shader source for the given GL object.""" 
    return _getShader(globj, 'frag')


def _getShader(globj, shaderType):
    """Returns the shader source for the given GL object and the given
    shader type ('vert' or 'frag').
    """
    fname = _getFileName(globj, shaderType)
    with open(fname, 'rt') as f: src = f.read()
    return _preprocess(src)    


def _getFileName(globj, shaderType):
    """Returns the file name of the shader program for the given GL object
    and shader type.
    """

    if shaderType not in ('vert', 'frag'):
        raise RuntimeError('Invalid shader type: {}'.format(shaderType))

    if   isinstance(globj, glimage .GLImage):  prefix = 'glimage'
    elif isinstance(globj, glcircle.GLCircle): prefix = 'glimage'
    else:
        raise RuntimeError('Unknown GL object type: '
                           '{}'.format(type(globj)))

    return op.join(op.dirname(__file__), '{}_{}.glsl'.format(
        prefix, shaderType))
 

def _preprocess(src):
    """'Preprocess' the given shader source.

    This amounts to searching for lines containing '#pragma include filename',
    and replacing those lines with the contents of the specified files.
    """

    lines    = src.split('\n')
    lines    = [l.strip() for l in lines]

    pragmas = []
    for linei, line in enumerate(lines):
        if line.startswith('#pragma'):
            pragmas.append(linei)

    includes = []
    for linei in pragmas:

        line = lines[linei].split()
        
        if len(line) != 3:       continue
        if line[1] != 'include': continue

        includes.append((linei, line[2]))

    for linei, fname in includes:
        fname = op.join(op.dirname(__file__), fname)
        with open(fname, 'rt') as f:
            lines[linei] = f.read()

    return '\n'.join(lines)
