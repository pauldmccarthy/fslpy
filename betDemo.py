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
import tkprop       as tkp

import runshell     as shell

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


class BetOptions(tkp.HasProperties):
    
    inputImage           = tkp.FilePath(exists=True, required=True)
    outputImage          = tkp.FilePath(             required=True)
    t2Image              = tkp.FilePath(exists=True, required=lambda i: i.runChoice == '-A2')
    
    runChoice            = tkp.Choice(runChoices)
    
    outputExtracted      = tkp.Boolean(default=True)
    outputMaskImage      = tkp.Boolean(default=False)
    outputSkull          = tkp.Boolean(default=False)
    outputSurfaceOverlay = tkp.Boolean(default=False)
    outputMesh           = tkp.Boolean(default=False)
    thresholdImages      = tkp.Boolean(default=False)
    
    fractionalIntensity  = tkp.Double(default=0,   minval=0.0,  maxval=1.0)
    thresholdGradient    = tkp.Double(default=0.5, minval=-1.0, maxval=1.0)
    headRadius           = tkp.Double(default=0.0, minval=0.0)
    xCoordinate          = tkp.Double(default=0.0, minval=0.0)
    yCoordinate          = tkp.Double(default=0.0, minval=0.0)
    zCoordinate          = tkp.Double(default=0.0, minval=0.0)


    def setOutputImage(self, value, valid, *a):
        """
        When a (valid) input image file name is selected, the output
        image is set to the same name, with a suffix of '_brain'.
        """

        if not valid: return
        self.outputImage = value + '_brain'


    def __init__(self):
        """
        Adds a few callback listeners for various bits of behaviour.
        """

        BetOptions.inputImage.addListener(
            self, 'setOutputImage', self.setOutputImage)


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


betView = tkp.NotebookGroup((
    tkp.VGroup(
        label='BET options',
        children=(
            'inputImage',
            'outputImage',
            'fractionalIntensity',
            'runChoice',
            tkp.Widget('t2Image', visibleWhen=lambda i: i.runChoice == '-A2')
        )),
    tkp.VGroup(
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
            tkp.HGroup(
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

    
class BetFrame(tk.Frame):
    
    def __init__(self, parent, betOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        buttons = OrderedDict((
            ('Run BET',  lambda : checkAndRun(betOpts, parent)),
            ('Cancel',   parent.destroy),
            ('Help',     openHelp)))

        self.tkpFrame = tkp.buildGUI(
            self, betOpts, betView, optLabels, optTooltips, buttons)
        
        self.tkpFrame.pack(fill=tk.BOTH, expand=1)


if __name__ == '__main__':

    import logging
    logging.basicConfig(format='%(levelname)s - %(funcName)s: %(message)s', level=logging.DEBUG)

    app     = tk.Tk()
    betopts = BetOptions()

    betopts.inputImage  = '/Users/paulmc/MNI152_T1_2mm.nii.gz'
    betopts.outputImage = '/Users/paulmc/brain'

    frame = BetFrame(app, betopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to '''\
              '''set frontmost of process "Python" to true' ''')

    def checkFslDir():
        fsldir = os.environ.get('FSLDIR', None)
        if fsldir is None:
            tkmsg.showwarning(
                'Warning',
                'The FSLDIR environment variable is not set - '\
                'you will not be able to run BET.')
            
    app.after_idle(checkFslDir)
    app.mainloop()
