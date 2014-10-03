#!/usr/bin/env python
#
# screengrab.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import wx

import fsl.fslview.action as action

import props


class ScreenGrabAction(action.Action):

    def doAction(self, *args):

        # app = wx.GetApp()

        # if app is None:
        #     raise RuntimeError('A wx.App has not been created')

        # dlg = wx.FileDialog(app.GetTopWindow(),
        #                     message='Save screenshot',
        #                     style=wx.FD_SAVE)

        # if dlg.ShowModal() != wx.ID_OK: return

        # filename = dlg.GetPath()

        # dlg.Destroy()
        # wx.Yield()

        # TODO In-memory-only images will not be
        # rendered - will need to save them to a temp file

        print
        print 'The screenshot feature has not yet been ' \
              'implemented - try using "~paulmc/fslpy render" '\
              'with something like the following:'
        print

        print '~paulmc/fslpy render -f out.png -s 2048 2048 ',
        print '-wl {}'.format(
            ' '.join(['{}'.format(v) for v in self._displayCtx.location.xyz])),
        
        for image in self._imageList:

            fname = image.nibImage.get_filename()

            # No support for in-memory images just yet
            if fname is None:
                continue

            display = image.getAttribute('display')

            args = props.generateArguments(display)
            
            print fname, ' '.join(['{}'.format(a) for a in args]),
