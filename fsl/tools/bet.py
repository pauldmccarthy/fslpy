#!/usr/bin/env python
#
# bet.py - Front end to the FSL BET tool.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import sys

from collections import OrderedDict

import wx

import nibabel as nb

import fsl.props           as props
import fsl.data.imagefile  as imagefile
import fsl.utils.runwindow as runwindow
import fsl.utils.imageview as imageview

runChoices = OrderedDict((

    # This is a bit silly, but we can't use an empty
    # string as a key here, due to the way that props
    # handles empty strings.
    (' ',   'Run standard brain extraction using bet2'),
    ('-R',  'Robust brain centre estimation (iterates bet2 several times)'),
    ('-S',  'Eye & optic nerve cleanup (can be useful in SIENA)'),
    ('-B',  'Bias field & neck cleanup (can be useful in SIENA)'),
    ('-Z',  'Improve BET if FOV is very small in Z'),
    ('-F',  'Apply to 4D FMRI data'),
    ('-A',  'Run bet2 and then betsurf to get additional skull and scalp surfaces'),
    ('-A2', 'As above, when also feeding in non-brain extracted T2')))


class Options(props.HasProperties):

    inputImage           = props.FilePath(exists=True, suffixes=imagefile._allowedExts, required=True)
    outputImage          = props.FilePath(                                              required=True)
    t2Image              = props.FilePath(exists=True, suffixes=imagefile._allowedExts, required=lambda i: i.runChoice == '-A2')

    runChoice            = props.Choice(runChoices)

    outputExtracted      = props.Boolean(default=True)
    outputMaskImage      = props.Boolean(default=False)
    outputSkull          = props.Boolean(default=False)
    outputSurfaceOverlay = props.Boolean(default=False)
    outputMesh           = props.Boolean(default=False)
    thresholdImages      = props.Boolean(default=False)

    fractionalIntensity  = props.Double(default=0.5, minval=0.0,  maxval=1.0)
    thresholdGradient    = props.Double(default=0.0, minval=-1.0, maxval=1.0)
    headRadius           = props.Double(default=0.0, minval=0.0)
    xCoordinate          = props.Double(default=0.0, minval=0.0)
    yCoordinate          = props.Double(default=0.0, minval=0.0)
    zCoordinate          = props.Double(default=0.0, minval=0.0)


    def setOutputImage(self, value, valid, *a):
        """
        When a (valid) input image file name is selected, the output
        image is set to the same name, with a suffix of '_brain'.
        """

        if not valid: return
        value = imagefile.removeExt(value)
        self.outputImage = value + '_brain'

        
    def clearT2Image(self, value, *a):
        """
        This is a bit of a hack. If the user provides an invalid value
        for the T2 image (when running bet with the -A2 flag), but then
        changes their run choice to something other than -A2 (meaning
        that the invalid T2 image won't actually be used, so the fact
        that it is invalid doesn't really matter), props will still
        complain that the T2 image is invalid. So here, when the run
        choice is changed to something other than -A2, the T2 image is
        cleared, and props won't complain.
        """
        if value != '-A2': self.t2Image = None


    def __init__(self):
        """
        Adds a few callback listeners for various bits of behaviour.
        """

        Options.inputImage.addListener(
            self, 'setOutputImage', self.setOutputImage)
        Options.runChoice.addListener(
            self, 'clearT2Image',   self.clearT2Image)


    def genBetCmd(self):
        """
        Generates a command line call to the bet shell script, from
        the current option values.
        """

        errors = self.validateAll()

        if len(errors) > 0:
            raise ValueError('Options are not valid')

        cmd = ['bet']

        cmd.append(self.inputImage)
        cmd.append(self.outputImage)
        cmd.append('-v')

        runChoice = self.runChoice

        if runChoice.strip() != '':
            cmd.append(runChoice)

        if runChoice == '-A2':
            cmd.append(self.t2Image)

        if not self.outputExtracted:      cmd.append('-n')
        if     self.outputMaskImage:      cmd.append('-m')
        if     self.outputSkull:          cmd.append('-s')
        if     self.outputSurfaceOverlay: cmd.append('-o')
        if     self.outputMesh:           cmd.append('-e')
        if     self.thresholdImages:      cmd.append('-t')

        cmd.append('-f')
        cmd.append('{}'.format(self.fractionalIntensity))

        cmd.append('-g')
        cmd.append('{}'.format(self.thresholdGradient))

        if self.headRadius > 0.0:
            cmd.append('-r')
            cmd.append('{}'.format(self.headRadius))

        if all((self.xCoordinate > 0.0,
                self.yCoordinate > 0.0,
                self.zCoordinate > 0.0)):
            cmd.append('-c')
            cmd.append('{}'.format(self.xCoordinate))
            cmd.append('{}'.format(self.yCoordinate))
            cmd.append('{}'.format(self.zCoordinate))

        return cmd


optLabels = {
    'inputImage'           : 'Input image',
    'outputImage'          : 'Output image',
    'runChoice'            : 'Run options',
    't2Image'              : 'T2 image',
    'outputExtracted'      : 'Output brain-extracted image',
    'outputMaskImage'      : 'Output binary brain mask image',
    'thresholdImages'      : 'Apply thresholding to brain and mask image',
    'outputSkull'          : 'Output exterior skull surface image',
    'outputMesh'           : 'Generate brain surface as mesh in .vtk format',
    'outputSurfaceOverlay' : 'Output brain surface overlaid onto original image',
    'fractionalIntensity'  : 'Fractional intensity threshold',
    'thresholdGradient'    : 'Threshold gradient',
    'headRadius'           : 'Head radius (mm)',
    'centreCoords'         : 'Centre coordinates (voxels)',
    'xCoordinate'          : 'X',
    'yCoordinate'          : 'Y',
    'zCoordinate'          : 'Z'
}


optTooltips = {
    'fractionalIntensity' : 'Smaller values give larger brain outline estimates.',
    'thresholdGradient'   : 'Positive values give larger brain outline at bottom, smaller at top.',
    'headRadius'          : 'Initial surface sphere is set to half of this.',
    'centreCoords'        : 'Coordinates (voxels) for centre of initial brain surface sphere.'
}


def selectHeadCentre(opts, button):
    """
    Pops up a little dialog window allowing the user to interactively
    select the head centre location.
    """

    image  = nb.load(opts.inputImage)
    parent = button.GetTopLevelParent()
    frame  = imageview.ImageFrame(parent, image.get_data(), opts.inputImage)
    panel  = frame.panel

    panel.setLocation(
        opts.xCoordinate,
        opts.yCoordinate,
        opts.zCoordinate)

    # Whenever the x/y/z coordinates change on
    # the Options object,update the dialog view. 
    def updateViewX(val, *a): panel.setXLocation(val)
    def updateViewY(val, *a): panel.setYLocation(val)
    def updateViewZ(val, *a): panel.setZLocation(val)

    optListeners = (
        ('xCoordinate', 'updateViewX_{}'.format(id(panel)), updateViewX),
        ('yCoordinate', 'updateViewY_{}'.format(id(panel)), updateViewY),
        ('zCoordinate', 'updateViewZ_{}'.format(id(panel)), updateViewZ))

    for listener in optListeners:
        opts.addListener(*listener) 

    def rmListeners(ev):
        for listener in optListeners:
            prop = listener[0]
            name = listener[1]
            opts.removeListener(prop, name)

    # Remove the listeners when the dialog is closed
    frame.Bind(wx.EVT_WINDOW_DESTROY, rmListeners)

    # And whenever the x/y/z coordinates change
    # on the dialog, update the option values.
    def updateOpts(ev):
        opts.xCoordinate = ev.x
        opts.yCoordinate = ev.y
        opts.zCoordinate = ev.z

    panel.Bind(imageview.EVT_LOCATION_EVENT, updateOpts)

    # Position the dialog by the button that was clicked
    pos = button.GetScreenPosition()
    frame.SetPosition(pos)
    frame.Show()


betView = props.NotebookGroup((
    props.VGroup(
        label='BET options',
        children=(
            'inputImage',
            'outputImage',
            'fractionalIntensity',
            'runChoice',
            props.Widget('t2Image', visibleWhen=lambda i: i.runChoice == '-A2')
        )),
    props.VGroup(
        label='Advanced options',
        children=(
            'outputExtracted',
            'outputMaskImage',
            'thresholdImages',
            'outputSkull',
            'outputSurfaceOverlay',
            'outputMesh',
            'thresholdGradient',
            'headRadius',
            props.HGroup(
                key='centreCoords',
                children=(
                    props.Button(text='Select',
                                 callback=selectHeadCentre,
                                 enabledWhen=lambda i: i.isValid('inputImage')),
                    'xCoordinate',
                    'yCoordinate',
                    'zCoordinate'))))))


def interface(parent, opts):
    return props.buildGUI(
        parent, opts, betView, optLabels, optTooltips)

def runBet(parent, opts):

    def onFinish():
        image = nb.load(imagefile.addExt(opts.outputImage))
        frame = imageview.ImageFrame(parent,
                                     image.get_data(),
                                     title=opts.outputImage)
        frame.Show()
        
    runwindow.checkAndRun('BET', opts, parent, Options.genBetCmd,
                          optLabels=optLabels,
                          onFinish=onFinish)


FSL_TOOLNAME  = 'BET'
FSL_HELPPAGE  = 'bet'
FSL_OPTIONS   = Options
FSL_INTERFACE = interface
FSL_RUNTOOL   = runBet

