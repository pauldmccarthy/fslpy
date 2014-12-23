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

Another class, the :class:`ControlStrip` is also defined in this module; it
contains a few buttons allowing the user to configure a :class:`CanvasPanel`
instance.
"""

import logging
log = logging.getLogger(__name__)

import subprocess

from collections import OrderedDict

import wx

import props

import fsl.fslview.panel                      as fslpanel 
import fsl.fslview.profiles                   as profiles
import fsl.fslview.actions.actionpanel        as actionpanel
import fsl.fslview.profiles.profilepanel      as profilepanel
import fsl.fslview.displaycontext             as displayctx
import fsl.fslview.controls.imagelistpanel    as imagelistpanel
import fsl.fslview.controls.imagedisplaypanel as imagedisplaypanel
import fsl.fslview.controls.locationpanel     as locationpanel
import                                           colourbarpanel


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

    width, height = canvas.GetClientSize().Get()

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

    if canvas.showColourBar:
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

        # No support for in-memory images just yet
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


class CanvasPanel(fslpanel.FSLViewPanel):
    """
    """


    showCursor     = props.Boolean(default=True)
    syncLocation   = displayctx.DisplayContext.getSyncProperty('location')
    syncImageOrder = displayctx.DisplayContext.getSyncProperty('imageOrder')
    syncVolume     = displayctx.DisplayContext.getSyncProperty('volume')

    profile = props.Choice(
        OrderedDict([('view', 'View'),
                     ('edit', 'Edit')]),
        default='view')

    zoom = props.Percentage(minval=10, maxval=1000, default=100, clamped=True)

    colourBarLocation = props.Choice({
        'top'    : 'Top',
        'bottom' : 'Bottom',
        'left'   : 'Left',
        'right'  : 'Right'})

    
    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide


    def __init__(self, parent, imageList, displayCtx):

        actionz = {
            'screenshot'              : self.screenshot,
            'toggleColourBar'         : self.toggleColourBar,
            'toggleImageList'         : self.toggleImageList,
            'toggleDisplayProperties' : self.toggleDisplayProperties,
            'toggleLocationPanel'     : self.toggleLocationPanel,
            'toggleCanvasProperties'  : self.toggleCanvasProperties}
        
        fslpanel.FSLViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        self.__profileManager = profiles.ProfileManager(
            self, imageList, displayCtx)
        
        self.bindProps('syncLocation',
                       displayCtx,
                       displayCtx.getSyncPropertyName('location'))
        self.bindProps('syncImageOrder',
                       displayCtx,
                       displayCtx.getSyncPropertyName('imageOrder'))
        self.bindProps('syncVolume',
                       displayCtx,
                       displayCtx.getSyncPropertyName('volume')) 

        self.__actionPanel      = actionpanel.ActionPanel(
            self, self, propz=[])
        self.__profilePanel     = wx.Panel(self)
        self.__canvasContainer  = wx.Panel(self)
        self.__listLocContainer = wx.Panel(self)
        self.__dispSetContainer = wx.Panel(self)

        self.__canvasPanel = wx.Panel(self.__canvasContainer)
 
        self.__imageListPanel = imagelistpanel.ImageListPanel(
            self.__listLocContainer, imageList, displayCtx)

        self.__locationPanel = locationpanel.LocationPanel(
            self.__listLocContainer, imageList, displayCtx) 
        
        self.__displayPropsPanel = imagedisplaypanel.ImageDisplayPanel(
            self.__dispSetContainer, imageList, displayCtx)
        
        self.__canvasPropsPanel = actionpanel.ActionPanel(
            self.__dispSetContainer, self, actionz=[])

        self.__listLocSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__listLocContainer.SetSizer(self.__listLocSizer)

        self.__listLocSizer.Add(self.__imageListPanel,
                                flag=wx.EXPAND,
                                proportion=0.5)
        self.__listLocSizer.Add(self.__locationPanel,
                                flag=wx.EXPAND,
                                proportion=1)

        self.__dispSetSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.__dispSetContainer.SetSizer(self.__dispSetSizer)

        self.__dispSetSizer.Add(self.__displayPropsPanel,
                                flag=wx.EXPAND,
                                proportion=1)
        self.__dispSetSizer.Add(self.__canvasPropsPanel,
                                flag=wx.EXPAND,
                                proportion=0.75)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer   = None
        self.__colourBar     = None
        self.__showColourBar = False

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)
        
        self.__sizer.Add(self.__actionPanel,       flag=wx.EXPAND)
        self.__sizer.Add(self.__profilePanel,      flag=wx.EXPAND)
        self.__sizer.Add(self.__listLocContainer,  flag=wx.EXPAND)
        self.__sizer.Add(self.__canvasContainer,   flag=wx.EXPAND,
                         proportion=1)
        self.__sizer.Add(self.__dispSetContainer,  flag=wx.EXPAND)

        self.__imageListPanel   .Show(False)
        self.__locationPanel    .Show(False)
        self.__canvasPropsPanel .Show(False)
        self.__displayPropsPanel.Show(False)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('colourBarLocation',     lName, self.__layout)
        self.addListener('profile',               lName, self.__profileChanged)
        
        self._init()
        self.__profileChanged()
        self.__layout()

            
    def _init(self):
        raise NotImplementedError('CanvasPanel._init must be '
                                  'provided by subclasses')


    def __profileChanged(self, *a):
        self.__profileManager.changeProfile(self.profile)

        if self.__profilePanel is not None:
            self.__profilePanel.DestroyChildren()

        realProfilePanel = profilepanel.ProfilePanel(
            self.__profilePanel, self.getCurrentProfile())

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer.Add(realProfilePanel)
        self.__profilePanel.SetSizer(sizer)

        self.__layout()


    def toggleImageList(self):
        self.__imageListPanel.Show(not self.__imageListPanel.IsShown())
        self.__layout()
        
    def toggleLocationPanel(self):
        self.__locationPanel.Show(not self.__locationPanel.IsShown())
        self.__layout()
        
    def toggleDisplayProperties(self):
        self.__displayPropsPanel.Show(not self.__displayPropsPanel.IsShown())
        self.__layout()
        
    def toggleCanvasProperties(self):
        self.__canvasPropsPanel .Show(not self.__canvasPropsPanel.IsShown())
        self.__layout()

    def toggleColourBar(self):
        self.__showColourBar = not self.__showColourBar
        self.__layout()

    def screenshot(self):
        _takeScreenShot(self._imageList, self._displayCtx, self)

        
    def getCanvasPanel(self):
        return self.__canvasPanel


    def getCurrentProfile(self):
        return self.__profileManager.getCurrentProfile()


    def __layout(self, *a):

        if not self.__showColourBar:

            if self.__colourBar is not None:
                self.unbindProps('colourBarLabelSide',
                                 self.__colourBar,
                                 'labelSide')
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
