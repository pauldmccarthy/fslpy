#!/usr/bin/env python
#
# loadcolourmap.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
import os.path as op

import fsl.data.strings                      as strings
import fsl.fslview.actions                   as actions
import fsl.fslview.colourmaps                as fslcmap
import fsl.fslview.displaycontext.volumeopts as volumeopts


# TODO You will need to patch ColourMap instances
# for any new display option types


log = logging.getLogger(__name__)


_stringID = 'actions.loadcolourmap.'


class LoadColourMapAction(actions.Action):
    
    def doAction(self):

        import wx

        app = wx.GetApp()

        # prompt the user to choose a colour map file
        dlg = wx.FileDialog(
            app.GetTopWindow(),
            message=strings.messages[_stringID + 'loadcmap'],
            style=wx.FD_OPEN)

        if dlg.ShowModal() != wx.ID_OK:
            return

        # prompt the user to choose  a name for the colour
        # map (using the filename prefix as the default)
        cmapFile = dlg.GetPath()
        cmapName = op.splitext(op.basename(cmapFile))[0]

        cmapNameMsg = strings.messages[_stringID + 'namecmap']

        while True:

            dlg = wx.TextEntryDialog(
                app.GetTopWindow(),
                message=cmapNameMsg,
                defaultValue=cmapName)

            if dlg.ShowModal() != wx.ID_OK:
                return

            cmapName = dlg.GetValue()

            # a colour map with the specified name already exists
            if fslcmap.isRegistered(cmapName):
                cmapNameMsg = strings.messages[_stringID + 'alreadyinstalled']
                continue

            # colour map names must only contain 
            # letters, numbers, and underscores
            if not cmapName.replace('_', '').isalnum():
                cmapNameMsg = strings.messages[_stringID + 'invalidname']
                continue

            break

        # register the selected colour map file
        fslcmap.registerColourMap(cmapFile, cmapName)

        # update the VolumeOpts colour map property ...
        #
        # for future images
        volumeopts.VolumeOpts.cmap.setConstraint(
            None,
            'cmapNames',
            fslcmap.getColourMaps())

        # and for any existing VolumeOpts instances
        for image in self._imageList:
            display = self._displayCtx.getDisplayProperties(image)
            opts    = display.getDisplayOpts()
            if isinstance(opts, volumeopts.VolumeOpts):
                opts.setConstraint('cmap',
                                   'cmapNames',
                                   fslcmap.getColourMaps())

        # ask the user if they want to install
        # the colour map for future use
        dlg = wx.MessageDialog(
            app.GetTopWindow(),
            message=strings.messages['actions.loadcolourmap.installcmap'],
            style=wx.YES_NO)

        if dlg.ShowModal() != wx.ID_YES:
            return

        # install the colour map
        try:
            fslcmap.installColourMap(cmapName)
            
        except Exception as e:
            log.warn('Error installing colour map: {}'.format(e))
            wx.MessageDialog(
                app.GetTopWindow(),
                message='{}: {}'.format(
                    strings.messages[_stringID + 'installerror'], str(e)),
                style=wx.ICON_ERROR).ShowModal()
