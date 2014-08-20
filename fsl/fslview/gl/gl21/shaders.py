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

def _getFilePrefix(globj):

    if   isinstance(globj, glimage.GLImage):
        return 'glimage'
    elif isinstance(globj, glcircle.GLCircle):
        return 'glimage'
    else:
        raise RuntimeError('Unknown GL object type: '
                           '{}'.format(type(globj)))
            

def getVertexShader(globj):
    prefix = _getFilePrefix(globj)
    fname  = op.join(op.dirname(__file__), '{}_vert.glsl'.format(prefix))

    with open(fname, 'rt') as f: src = f.read()
    return src
    

def getFragmentShader(globj):
    prefix = _getFilePrefix(globj)
    fname  = op.join(op.dirname(__file__), '{}_frag.glsl'.format(prefix))

    with open(fname, 'rt') as f: src = f.read()
    return src 
