#!/usr/bin/env python
#
# betDemo.py - Replicating FSL's bet gui in Tkinter using tkprop.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import sys

from collections import OrderedDict

import Tkinter      as tk
import tkMessageBox as tkmsg
import                 ttk

import fsl.props          as props
import fsl.utils.runshell as shell

runChoices = OrderedDict((

    # This is a bit silly, but we can't use an empty
    # string as a key here, due to the way that tkprop
    # and Tkinter handle empty strings.
    (' ',   'Run standard brain extraction using bet2'),
    ('-R',  'Robust brain centre estimation (iterates bet2 several times)'),
    ('-S',  'Eye & optic nerve cleanup (can be useful in SIENA)'),
    ('-B',  'Bias field & neck cleanup (can be useful in SIENA)'),
    ('-Z',  'Improve BET if FOV is very small in Z'),
    ('-F',  'Apply to 4D FMRI data'),
    ('-A',  'Run bet2 and then betsurf to get additional skull and scalp surfaces'),
    ('-A2', 'As above, when also feeding in non-brain extracted T2')))

filetypes = ['.nii.gz', '.nii', '.hdr', '.img']

class Options(props.HasProperties):
    
    inputImage           = props.FilePath(exists=True, suffixes=filetypes, required=True)
    outputImage          = props.FilePath(                                 required=True)
    t2Image              = props.FilePath(exists=True, suffixes=filetypes, required=lambda i: i.runChoice == '-A2')
    
    runChoice            = props.Choice(runChoices)
    
    outputExtracted      = props.Boolean(default=True)
    outputMaskImage      = props.Boolean(default=False)
    outputSkull          = props.Boolean(default=False)
    outputSurfaceOverlay = props.Boolean(default=False)
    outputMesh           = props.Boolean(default=False)
    thresholdImages      = props.Boolean(default=False)
    
    fractionalIntensity  = props.Double(default=0,   minval=0.0,  maxval=1.0)
    thresholdGradient    = props.Double(default=0.5, minval=-1.0, maxval=1.0)
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
                    'xCoordinate',
                    'yCoordinate',
                    'zCoordinate'))
        ))
))


def checkAndRun(betOpts, tkRoot):
    """
    Checks that the given options are valid. If they are, bet is run.
    If the options are not valid, some complaints are directed towards
    the user.
    """

    errors = betOpts.validateAll()
    if len(errors) > 0:

        msg = 'There are numerous errors which need '\
              'to be fixed before BET can be run:\n'

        for name,error in errors:
            msg = msg + '\n - {}: {}'.format(optLabels[name], error)

        tkmsg.showwarning('Error', msg)
        
    else:
        cmd = betOpts.genBetCmd()
        shell.run(cmd, tkRoot)


def openHelp():
    """
    Opens BET help in a web browser.
    """

    fsldir = os.environ.get('FSLDIR', None)
    url    = 'file://{}/doc/redirects/bet.html'.format(fsldir)

    if fsldir is not None:
        import webbrowser
        webbrowser.open(url)
    else:
        tkmsg.showerror(
            'Error',
            'The FSLDIR environment variable is not set - I don\'t '\
            'know where to find the FSL documentation.') 

    
class Frame(tk.Frame):
    
    def __init__(self, parent, betOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        buttons = OrderedDict((
            ('Run BET',  lambda : checkAndRun(betOpts, parent)),
            ('Quit',     parent.destroy),
            ('Help',     openHelp)))

        self.propFrame = props.buildGUI(
            self, betOpts, betView, optLabels, optTooltips, buttons)
        
        self.propFrame.pack(fill=tk.BOTH, expand=1)
