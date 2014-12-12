#!/usr/bin/env python
#
# The profiles module contains logic for mouse-keyboard interaction.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""The :mod:`profiles` module contains logic for mouse/keyboard interaction
with :class:`~fsl.fslview.views.canvaspanel.CanvasPanel` panels.
"""

import logging
log = logging.getLogger(__name__)


import props


class Profile(props.HasProperties):
    """
    Subclasses must define a props.Choice property called 'mode'.
    """

    def __init__(self, canvasPanel, imageList, displayCtx):
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx
        self._name        = '{}_{}'.format(self.__class__.__name__, id(self)) 

        # check that the subclass has
        # defined a 'mode' property
        try:
            self.getProp('mode')
        except KeyError:
            raise NotImplementedError('Profile subclasses must provide '
                                      'a property called mode')


    def register(self):
        raise NotImplementedError('Profile subclasses must implement '
                                  'a methocd called register')

    
    def deregister(self):
        raise NotImplementedError('Profile subclasses must implement '
                                  'a methocd called deregister') 


class ProfileManager(object):


    def __init__(self, canvasPanel, imageList, displayCtx):

        from fsl.fslview.views.orthopanel    import OrthoPanel
        from fsl.fslview.views.lightboxpanel import LightBoxPanel

        from orthoviewprofile    import OrthoViewProfile
        from orthoeditprofile    import OrthoEditProfile
        from lightboxviewprofile import LightBoxViewProfile
        # from lightboxeditprofile import LightBoxEditProfile

        self._profileMap = {
            ('view', OrthoPanel)    : OrthoViewProfile,
            ('edit', OrthoPanel)    : OrthoEditProfile,
            ('view', LightBoxPanel) : LightBoxViewProfile,
        }
                
        self._canvasPanel    = canvasPanel
        self._canvasCls      = canvasPanel.__class__
        self._imageList      = imageList
        self._displayCtx     = displayCtx
        self._currentProfile = None


    def getCurrentProfile(self):
        return self._currentProfile

        
    def changeProfile(self, profile):

        profileCls = self._profileMap[profile, self._canvasCls]

        if self._currentProfile is not None:
            log.debug('Deregistering {} profile from {}'.format(
                self._currentProfile.__class__.__name__,
                self._canvasCls.__name__))
            self._currentProfile.deregister()
               
        self._currentProfile = profileCls(self._canvasPanel,
                                          self._imageList,
                                          self._displayCtx)
        
        log.debug('Registering {} profile with {}'.format(
            self._currentProfile.__class__.__name__,
            self._canvasCls.__name__))
        
        self._currentProfile.register()
