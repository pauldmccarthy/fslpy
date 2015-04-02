#!/usr/bin/env python
#
# textures.py - Management of OpenGL image textures.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains logic for creating OpenGL textureswhich will
potentially be shared between multiple parts of the program.

The :mod:`.texture` sub-module contains the definition of the :class:`Texture`
class, the base class for all texture types.

The main interface to this module comprises two functions:

  - :func:`getTexture`:    Return a :class:`Texture` instance, creating one if
                           it does not already exist.

  - :func:`deleteTexture`: Cleans up the resources used by a :class:`Texture`
                           instance when it is no longer needed.

You are also free to create and manage your own texture instances directly,
if you know that it will not be needed by other parts of the application.

"""


_allTextures = {}
"""This dictionary contains all of the textures which currently exist. The
key is the texture tag (see :func:`getTexture`), and the value is the
corresponding :class:`ImageTexture` object.
"""


def getTexture(textureType, name, *args, **kwargs):
    """Retrieve a texture  object for the given target object (with
    the given tag), creating one if it does not exist.

    :arg textureType: The type of texture required.
    
    :arg name:        An application-unique string to be associated with the
                      given texture. Future requests for a texture with the
                      same type and name will return the same :class:`Texture`
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
    :class:`ImageTexture` instance, and removes it from the
    :attr:`_allTextures` dictionary.
    """
    
    texture.destroy()
    _allTextures.pop(texture.getTextureName(), None)


# All *Texture classes are made accessible at the
# textures package level due to these imports
from imagetexture     import ImageTexture
from colourmaptexture import ColourMapTexture
# from selectiontexture import SelectionTexture
# from rendertexture    import RenderTexture
# from rendertexture    import ImageRenderTexture
