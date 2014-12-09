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


class ProfileManager(object):


    def __init__(self, canvasPanel, imageList, displayCtx):

        import fsl.fslview.views.orthopanel    as orthopanel
        import fsl.fslview.views.lightboxpanel as lightboxpanel

        import orthoviewprofile
        import orthoeditprofile
        import lightboxviewprofile
        # import lightboxeditprofile
                
        self._canvasPanel = canvasPanel
        self._imageList   = imageList
        self._displayCtx  = displayCtx

        if isinstance(canvasPanel, orthopanel.OrthoPanel):
            self._viewProfile = orthoviewprofile
            self._editProfile = orthoeditprofile
            
        elif isinstance(canvasPanel, lightboxpanel.LightBoxPanel):
            self._viewProfile = lightboxviewprofile
            # self._editProfile = lightboxeditprofile

        self._currentProfile = None
        self._profileCtx     = None

        
    def changeProfile(self, profile):

        if   profile == 'view':
            newProfile = self._viewProfile
        elif profile == 'edit':
            newProfile = self._editProfile
        else:
            raise ValueError('Invalid profile specified: {}'.format(profile))
        
        if self._currentProfile is not None:
            self._currentProfile.deregister(self._profileCtx)
               
        self._currentProfile = newProfile
        self._profileCtx     = self._currentProfile.register(
            self._canvasPanel, self._imageList, self._displayCtx)
