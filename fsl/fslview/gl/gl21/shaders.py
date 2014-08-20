#!/usr/bin/env python
#
# shaders.py - Convenience functions for managing vetex/fragment shaders.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""
"""

import logging
log = logging.getLogger(__name__)

import os.path as op

import fsl.fslview.gl.glimage  as glimage
import fsl.fslview.gl.glcircle as glcircle

    
def getVertexShader(  globj): return _getShader(globj, 'vert')
def getFragmentShader(globj): return _getShader(globj, 'frag')


def _getShader(globj, shaderType):
    fname = _getFileName(globj, shaderType)
    with open(fname, 'rt') as f: src = f.read()
    return _preprocess(src)    


def _getFileName(globj, shaderType):

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
