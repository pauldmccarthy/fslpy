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

import                   wx
import wx.lib.agw.aui as aui

import props

import fsl.data.strings                         as strings
import fsl.fslview.panel                        as fslpanel
import fsl.fslview.profiles                     as profiles
import fsl.fslview.displaycontext               as displayctx
import fsl.fslview.controls.imagelistpanel      as imagelistpanel
# import fsl.fslview.controls.imagedisplaypanel as imagedisplaypanel
import fsl.fslview.controls.imagedisplaytoolbar as imagedisplaytoolbar
import fsl.fslview.controls.locationpanel       as locationpanel
import fsl.fslview.controls.atlaspanel          as atlaspanel
import                                             colourbarpanel


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


class CanvasPanel(fslpanel.FSLViewPanel):
    """
    """


    showCursor     = props.Boolean(default=True)
    syncLocation   = displayctx.DisplayContext.getSyncProperty('location')
    syncImageOrder = displayctx.DisplayContext.getSyncProperty('imageOrder')
    syncVolume     = displayctx.DisplayContext.getSyncProperty('volume')

    profile = props.Choice()

    zoom = props.Percentage(minval=10, maxval=1000, default=100, clamped=True)

    colourBarLocation  = props.Choice(
        ('top', 'bottom', 'left', 'right'),
        labels=[strings.choices['CanvasPanel.colourBarLocation.top'],
                strings.choices['CanvasPanel.colourBarLocation.bottom'],
                strings.choices['CanvasPanel.colourBarLocation.left'],
                strings.choices['CanvasPanel.colourBarLocation.right']])

    
    colourBarLabelSide = colourbarpanel.ColourBarPanel.labelSide


    def __init__(self, parent, imageList, displayCtx):

        # TODO add 'show/hide profile (props/actions) panel' action
        actionz = {
            'screenshot'              : self.screenshot,
            'toggleColourBar'         : self.toggleColourBar,
            'toggleImageList'         : lambda *a: self.toggleControlPanel(
                imagelistpanel.ImageListPanel, *a),
            'toggleAtlasPanel'        : lambda *a: self.toggleControlPanel(
                atlaspanel.AtlasPanel, *a),
            'toggleDisplayProperties' : lambda *a: self.toggleControlPanel(
                imagedisplaytoolbar.ImageDisplayToolBar, *a),
            'toggleLocationPanel'     : lambda *a: self.toggleControlPanel(
                locationpanel.LocationPanel, *a),
            'toggleCanvasProperties'  : lambda  *a: self.toggleConfigPanel(
                type(self), self, *a)
        }
        
        fslpanel.FSLViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        self.__profileManager = profiles.ProfileManager(
            self, imageList, displayCtx)

        if displayCtx.getParent() is not None:
        
            self.bindProps('syncLocation',
                           displayCtx,
                           displayCtx.getSyncPropertyName('location'))
            self.bindProps('syncImageOrder',
                           displayCtx,
                           displayCtx.getSyncPropertyName('imageOrder'))
            self.bindProps('syncVolume',
                           displayCtx,
                           displayCtx.getSyncPropertyName('volume'))
        else:

            # Disable syncLocation, syncImageOrder, and syncVolume somehow
            pass


        self.__canvasContainer = wx.Panel(self)
        self.__canvasPanel     = wx.Panel(self.__canvasContainer)
        self.__controlPanels   = {}
        self.__configPanels    = {}

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer   = None
        self.__colourBar     = None
        self.__showColourBar = False

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = '{}_{}'.format(type(self).__name__, self._name)
        self.addListener('colourBarLocation', lName, self.__layout)
        self.addListener('profile',           lName, self.__profileChanged)
        
        imageList .addListener('images',
                               lName,
                               self.__selectedImageChanged)
        displayCtx.addListener('selectedImage',
                               lName,
                               self.__selectedImageChanged)
        
        self._init()
        self.__profileChanged()
        self.__selectedImageChanged()
        self.__layout()
        
        self.__auiMgr = aui.AuiManager(self, agwFlags=0) 
        self.__auiMgr.AddPane(self.__canvasContainer, wx.CENTRE)
        self.__auiMgr.Update()

        self.__auiMgr.Bind(aui.EVT_AUI_PANE_CLOSE, self.__onPaneClose)

            
    def _init(self):
        raise NotImplementedError('CanvasPanel._init must be '
                                  'provided by subclasses')


    def destroy(self):
        """Makes sure that any remaining control panels are destroyed
        cleanly.
        """

        fslpanel.FSLViewPanel.destroy(self)
        
        # Make sure that any control panels are correctly destroyed
        for panelType, panel in self.__controlPanels.items():
            panel.destroy()

        if self.__colourBar is not None:
            self.__colourBar.destroy()

        lName = '{}_{}'.format(type(self).__name__, self._name)
        self._imageList .removeListener('images',        lName)
        self._displayCtx.removeListener('selectedImage', lName)


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
            
    
    def __profileChanged(self, *a):

        self.__profileManager.changeProfile(self.profile)

        # TODO if a profile panel is being displayed,
        #      destroy it and create a new one
        
        profile = self.getCurrentProfile()

        # Profile mode changes may result in the 
        # content of the above prop/action panels 
        # changing. So we need to make sure that 
        # the canvas panel is sized appropriately.
        def modeChange(*a):
            self.__layout()
            
        profile.addListener('mode', self._name, modeChange)

        
    def __onPaneClose(self, ev=None, panel=None):

        if ev is not None:
            ev.Skip()
            panel = ev.GetPane().window

        log.debug('Panel closed: {}'.format(type(panel).__name__))

        if isinstance(panel, (fslpanel.FSLViewPanel,
                              fslpanel.FSLViewToolBar)):
            self.__controlPanels.pop(type(panel))

            # calling fslpanel.FSLViewPanel.destroy()
            # here -  wx.Destroy is done below
            panel.destroy()
            
        elif isinstance(panel, fslpanel.ConfigPanel):
            self.__configPanels.pop(panel.getTarget())

        # WTF AUI. Sometimes this method gets called
        # twice for a panel, the second time with a
        # reference to a wx._wxpyDeadObject; in such
        # situations, the Destroy method call below
        # will result in an exception being raised.
        else:
            return
        
        panel.Destroy()
 
        
    def toggleControlPanel(self, panelType, *a):
        
        window = self.__controlPanels.get(panelType, None)

        if window is not None:
            self.__auiMgr.DetachPane(window)
            self.__onPaneClose(None, window)
        else:
            window   = panelType(self, self._imageList, self._displayCtx)
            paneInfo = aui.AuiPaneInfo()        \
                .Top()                          \
                .MinSize(window.GetMinSize())   \
                .BestSize(window.GetBestSize()) \
                .Caption(strings.titles[window])

            if isinstance(window, fslpanel.FSLViewToolBar):
                paneInfo = paneInfo.ToolbarPane()
                    
            self.__auiMgr.AddPane(window, paneInfo)
            self.__controlPanels[panelType] = window
            
        self.__auiMgr.Update()
        

    def toggleConfigPanel(self, targetType, target, *a):
            
        import fsl.fslview.layouts as layouts
        
        window = self.__configPanels.get(targetType, None)

        if window is not None:
            
            self.__auiMgr.DetachPane(window)
            self.__onPaneClose(None, window)
        else:
            layout = layouts.layouts.get(targetType, None)
            window = fslpanel.ConfigPanel(self, target, layout=layout)

            self.__configPanels[target] = window
            self.__auiMgr.AddPane(window, wx.TOP)
            
        self.__auiMgr.Update()

        
    def toggleColourBar(self, *a):
        self.__showColourBar = not self.__showColourBar
        self.__layout()

        
    def colourBarIsShown(self):
        return self.__showColourBar

    
    def screenshot(self, *a):
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
