#!/usr/bin/env python
#
# fsl.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import logging

import wx

import fsl.tools as tools

if __name__ == '__main__':

    logging.basicConfig(
        format='%(levelname)8s %(filename)20s %(lineno)4d: %(funcName)s - %(message)s',
        level=logging.DEBUG) 

    if len(sys.argv) != 2:
        print('usage: fsl.py toolname')
        sys.exit(1)

    modname = sys.argv[1]
    toolmod = getattr(tools, modname, None)

    if toolmod is None:
        print('Unknown tool: {}'.format(modname))
        sys.exit(1)

    Options = getattr(toolmod, 'Options', None)
    Frame   = getattr(toolmod, 'Frame',   None)

    if (Options is None) or (Frame is None):
        print('{} does not appear to be a valid tool'.format(modname))
        sys.exit(1)

    app   = wx.App()
    opts  = Options()
    frame = Frame(opts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to '''\
              '''set frontmost of process "Python" to true' ''')

    def checkFslDir():
        fsldir = os.environ.get('FSLDIR', None)
        if fsldir is None:

            msg = 'The FSLDIR environment variable is not set - '\
                'you will not be able to run {}.'.format(modname)

            wx.MessageDialog(
                frame,
                message=msg,
                style=wx.OK | wx.ICON_EXCLAMATION).ShowModal()
            app.Unbind(wx.EVT_IDLE)

    frame.Fit()
    frame.Show()
    #app.Bind(wx.EVT_IDLE, lambda e: checkFslDir())
    app.MainLoop()
