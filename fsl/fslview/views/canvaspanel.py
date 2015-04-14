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

import wx

import fsl
import fsl.tools.fslview_parseargs              as fslview_parseargs
import fsl.data.imageio                         as iio
import fsl.data.strings                         as strings
import fsl.fslview.displaycontext               as displayctx
import fsl.fslview.displaycontext.orthoopts     as orthoopts
import fsl.fslview.controls.imagelistpanel      as imagelistpanel
import fsl.fslview.controls.imagedisplaytoolbar as imagedisplaytoolbar
import fsl.fslview.controls.locationpanel       as locationpanel
import fsl.fslview.controls.atlaspanel          as atlaspanel
import                                             colourbarpanel
import                                             viewpanel


log = logging.getLogger(__name__)


def _takeScreenShot(imageList, displayCtx, canvas):

    # Check to make sure that all images are saved
    # on disk, and ask the  user what they want to
    # do about the ones that aren't.
    for image in displayCtx.getOrderedImages():

        # If the image is not saved, popup a dialog
        # telling the user they must save the image
        # before the screenshot can proceed
        if not image.saved:
            title = strings.titles[  'CanvasPanel.screenshot.notSaved']
            msg   = strings.messages['CanvasPanel.screenshot.notSaved']
            msg   = msg.format(image.name)

            dlg = wx.MessageDialog(canvas,
                                   message=msg,
                                   caption=title,
                                   style=(wx.CENTRE |
                                          wx.YES_NO |
                                          wx.CANCEL |
                                          wx.ICON_QUESTION))
            dlg.SetYesNoCancelLabels(
                strings.labels['CanvasPanel.screenshot.notSaved.save'],
                strings.labels['CanvasPanel.screenshot.notSaved.skip'],
                strings.labels['CanvasPanel.screenshot.notSaved.cancel'])

            result = dlg.ShowModal()

            # The user chose to save the image
            if result == wx.ID_YES:
                iio.saveImage(image)

            # The user chose to skip the image
            elif result == wx.ID_NO:
                continue

            # the user clicked cancel, or closed the dialog
            else:
                return    

    # Ask the user where they want 
    # the screenshot to be saved
    dlg = wx.FileDialog(canvas,
                        message=strings.messages['CanvasPanel.screenshot'],
                        style=wx.FD_SAVE)

    if dlg.ShowModal() != wx.ID_OK:
        return

    filename = dlg.GetPath()

    # Make the dialog go away before
    # the screenshot gets taken
    dlg.Destroy()
    wx.Yield()

    # Screnshot size and scene options
    sceneOpts     = canvas.getSceneOptions()
    width, height = canvas.getCanvasPanel().GetClientSize().Get()

    # Generate command line arguments for
    # a callout to render.py - start with
    # the render.py specific options
    argv  = []
    argv += ['--outfile', filename]
    argv += ['--size', '{}'.format(width), '{}'.format(height)]
    argv += ['--background', '0', '0', '0', '255']

    # Add scene options
    argv += fslview_parseargs.generateSceneArgs(
        imageList, displayCtx, sceneOpts)

    # Add ortho specific options, if it's 
    # an orthopanel we're dealing with
    if isinstance(sceneOpts, orthoopts.OrthoOpts):

        xcanvas = canvas.getXCanvas()
        ycanvas = canvas.getYCanvas()
        zcanvas = canvas.getZCanvas()
        
        argv += ['--{}'.format(fslview_parseargs.ARGUMENTS[sceneOpts,
                                                           'xcentre'][1])]
        argv += ['{}'.format(c) for c in xcanvas.pos.xy]
        argv += ['--{}'.format(fslview_parseargs.ARGUMENTS[sceneOpts,
                                                           'ycentre'][1])]
        argv += ['{}'.format(c) for c in ycanvas.pos.xy]
        argv += ['--{}'.format(fslview_parseargs.ARGUMENTS[sceneOpts,
                                                           'zcentre'][1])]
        argv += ['{}'.format(c) for c in zcanvas.pos.xy]

    # Add display options for each image
    for image in displayCtx.getOrderedImages():

        display = displayCtx.getDisplayProperties(image)
        fname   = image.imageFile

        # Skip invisible/unsaved/in-memory images
        if not (display.enabled and image.saved):
            continue

        imgArgv = fslview_parseargs.generateImageArgs(image, displayCtx)
        argv   += [fname] + imgArgv

    log.debug('Generating screenshot with call '
              'to render: {}'.format(' '.join(argv)))

    # Run render.py to generate the screenshot
    msg     = strings.messages['CanvasPanel.screenshot.pleaseWait']
    busyDlg = wx.BusyInfo(msg, canvas)
    result  = fsl.runTool('render', argv)
    
    busyDlg.Destroy()

    if result != 0:
        title = strings.titles[  'CanvasPanel.screenshot.error']
        msg   = strings.messages['CanvasPanel.screenshot.error']
        msg   = msg.format(' '.join(['render'] + argv))
        wx.MessageBox(msg, title, wx.ICON_ERROR | wx.OK) 


class CanvasPanel(viewpanel.ViewPanel):
    """
    """

    syncLocation   = displayctx.DisplayContext.getSyncProperty('location')
    syncImageOrder = displayctx.DisplayContext.getSyncProperty('imageOrder')
    syncVolume     = displayctx.DisplayContext.getSyncProperty('volume')

    def __init__(self,
                 parent,
                 imageList,
                 displayCtx,
                 sceneOpts,
                 extraActions=None):

        if extraActions is None:
            extraActions = {}

        actionz = dict({
            'screenshot'              : self.screenshot,
            'toggleImageList'         : lambda *a: self.togglePanel(
                imagelistpanel.ImageListPanel),
            'toggleAtlasPanel'        : lambda *a: self.togglePanel(
                atlaspanel.AtlasPanel),
            'toggleDisplayProperties' : lambda *a: self.togglePanel(
                imagedisplaytoolbar.ImageDisplayToolBar, False, self),
            'toggleLocationPanel'     : lambda *a: self.togglePanel(
                locationpanel.LocationPanel),
        }.items() + extraActions.items())
        
        viewpanel.ViewPanel.__init__(
            self, parent, imageList, displayCtx, actionz)

        self.__opts = sceneOpts
        
        # Bind the sync* properties of this
        # CanvasPanel to the corresponding
        # properties on the DisplayContext
        # instance. 
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
            
        # If the displayCtx instance does not
        # have a parent, this means that it is
        # a top level instance
        else:
            self.disableProperty('syncLocation')
            self.disableProperty('syncImageOrder')
            self.disableProperty('syncVolume')

        self.__canvasContainer = wx.Panel(self)
        self.__canvasPanel     = wx.Panel(self.__canvasContainer)

        self.setCentrePanel(self.__canvasContainer)

        # Canvas/colour bar layout is managed in
        # the _layout/_toggleColourBar methods
        self.__canvasSizer   = None
        self.__colourBar     = None

        # Use a different listener name so that subclasses
        # can register on the same properties with self._name
        lName = 'CanvasPanel_{}'.format(self._name)
        self.__opts.addListener('colourBarLocation', lName, self.__layout)
        self.__opts.addListener('showColourBar',     lName, self.__layout)
        
        self.__layout()


    def getSceneOptions(self):
        return self.__opts


    def destroy(self):
        """Makes sure that any remaining control panels are destroyed
        cleanly.
        """

        viewpanel.ViewPanel.destroy(self)

        if self.__colourBar is not None:
            self.__colourBar.destroy()

    
    def screenshot(self, *a):
        _takeScreenShot(self._imageList, self._displayCtx, self)

        
    def getCanvasPanel(self):
        return self.__canvasPanel


    def __layout(self, *a):

        if not self.__opts.showColourBar:

            if self.__colourBar is not None:
                self.__opts.unbindProps('colourBarLabelSide',
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

        self.__opts.bindProps('colourBarLabelSide',
                              self.__colourBar,
                              'labelSide') 
            
        if   self.__opts.colourBarLocation in ('top', 'bottom'):
            self.__colourBar.orientation = 'horizontal'
        elif self.__opts.colourBarLocation in ('left', 'right'):
            self.__colourBar.orientation = 'vertical'
        
        if self.__opts.colourBarLocation in ('top', 'bottom'):
            self.__canvasSizer = wx.BoxSizer(wx.VERTICAL)
        else:
            self.__canvasSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.__canvasContainer.SetSizer(self.__canvasSizer)

        if self.__opts.colourBarLocation in ('top', 'left'):
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
        else:
            self.__canvasSizer.Add(self.__canvasPanel, flag=wx.EXPAND,
                                   proportion=1)
            self.__canvasSizer.Add(self.__colourBar,   flag=wx.EXPAND)

        # Force the canvas panel to resize itself
        self.PostSizeEvent()
