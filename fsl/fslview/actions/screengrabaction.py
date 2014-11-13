#!/usr/bin/env python
#
# screengrab.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)


import subprocess
import wx

import props

import fsl.fslview.action              as action
import fsl.fslview.views.canvaspanel   as canvaspanel
import fsl.fslview.views.lightboxpanel as lightboxpanel
import fsl.fslview.views.orthopanel    as orthopanel


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

        # TODO Support output of multiple views?

        # Get the currently active view panel
        viewPanel = self._fslviewframe._centrePane.GetPage(
            self._fslviewframe._centrePane.GetSelection())

        # TODO support view panels other than lightbox/ortho? 
        if not isinstance(viewPanel, canvaspanel.CanvasPanel):
            return

        width, height = viewPanel.GetClientSize().Get()

        argv  = []
        argv += ['--outfile', 'out.png']
        argv += ['--size', '{}'.format(width), '{}'.format(height)]
        argv += ['--background', '0', '0', '0', '255']

        # TODO get location from panel - if possync
        # is false, this will be wrong
        argv += ['--worldloc']
        argv += ['{}'.format(c) for c in self._displayCtx.location.xyz]
        argv += ['--selectedImage']
        argv += ['{}'.format(self._displayCtx.selectedImage)]

        if not viewPanel.showCursor:
            argv += ['--hideCursor']

        if viewPanel.showColourBar:
            argv += ['--showColourBar']
            argv += ['--colourBarLocation']
            argv += [viewPanel.colourBarLocation]
            argv += ['--colourBarLabelSide']
            argv += [viewPanel.colourBarLabelSide] 

        #
        if isinstance(viewPanel, orthopanel.OrthoPanel):
            if not viewPanel.showXCanvas: argv += ['--hidex']
            if not viewPanel.showYCanvas: argv += ['--hidey']
            if not viewPanel.showZCanvas: argv += ['--hidez']
            if not viewPanel.showLabels:  argv += ['--hideLabels']

            argv += ['--xzoom', '{}'.format(viewPanel.xzoom)]
            argv += ['--yzoom', '{}'.format(viewPanel.yzoom)]
            argv += ['--zzoom', '{}'.format(viewPanel.zzoom)]
            argv += ['--layout',            viewPanel.layout]

            xbounds = viewPanel._xcanvas.displayBounds
            ybounds = viewPanel._ycanvas.displayBounds
            zbounds = viewPanel._zcanvas.displayBounds

            xx = xbounds.xlo + (xbounds.xhi - xbounds.xlo) * 0.5
            xy = xbounds.ylo + (xbounds.yhi - xbounds.ylo) * 0.5
            yx = ybounds.xlo + (ybounds.xhi - ybounds.xlo) * 0.5
            yy = ybounds.ylo + (ybounds.yhi - ybounds.ylo) * 0.5
            zx = zbounds.xlo + (zbounds.xhi - zbounds.xlo) * 0.5
            zy = zbounds.ylo + (zbounds.yhi - zbounds.ylo) * 0.5

            argv += ['--xcentre', '{}'.format(xx), '{}'.format(xy)]
            argv += ['--ycentre', '{}'.format(yx), '{}'.format(yy)]
            argv += ['--zcentre', '{}'.format(zx), '{}'.format(zy)]

            
        elif isinstance(viewPanel, lightboxpanel.LightBoxPanel):
            argv += ['--lightbox']
            argv += ['--sliceSpacing',  '{}'.format(viewPanel.sliceSpacing)]
            argv += ['--nrows',         '{}'.format(viewPanel.nrows)]
            argv += ['--ncols',         '{}'.format(viewPanel.ncols)]
            argv += ['--zrange',        '{}'.format(viewPanel.zrange)]
            argv += ['--showGridLines', '{}'.format(viewPanel.showGridLines)]
            argv += ['--zax',           '{}'.format(viewPanel.zax)]
        
        for image in self._imageList:

            fname = image.nibImage.get_filename()

            # No support for in-memory images just yet
            if fname is None:
                continue

            display = self._displayCtx.getDisplayProperties(image)
            imgArgv = props.generateArguments(display)

            argv += ['--image', fname] + imgArgv

        argv = ' '.join(argv).split()
        print argv

        subprocess.call(['fsl.py', 'render'] + argv)
