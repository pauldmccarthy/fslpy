#!/usr/bin/env python
#
# canvaspanel.py - Base class for all panels that display image data.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`CanvasPanel` class, which is the base
class for all panels which display image data (e.g. the
:class:`~fsl.fslview.views.orthopanel.OrthoPanel` and the
:class:`~fsl.fslview.views.lightboxpanel.LightBoxPanel`).

"""

import logging
log = logging.getLogger(__name__)

import subprocess

import wx

import props

import fsl.data.strings                         as strings
import fsl.fslview.displaycontext               as displayctx
import fsl.fslview.controls.imagelistpanel      as imagelistpanel
# import fsl.fslview.controls.imagedisplaypanel as imagedisplaypanel
import fsl.fslview.controls.imagedisplaytoolbar as imagedisplaytoolbar
import fsl.fslview.controls.locationpanel       as locationpanel
import fsl.fslview.controls.atlaspanel          as atlaspanel
import                                             colourbarpanel
import                                             viewpanel


def _takeScreenShot(imageList, displayCtx, canvas):

    import fsl.fslview.views.orthopanel    as orthopanel
    import fsl.fslview.views.lightboxpanel as lightboxpanel
    
    dlg = wx.FileDialog(canvas,
                        message='Save screenshot',
                        style=wx.FD_SAVE)

    if dlg.ShowModal() != wx.ID_OK: return

    filename = dlg.GetPath()

    dlg.Destroy()
    wx.Yield()

    # TODO In-memory-only images will not be rendered -
    # will need to save them to a temp file or
    # alternately prompt the user to save all in memory
    # images and try again

    # TODO support view panels other than lightbox/ortho? 
    if not isinstance(canvas, CanvasPanel):
        return

    width, height = canvas.getCanvasPanel().GetClientSize().Get()

    argv  = []
    argv += ['--outfile', filename]
    argv += ['--size', '{}'.format(width), '{}'.format(height)]
    argv += ['--background', '0', '0', '0', '255']

    # TODO get location from panel - if possync
    # is false, this will be wrong
    argv += ['--worldloc']
    argv += ['{}'.format(c) for c in displayCtx.location.xyz]
    argv += ['--selectedImage']
    argv += ['{}'.format(displayCtx.selectedImage)]

    if not canvas.showCursor:
        argv += ['--hideCursor']

    if canvas.colourBarIsShown():
        argv += ['--showColourBar']
        argv += ['--colourBarLocation']
        argv += [canvas.colourBarLocation]
        argv += ['--colourBarLabelSide']
        argv += [canvas.colourBarLabelSide] 

    #
    if isinstance(canvas, orthopanel.OrthoPanel):
        if not canvas.showXCanvas: argv += ['--hidex']
        if not canvas.showYCanvas: argv += ['--hidey']
        if not canvas.showZCanvas: argv += ['--hidez']
        if not canvas.showLabels:  argv += ['--hideLabels']

        argv += ['--xzoom', '{}'.format(canvas.xzoom)]
        argv += ['--yzoom', '{}'.format(canvas.yzoom)]
        argv += ['--zzoom', '{}'.format(canvas.zzoom)]
        argv += ['--layout',            canvas.layout]

        xbounds = canvas._xcanvas.displayBounds
        ybounds = canvas._ycanvas.displayBounds
        zbounds = canvas._zcanvas.displayBounds

        xx = xbounds.xlo + (xbounds.xhi - xbounds.xlo) * 0.5
        xy = xbounds.ylo + (xbounds.yhi - xbounds.ylo) * 0.5
        yx = ybounds.xlo + (ybounds.xhi - ybounds.xlo) * 0.5
        yy = ybounds.ylo + (ybounds.yhi - ybounds.ylo) * 0.5
        zx = zbounds.xlo + (zbounds.xhi - zbounds.xlo) * 0.5
        zy = zbounds.ylo + (zbounds.yhi - zbounds.ylo) * 0.5

        argv += ['--xcentre', '{}'.format(xx), '{}'.format(xy)]
        argv += ['--ycentre', '{}'.format(yx), '{}'.format(yy)]
        argv += ['--zcentre', '{}'.format(zx), '{}'.format(zy)]


    elif isinstance(canvas, lightboxpanel.LightBoxPanel):
        argv += ['--lightbox']
        argv += ['--sliceSpacing',  '{}'.format(canvas.sliceSpacing)]
        argv += ['--nrows',         '{}'.format(canvas.nrows)]
        argv += ['--ncols',         '{}'.format(canvas.ncols)]
        argv += ['--zax',           '{}'.format(canvas.zax)]
        argv += ['--zrange',        '{}'.format(canvas.zrange[0]),
                                    '{}'.format(canvas.zrange[1])]

        if canvas.showGridLines:
            argv += ['--showGridLines']

    for image in displayCtx.getOrderedImages():

        fname = image.imageFile

        # No support for in-memory images just yet.
        # 
        # TODO Popup a message telling the
        # user they must save images before
        # the screenshot can proceed
        if fname is None:
            continue

        display = displayCtx.getDisplayProperties(image)
        imgArgv = props.generateArguments(display)

        argv += ['--image', fname] + imgArgv

    argv = ' '.join(argv).split()
    argv = ['fslpy', 'render'] + argv

    log.debug('Generating screenshot with '
              'call to render: {}'.format(' '.join(argv)))

    print 'Generate this scene from the command ' \
          'line with: {}'.format(' '.join(argv))

    subprocess.call(argv)


class CanvasPanel(viewpanel.ViewPanel):
    """
    """


    showCursor     = props.Boolean(default=True)
    syncLocation   = displayctx.DisplayContext.getSyncProperty('location')
    syncImageOrder = displayctx.DisplayContext.getSyncProperty('imageOrder')
    syncVolume     = displayctx.DisplayContext.getSyncProperty('volume')

    zoom = props.Percentage(minval=10, maxval=1000, default=100, clamped=True)

    colourBarLocation  = props.Choice(
        ('top', 'bottom', 'left', 'right'),
        labels=[strings.choices['CanvasPanel.colourBarLocation.top'],
                strings.choices['CanvasPanel.colourBarLocation.bottom'],
                strings.choices['CanvasPanel.colourBarLocation.left'],
                strings.choices['CanvasPanel.colourBarLocation.right']])

    
    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide


    def __init__(self, parent, imageList, displayCtx, extraActions=None):

        if extraActions is None:
            extraActions = {}

        actionz = dict({
            'screenshot'              : self.screenshot,
            'toggleColourBar'         : self.toggleColourBar,
            'toggleImageList'         : lambda *a: self.togglePanel(
                imagelistpanel.ImageListPanel),
            'toggleAtlasPanel'        : lambda *a: self.togglePanel(
                atlaspanel.AtlasPanel),
            'toggleDisplayProperties' : lambda *a: self.togglePanel(
                imagedisplaytoolbar.ImageDisplayToolBar),
            'toggleLocationPanel'     : lambda *a: self.togglePanel(
                locationpanel.LocationPanel),
        }.items() + extraActions.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        # If the provided DisplayContext  does not
        # have a parent, this will raise an error.
        # But I don't think a CanvasPanel will ever
        # be created with a 'master' DisplayContext.
        self.bindProps('syncLocation',
                       displayCtx,
                       displayCtx.getSyncPropertyName('location'))
        self.bindProps('syncImageOrder',
                       displayCtx,
                       displayCtx.getSyncPropertyName('imageOrder'))
        self.bindProps('syncVolume',
                       displayCtx,
                       displayCtx.getSyncPropertyName('volume'))

        self.__canvasContainer = wx.Panel(self)
        self.__canvasPanel     = wx.Panel(self.__canvasContainer)

        self.setCentrePanel(self.__canvasContainer)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer   = None
        self.__colourBar     = None
        self.__showColourBar = False

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('colourBarLocation', lName, self.__layout)
        
        self.__layout()


    def destroy(self):
        """Makes sure that any remaining control panels are destroyed
        cleanly.
        """

        viewpanel.ViewPanel.destroy(self)

        if self.__colourBar is not None:
            self.__colourBar.destroy()


    def toggleColourBar(self, *a):
        self.__showColourBar = not self.__showColourBar
        self.__layout()

        
    def colourBarIsShown(self):
        return self.__showColourBar

    
    def screenshot(self, *a):
        _takeScreenShot(self._imageList, self._displayCtx, self)

        
    def getCanvasPanel(self):
        return self.__canvasPanel


    def __layout(self, *a):

        if not self.__showColourBar:

            if self.__colourBar is not None:
                self.unbindProps('colourBarLabelSide',
                                 self.__colourBar,
                                 'labelSide')
                self.__colourBar.destroy()
                self.__colourBar.Destroy()
                self.__colourBar = None
                
            self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.__canvasSizer.Add(self.__canvasPanel,
                                   flag=wx.EXPAND,
                                   proportion=1)

            self.__canvasContainer.SetSizer(self.__canvasSizer)
            self.PostSizeEvent()
            return

        if self.__colourBar is None:
            self.__colourBar = colourbarpanel.ColourBarPanel(
                self.__canvasContainer, self._imageList, self._displayCtx)

        self.bindProps('colourBarLabelSide', self.__colourBar, 'labelSide') 
            
        if   self.colourBarLocation in ('top', 'bottom'):
            self.__colourBar.orientation = 'horizontal'
        elif self.colourBarLocation in ('left', 'right'):
            self.__colourBar.orientation = 'vertical'
        
        if self.colourBarLocation in ('top', 'bottom'):
            self.__canvasSizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__canvasContainer.SetSizer(self.__canvasSizer)

        if self.colourBarLocation in ('top', 'left'):
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
        else:
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)

        # Force the canvas panel to resize itself
        self.PostSizeEvent()
