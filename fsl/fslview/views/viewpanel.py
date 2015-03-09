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
                                       agwFlags=(aui.AUI_MGR_ALLOW_FLOATING |
                                                 aui.AUI_MGR_LIVE_RESIZE))        
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

        # A very shitty necessity. When panes are floated,
        # the AuiManager sets the size of the floating frame
        # to the minimum size of the panel, without taking
        # into account the size of its borders/title bar,
        # meaning that the panel size is too small. Here,
        # we're just creating a dummy MiniFrame (from which
        # the AuiFloatingFrame derives), and saving the size
        # of its trimmings for later use in the togglePanel
        # method.
        ff         = wx.MiniFrame(self)

        # total size of frame
        size       = ff.GetSize().Get()

        # size of frame, sans trimmings
        clientSize = ff.GetClientSize().Get()
        
        ff.Destroy()

        self.__floatOffset = (size[0] - clientSize[0],
                              size[1] - clientSize[1])

        
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
        self.__auiMgrUpdate()


    def togglePanel(self, panelType, floatPane=False, *args, **kwargs):

        import fsl.fslview.layouts as layouts

        window = self.__panels.get(panelType, None)

        if window is not None:
            self.__onPaneClose(None, window)
            
        else:
            
            window   = panelType(
                self, self._imageList, self._displayCtx, *args, **kwargs)

            paneInfo = aui.AuiPaneInfo()

            if isinstance(window, fsltoolbar.FSLViewToolBar):
                paneInfo.ToolbarPane()

                # When the toolbar contents change,
                # update the layout, so that the
                # toolbar's new size is accommodated
                window.Bind(fsltoolbar.EVT_TOOLBAR_EVENT, self.__auiMgrUpdate)

            paneInfo.LeftDockable( False) \
                    .RightDockable(False) \
                    .Caption(strings.titles[window])                

            # Dock the pane at the position specified
            # in fsl.fslview.layouts.locations, or
            # at the top of the panel if there is no
            # location specified 
            if floatPane is False:

                paneInfo = paneInfo.Direction(
                    layouts.locations.get(window, aui.AUI_DOCK_TOP))

            # Or, for floating panes, centre the
            # floating pane on this ViewPanel 
            else:

                selfPos    = self.GetScreenPosition().Get()
                selfSize   = self.GetSize().Get()
                selfCentre = (selfPos[0] + selfSize[0] * 0.5,
                              selfPos[1] + selfSize[1] * 0.5)

                paneSize = window.GetBestSize().Get()
                panePos  = (selfCentre[0] - paneSize[0] * 0.5,
                            selfCentre[1] - paneSize[1] * 0.5)

                paneInfo = paneInfo \
                    .Float()        \
                    .FloatingPosition(panePos)
                    
            self.__auiMgr.AddPane(window, paneInfo)
            self.__panels[panelType] = window
            self.__auiMgrUpdate()
 

    def __selectedImageChanged(self, *a):
        """Called when the image list or selected image changed.

        This method is slightly hard-coded and hacky. For the time being, edit
        profiles are only going to be supported for ``volume`` image
        types, which are being displayed in ``id`` or ``pixdim`` space..
        This method checks the type of the selected image, and disables
        the ``edit`` profile option (if it is an option), so the user can
        only choose an ``edit`` profile on ``volume`` image types.
        """
        image = self._displayCtx.getSelectedImage()

        if image is None:
            return

        display     = self._displayCtx.getDisplayProperties(image)
        profileProp = self.getProp('profile')

        # edit profile is not an option -
        # nothing to be done
        if 'edit' not in profileProp.getChoices(self):
            return

        if image.imageType != 'volume' or \
           display.transform not in ('id', 'pixdim'):
            
            # change profile if needed,
            if self.profile == 'edit':
                self.profile = 'view'

            # and disable edit profile
            profileProp.disableChoice('edit', self)
            
        # Otherwise make sure edit
        # is enabled for volume images
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
        """Called when the current :attr:`profile` property changes. Tells
        the :class:`~fsl.fslview.profiles.ProfileManager` about the change.

        The ``ProfileManager`` will then update mouse/keyboard listeners
        according to the new profile.
        """

        self.__profileManager.changeProfile(self.profile)

    
    def __auiMgrUpdate(self, *a):
        """Calls the :meth:`~wx.lib.agw.aui.AuiManager.Update` method
        on the ``AuiManager`` instance that is managing this panel.

        Ensures that the position of any floating panels is preserved,
        as the ``AuiManager`` tends to move them about in some
        circumstances.
        """

        # When a panel is added/removed from the AuiManager,
        # the position of floating panels seems to get reset
        # to their original position, when they were created.
        # Here, we explicitly set the position of each
        # floating frame, so the AuiManager doesn't move our
        # windows about the place.
        # 
        # We also explicitly tell the AuiManager what the
        # current minimum and best sizes are for every panel
        for panel in self.__panels.values():
            paneInfo = self.__auiMgr.GetPane(panel)
            parent   = panel.GetParent()

            minSize   = panel.GetMinSize() .Get()
            bestSize  = panel.GetBestSize().Get()

            # See comments in __init__ about
            # this 'float offset' thing 
            floatSize = (bestSize[0] + self.__floatOffset[0],
                         bestSize[1] + self.__floatOffset[1])

            log.debug('New size for panel {} - min: {}, '
                      'best: {}, float: {}'.format(
                          type(panel).__name__, minSize, bestSize, floatSize))
            
            paneInfo.MinSize(     minSize)  \
                    .BestSize(    bestSize) \
                    .FloatingSize(floatSize)
                
            if paneInfo.IsFloating() and \
               isinstance(parent, aui.AuiFloatingFrame):
                paneInfo.FloatingPosition(parent.GetScreenPosition())

        self.__auiMgr.Update()

        
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
            self.__auiMgrUpdate()

        # WTF AUI. Sometimes this method gets called
        # twice for a panel, the second time with a
        # reference to a wx._wxpyDeadObject; in such
        # situations, the Destroy method call below
        # will result in an exception being raised.
        else:
            return
        
        panel.Destroy()
