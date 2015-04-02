#!/usr/bin/env python
#
# textures.py - Management of OpenGL image textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package is a container for a collection of classes which use OpenGL
textures for various purposes. It also contains a simple system for managing
OpenGL textures which will potentially be shared between multiple parts of the
program.

The :mod:`.texture` sub-module contains the definition of the :class:`Texture`
class, the base class for all texture types.

The shared texture management interface comprises two functions:

  - :func:`getTexture`:    Return a :class:`Texture` instance, creating one if
                           it does not already exist.

  - :func:`deleteTexture`: Cleans up the resources used by a :class:`.Texture`
                           instance when it is no longer needed.

You are also free to create and manage your own texture instances directly,
if you know that it will not be needed by other parts of the application.
"""


_allTextures = {}
"""This dictionary contains all of the textures which currently exist. The key
is a combination of the texture namem, and the texture type, and the value is
the corresponding :class:`.Texture` object.

See :func:`getTexture` and :func:`deleteTexture`.
"""


def getTexture(textureType, name, *args, **kwargs):
    """Retrieve a texture object for the given target object (with
    the given name), creating one if it does not exist.

    :arg textureType: The type of texture required.
    
    :arg name:        An application-unique string to be associated with the
                      given texture. Future requests for a texture with the
                      same type and name will return the same :class:`.Texture`
                      instance.
    
    :arg args:        Texture type specific constructor arguments.
    
    :arg kwargs:      Texture type specific constructor arguments.
    """

    name       = '{}_{}'.format(textureType.__name__, name)
    textureObj = _allTextures.get(name, None)

    if textureObj is None:
        textureObj = textureType(name, *args, **kwargs)
        _allTextures[name] = textureObj

    return textureObj


def deleteTexture(texture):
    """Releases the OpenGL memory associated with the given
    :class:`.Texture` instance, and removes it from the
    :attr:`_allTextures` dictionary.
    """
    
    if _allTextures.pop(texture.getTextureName(), None) is not None:
        texture.destroy()


# All *Texture classes are made available at the
# textures package level due to these imports
from texture          import Texture
from texture          import Texture2D
from imagetexture     import ImageTexture
from colourmaptexture import ColourMapTexture
from selectiontexture import SelectionTexture
from rendertexture    import RenderTexture
from rendertexture    import ImageRenderTexture
