#!/usr/bin/env python
#
# fslview.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import wx

import fsl.fslview.orthopanel     as orthopanel
import fsl.fslview.imagelistpanel as imagelistpanel
import fsl.fslview.lightboxcanvas as lightboxcanvas

import fsl.data.fslimage as fslimage
import fsl.props         as props


class FslViewPanel(wx.Panel):

    def __init__(self, parent, imageList):
        
        wx.Panel.__init__(self, parent)
        self.imageList = imageList

        self.glContext = None

        self.ctrlPanel = None
        self.mainPanel = None
        self.listPanel = imagelistpanel.ImageListPanel(self, imageList)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)

        self.sizer.Add((1, 1), flag=wx.EXPAND)
        self.sizer.Add((1, 1), flag=wx.EXPAND, proportion=1)
        
        self.sizer.Add(self.listPanel, flag=wx.EXPAND)

        self.SetAutoLayout(1)

        # self.showOrtho()


    def _replace(self, mainPanel, ctrlPanel):

        self.sizer.Remove(0)
        self.sizer.Remove(0)

        self.sizer.Insert(0, ctrlPanel, flag=wx.EXPAND)
        self.sizer.Insert(1, mainPanel, flag=wx.EXPAND, proportion=1)

        if self.mainPanel is not None: self.mainPanel.Destroy()
        if self.ctrlPanel is not None: self.ctrlPanel.Destroy()

        self.mainPanel = mainPanel
        self.ctrlPanel = ctrlPanel
        
        self.Layout()


    def showOrtho(self):

        if isinstance(self.mainPanel, orthopanel.OrthoPanel):
            return

        mainPanel = orthopanel.OrthoPanel(self, self.imageList,
                                          glContext=self.glContext)
        
        ctrlPanel = props.buildGUI(self, mainPanel)

        if self.glContext is None:
            self.glContext = mainPanel.xcanvas.glContext

        self._replace(mainPanel, ctrlPanel)


    def showLightBox(self):

        if isinstance(self.mainPanel, lightboxcanvas.LightBoxPanel):
            return

        mainPanel = lightboxcanvas.LightBoxPanel(self, self.imageList,
                                                 glContext=self.glContext)
        
        ctrlPanel = props.buildGUI(self, mainPanel.canvas)

        if self.glContext is None:
            self.glContext = mainPanel.canvas.glContext 

        self._replace(mainPanel, ctrlPanel) 
        


def fslviewArguments(parser):
    parser.add_argument('image', help='Image file to view', nargs='*')


def loadImages(args):
    imageList = fslimage.ImageList(map(fslimage.Image, args.image))
    return imageList

    
def interface(parent, imageList):
    
    panel = FslViewPanel(parent, imageList)

    menubar  = parent.GetMenuBar()
    viewMenu = wx.Menu()
    menubar.Append(viewMenu, 'View')

    orthoAction    = viewMenu.Append(wx.ID_ANY, 'Ortho view')
    lightboxAction = viewMenu.Append(wx.ID_ANY, 'Lightbox view')

    parent.Bind(wx.EVT_MENU, lambda ev: panel.showOrtho(),    orthoAction)
    parent.Bind(wx.EVT_MENU, lambda ev: panel.showLightBox(), lightboxAction)
    
    return panel
    

FSL_TOOLNAME  = 'FSLView'
FSL_INTERFACE = interface
FSL_CONTEXT   = loadImages
FSL_ARGUMENTS = fslviewArguments
