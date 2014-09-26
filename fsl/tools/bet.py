#!/usr/bin/env python
#
# bet.py - Front end to the FSL BET tool.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from collections import OrderedDict

import props

import fsl.data.imagefile           as imagefile
import fsl.data.image               as fslimage
import fsl.fslview.displaycontext   as displaycontext

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
    ('-A',  'Run bet2 and then betsurf to get additional skull and scalp '
            'surfaces'),
    ('-A2', 'As above, when also feeding in non-brain extracted T2')))


class Options(props.HasProperties):

    inputImage           = props.FilePath(
        exists=True,
        suffixes=imagefile._allowedExts,
        required=True)
    outputImage          = props.FilePath(required=True)
    t2Image              = props.FilePath(
        exists=True,
        suffixes=imagefile._allowedExts,
        required=lambda i: i.runChoice == '-A2')

    runChoice            = props.Choice(runChoices)

    outputExtracted      = props.Boolean(default=True)
    outputMaskImage      = props.Boolean(default=False)
    outputSkull          = props.Boolean(default=False)
    outputSurfaceOverlay = props.Boolean(default=False)
    outputMesh           = props.Boolean(default=False)
    thresholdImages      = props.Boolean(default=False)

    fractionalIntensity  = props.Real(default=0.5, minval=0.0,  maxval=1.0)
    thresholdGradient    = props.Real(default=0.0, minval=-1.0, maxval=1.0)
    headRadius           = props.Real(default=0.0, minval=0.0)
    xCoordinate          = props.Int(default=0, minval=0)
    yCoordinate          = props.Int(default=0, minval=0)
    zCoordinate          = props.Int(default=0, minval=0)


    def setOutputImage(self, value, valid, ctx):
        """
        When a (valid) input image file name is selected, the output
        image is set to the same name, with a suffix of '_brain'.
        """

        if not valid: return
        value = imagefile.removeExt(value)
        self.outputImage = value + '_brain'

        
    def clearT2Image(self, value, valid, ctx):
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

        self.addListener('inputImage', 'setOutputImage', self.setOutputImage)
        self.addListener('runChoice',  'clearT2Image',   self.clearT2Image)


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

        if any((self.xCoordinate > 0.0,
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
    'outputSurfaceOverlay' : 'Output brain surface overlaid onto original '
                             'image',
    'fractionalIntensity'  : 'Fractional intensity threshold',
    'thresholdGradient'    : 'Threshold gradient',
    'headRadius'           : 'Head radius (mm)',
    'centreCoords'         : 'Centre coordinates (voxels)',
    'xCoordinate'          : 'X',
    'yCoordinate'          : 'Y',
    'zCoordinate'          : 'Z'
}


optTooltips = {
    'fractionalIntensity' : 'Smaller values give larger brain outline '
                            'estimates.',
    'thresholdGradient'   : 'Positive values give larger brain outline at '
                            'bottom, smaller at top.',
    'headRadius'          : 'Initial surface sphere is set to half of this.',
    'centreCoords'        : 'Coordinates (voxels) for centre of initial '
                            'brain surface sphere.'
}


def selectHeadCentre(opts, button):
    """
    Pops up a little dialog window allowing the user to interactively
    select the head centre location.
    """
    import                                 wx
    import fsl.fslview.views.orthopanel as orthopanel

    image      = fslimage.Image(opts.inputImage)
    imageList  = fslimage.ImageList([image])
    displayCtx = displaycontext.DisplayContext(imageList)
    parent     = button.GetTopLevelParent()
    frame      = orthopanel.OrthoDialog(parent,
                                        imageList,
                                        displayCtx,
                                        opts.inputImage,
                                        style=wx.RESIZE_BORDER)
    panel      = frame.panel

    # Whenever the x/y/z coordinates change on
    # the ortho panel, update the option values.
    def updateOpts(*a):
        x, y, z = image.worldToVox([displayCtx.location])[0]

        if   x >= image.shape[0]: x = image.shape[0] - 1
        elif x <  0:              x = 0
        
        if   y >= image.shape[1]: y = image.shape[1] - 1
        elif y <  0:              y = 0
        
        if   z >= image.shape[2]: z = image.shape[2] - 1
        elif z <  0:              z = 0

        opts.xCoordinate = round(x)
        opts.yCoordinate = round(y)
        opts.zCoordinate = round(z)

    displayCtx.addListener('location', 'BETHeadCentre', updateOpts)

    # Set the initial location on the orthopanel.
    # TODO this ain't working, as it needs to be
    # done after the frame has been displayed, i.e
    # via wx.CallAfter or similar. 
    voxCoords   = [opts.xCoordinate, opts.yCoordinate, opts.zCoordinate]
    worldCoords = image.voxToWorld([voxCoords])[0]
    panel.pos   = worldCoords

    # Position the dialog by the button that was clicked
    pos = button.GetScreenPosition()
    frame.SetPosition(pos)
    frame.ShowModal()


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
                    props.Button(
                        text='Select',
                        callback=selectHeadCentre,
                        enabledWhen=lambda i: i.isValid('inputImage')),
                    'xCoordinate',
                    'yCoordinate',
                    'zCoordinate'))))))


def interface(parent, args, opts):
    
    import wx
    
    frame    = wx.Frame(parent)
    betPanel = props.buildGUI(
        frame, opts, betView, optLabels, optTooltips)

    frame.Layout()
    frame.Fit()

    return frame
    


def runBet(parent, opts):

    import fsl.utils.runwindow          as runwindow
    import fsl.fslview.views.orthopanel as orthopanel 

    def onFinish(window, exitCode):

        if exitCode != 0: return

        inImage   = fslimage.Image(opts.inputImage)
        outImage  = fslimage.Image(opts.outputImage)
        imageList = fslimage.ImageList([inImage, outImage])

        displayCtx = displaycontext.DisplayContext(imageList)

        outDisplay = outImage.getAttribute('display')

        outDisplay.cmap             = 'Reds'
        outDisplay.displayRange.xlo = 1
        outDisplay.clipLow          = True
        outDisplay.clipHigh         = True

        frame  = orthopanel.OrthoFrame(parent,
                                       imageList,
                                       displayCtx,
                                       title=opts.outputImage)
        frame.Show()
        
    runwindow.checkAndRun('BET', opts, parent, Options.genBetCmd,
                          optLabels=optLabels,
                          onFinish=onFinish,
                          modal=False)


FSL_TOOLNAME  = 'BET'
FSL_HELPPAGE  = 'bet'
FSL_CONTEXT   = lambda args: Options()
FSL_INTERFACE = interface
FSL_ACTIONS   = [('Run BET', runBet)]
