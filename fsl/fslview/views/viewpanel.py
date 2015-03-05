#!/usr/bin/env python
#
# viewpanel.py - Superclass for all FSLView view panels.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`ViewPanel` class, which is the superclass
of all of the 'view' panels available in FSLView - see
:class:`~fsl.fslview.frame.FSLViewFrame`.
"""

import logging

import                   wx
import wx.lib.agw.aui as aui

import props

import fsl.fslview.panel    as fslpanel
import fsl.fslview.toolbar  as fsltoolbar
import fsl.fslview.profiles as profiles
import fsl.data.strings     as strings


log = logging.getLogger(__name__)


class ViewPanel(fslpanel.FSLViewPanel):

    profile = props.Choice()
    
    def __init__(self, parent, imageList, displayCtx, actionz=None):

        fslpanel.FSLViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        self.__profileManager = profiles.ProfileManager(
            self, imageList, displayCtx)

        self.__panels = {}

        self.__auiMgr = aui.AuiManager(self,
                                       agwFlags=aui.AUI_MGR_ALLOW_FLOATING) 
        self.__auiMgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onPaneClose)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name 
        lName = 'ViewPanel_{}'.format(self._name)
        
        self.addListener('profile', lName, self.__profileChanged)
        
        imageList .addListener('images',
                               lName,
                               self.__selectedImageChanged)
        displayCtx.addListener('selectedImage',
                               lName,
                               self.__selectedImageChanged)

        self.__selectedImageChanged()

        
    def destroy(self):
        fslpanel.FSLViewPanel.destroy(self)
        
        # Make sure that any control panels are correctly destroyed
        for panelType, panel in self.__panels.items():
            panel.destroy()
            
        lName = '{}_{}'.format(type(self).__name__, self._name)
        self._imageList .removeListener('images',        lName)
        self._displayCtx.removeListener('selectedImage', lName) 


    def setCentrePanel(self, panel):
        panel.Reparent(self)
        self.__auiMgr.AddPane(panel, wx.CENTRE)
        self.__auiMgr.Update()


    def togglePanel(self, panelType, floatPane=False, *args, **kwargs):

        window = self.__panels.get(panelType, None)

        if window is not None:
            self.__onPaneClose(None, window)
            
        else:

            # TODO Existing floating panels seem to get
            #      moved about when a new panel is
            #      opened. Do something about that.
            
            window   = panelType(
                self, self._imageList, self._displayCtx, *args, **kwargs)
            paneInfo = aui.AuiPaneInfo()        \
                .MinSize(window.GetMinSize())   \
                .BestSize(window.GetBestSize()) \
                .LeftDockable(False)            \
                .RightDockable(False)           \
                .Caption(strings.titles[window])

            if isinstance(window, fsltoolbar.FSLViewToolBar):
                paneInfo = paneInfo.ToolbarPane().Resizable(False)

            if floatPane is False:
                paneInfo = paneInfo.Top()
            else:
                # Centre the floating pane on this pane
                selfPos    = self.GetScreenPosition().Get()
                selfSize   = self.GetSize().Get()
                selfCentre = (selfPos[0] + selfSize[0] * 0.5,
                              selfPos[1] + selfSize[1] * 0.5)

                paneSize = window.GetBestSize().Get()
                panePos  = (selfCentre[0] - paneSize[0] * 0.5,
                            selfCentre[1] - paneSize[1] * 0.5)
                
                paneInfo = paneInfo.Float().FloatingPosition(panePos)
                    
            self.__auiMgr.AddPane(window, paneInfo)
            self.__panels[panelType] = window
            
        self.__auiMgr.Update()


    def __selectedImageChanged(self, *a):
        """Called when the image list or selected image changed.

        This method is slightly hard-coded and hacky. For the time being, edit
        profiles are only going to be supported for ``volume`` image
        types. This method checks the type of the selected image, and disables
        the ``edit`` profile option (if it is an option), so the user can
        only choose an ``edit`` profile on ``volume`` image types.
        """
        image = self._displayCtx.getSelectedImage()

        if image is None:
            return

        profileProp = self.getProp('profile')

        # edit profile is not an option -
        # nothing to be done
        if 'edit' not in profileProp.getChoices(self):
            return

        if image.imageType != 'volume':
            
            # change profile if needed,
            if self.profile == 'edit':
                self.profile = 'view'

            # and disable edit profile
            profileProp.disableChoice('edit', self)
            
        # make sure edit is enabled for volume images
        else:
            profileProp.enableChoice('edit', self)


    def initProfile(self):
        """Must be called by subclasses, after they have initialised all
        of the attributes which may be needed by their corresponding
        Profile instances. 
        """
        self.__profileChanged()


    def getCurrentProfile(self):
        return self.__profileManager.getCurrentProfile()

        
    def __profileChanged(self, *a):

        self.__profileManager.changeProfile(self.profile)

        # profile = self.getCurrentProfile()

        # Profile mode changes may result in the 
        # content of the above prop/action panels 
        # changing. So we need to make sure that 
        # the canvas panel is sized appropriately.
        # def modeChange(*a):
        #     self.__layout()
            
        # profile.addListener('mode', self._name, modeChange)
    
        
    def __onPaneClose(self, ev=None, panel=None):

        if ev is not None:
            ev.Skip()
            panel = ev.GetPane().window

        log.debug('Panel closed: {}'.format(type(panel).__name__))
        
        if isinstance(panel, (fslpanel  .FSLViewPanel,
                              fsltoolbar.FSLViewToolBar)):
            self.__panels.pop(type(panel))

            # calling fslpanel.FSLViewPanel.destroy()
            # here -  wx.Destroy is done below
            panel.destroy()

            # Even when the user closes a pane,
            # AUI does not detach said pane -
            # we have to do it manually
            self.__auiMgr.DetachPane(panel)
            self.__auiMgr.Update()

        # WTF AUI. Sometimes this method gets called
        # twice for a panel, the second time with a
        # reference to a wx._wxpyDeadObject; in such
        # situations, the Destroy method call below
        # will result in an exception being raised.
        else:
            return
        
        panel.Destroy()
