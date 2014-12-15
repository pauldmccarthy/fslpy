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

import fsl.fslview.profiles                    as profiles
import fsl.fslview.controlpanel                as controlpanel 
import fsl.fslview.displaycontext              as displayctx
import fsl.fslview.viewpanel                   as viewpanel
import fsl.fslview.controls.imagelistpanel     as imagelistpanel
import fsl.fslview.controls.imagedisplaypanel  as imagedisplaypanel
import fsl.fslview.controls.locationpanel      as locationpanel
import                                            colourbarpanel


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

    # TODO In-memory-only images will not be
    # rendered - will need to save them to a temp file

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


class ControlStrip(controlpanel.ControlPanel):
    """
    """

    def __init__(self, parent, imageList, displayCtx, canvasPanel):
        controlpanel.ControlPanel.__init__(self, parent, imageList, displayCtx)

        self._imageListButton    = wx.Button(self, label='Image list')
        self._displayPropsButton = wx.Button(self, label='Image display')
        self._locationButton     = wx.Button(self, label='Location')
        self._settingsButton     = wx.Button(self, label='Display settings')
        self._screenShotButton   = wx.Button(self, label='Screen shot')
        self._profileBox         = props.makeWidget(self,
                                                    canvasPanel,
                                                    'profile')
        
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._sizer.Add(self._imageListButton)
        self._sizer.Add(self._displayPropsButton)
        self._sizer.Add(self._locationButton)
        self._sizer.Add(self._settingsButton)
        self._sizer.Add(self._screenShotButton)
        self._sizer.Add(self._profileBox)

        self.SetSizer(self._sizer)
        self.Layout()

        def toggleImageList(ev):
            canvasPanel.showImageList = not canvasPanel.showImageList
        def toggleDisplayProps(ev):
            canvasPanel.showImageDisplayPanel = \
                not canvasPanel.showImageDisplayPanel
        def toggleLocation(ev):
            canvasPanel.showLocationPanel = not canvasPanel.showLocationPanel
        def toggleSettings(ev):
            canvasPanel.showSettingsPanel = not canvasPanel.showSettingsPanel
        def screenShot(ev):
            _takeScreenShot(imageList, displayCtx, canvasPanel)

        def profileChanged(*a):
            self._profileModeBox = props.makeWidget(
                self,
                canvasPanel.getCurrentProfile(),
                'mode')
            self._sizer.Add(self._profileModeBox)
            self.Layout()

        canvasPanel.addListener('profile', self._name, profileChanged)
        profileChanged()

        self._imageListButton   .Bind(wx.EVT_BUTTON, toggleImageList)
        self._displayPropsButton.Bind(wx.EVT_BUTTON, toggleDisplayProps)
        self._locationButton    .Bind(wx.EVT_BUTTON, toggleLocation)
        self._settingsButton    .Bind(wx.EVT_BUTTON, toggleSettings)
        self._screenShotButton  .Bind(wx.EVT_BUTTON, screenShot)
            

class CanvasPanel(viewpanel.ViewPanel):
    """
    """

    showCursor = props.Boolean(default=True)

    showColourBar         = props.Boolean(default=False)
    showImageList         = props.Boolean(default=False)
    showLocationPanel     = props.Boolean(default=False)
    showImageDisplayPanel = props.Boolean(default=False)
    showSettingsPanel     = props.Boolean(default=False)

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

    
    _labels = {
        'showCursor'             : 'Show cursor',
        'showColourBar'          : 'Show/hide colour bar',
        'showImageList'          : 'Show/hide image list',
        'showLocationPanel'      : 'Show/hide location panel',
        'showImageDisplayPanel'  : 'Show/hide image display panel',
        'showSettingsPanel'      : 'Show/hide canvas settings',
        'syncLocation'           : 'Synchronise location',
        'syncImageOrder'         : 'Synchronise image order',
        'syncVolume'             : 'Synchronise volume number',
        'colourBarLocation'      : 'Colour bar location',
        'colourBarLabelSide'     : 'Colour bar label side',
        'profile'                : 'Profile'
    }


    def __createSettingsPanel(self, parent, imageList, displayCtx):
        """
        """

        return props.buildGUI(self.__dispSetContainer, self)


    def __init__(self,
                 parent,
                 imageList,
                 displayCtx):
        viewpanel.ViewPanel.__init__(self, parent, imageList, displayCtx)

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

        self.__canvasContainer  = wx.Panel(self)
        self.__listLocContainer = wx.Panel(self)
        self.__dispSetContainer = wx.Panel(self)

        self.__canvasPanel = wx.Panel(self.__canvasContainer)
 
        self.__imageListPanel = imagelistpanel.ImageListPanel(
            self.__listLocContainer, imageList, displayCtx)

        self.__locationPanel = locationpanel.LocationPanel(
            self.__listLocContainer, imageList, displayCtx) 
        
        self.__imageDisplayPanel = imagedisplaypanel.ImageDisplayPanel(
            self.__dispSetContainer, imageList, displayCtx)
        
        self.__settingsPanel = self.__createSettingsPanel(
            self.__dispSetContainer, imageList, displayCtx)

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

        self.__dispSetSizer.Add(self.__imageDisplayPanel,
                                flag=wx.EXPAND,
                                proportion=1)
        self.__dispSetSizer.Add(self.__settingsPanel,
                                flag=wx.EXPAND,
                                proportion=0.75)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer = None
        self.__colourBar   = None

        self.__sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.__sizer)
        self.__sizer.Add(self.__listLocContainer,  flag=wx.EXPAND)
        self.__sizer.Add(self.__canvasContainer,   flag=wx.EXPAND,
                         proportion=1)
        self.__sizer.Add(self.__dispSetContainer,  flag=wx.EXPAND)

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.addListener('showColourBar',         lName, self.__layout)
        self.addListener('colourBarLocation',     lName, self.__layout)
        self.addListener('showImageList',         lName, self.__layout)
        self.addListener('showLocationPanel',     lName, self.__layout)
        self.addListener('showImageDisplayPanel', lName, self.__layout)
        self.addListener('showSettingsPanel',     lName, self.__layout)
        self.addListener('profile',               lName, self.__profileChanged)
        
        self.__layout()
        self._init()
        self.__profileChanged()

        # Create the ControlStrip last, as it needs to access
        # the Profile instance of this canvas panel, which is
        # not created until _profileChanged is called above.
        # _profileChanged must be called after self._init, as
        # the profile logic may depend upon CanvasPanel
        # subclass-specific attributes (e.g. xcanvas/ycanvas/
        # zcanvas for the OrthoPanel). 
        #
        # And I think (but I can't remember why exactly) that
        # self._init needs to be called after self.__layout.
        # and self.__layout can only be called after all the
        # stuff contained in this panel has been created.
        self.__controlPanel = ControlStrip(
            self, imageList, displayCtx, self)
        self.__sizer.Insert(0, self.__controlPanel, flag=wx.EXPAND)


    def _init(self):
        raise NotImplementedError('CanvasPanel._init must be '
                                  'provided by subclasses')


    def __profileChanged(self, *a):
        self.__profileManager.changeProfile(self.profile)

        
    def getCanvasPanel(self):
        return self.__canvasPanel


    def getCurrentProfile(self):
        return self.__profileManager.getCurrentProfile()

    
    def __layout(self, *a):

        self.__toggleColourBar()

        if self.showImageList:         self.__imageListPanel   .Show(True)
        else:                          self.__imageListPanel   .Show(False)
        if self.showLocationPanel:     self.__locationPanel    .Show(True)
        else:                          self.__locationPanel    .Show(False)
        if self.showImageDisplayPanel: self.__imageDisplayPanel.Show(True)
        else:                          self.__imageDisplayPanel.Show(False)
        if self.showSettingsPanel:     self.__settingsPanel    .Show(True)
        else:                          self.__settingsPanel    .Show(False) 

        self.PostSizeEvent()


    def __toggleColourBar(self):

        if not self.showColourBar:

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
