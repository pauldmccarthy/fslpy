#!/usr/bin/env python
#
# betDemo.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import sys

from collections import OrderedDict

import Tkinter as tk
import            ttk
import tkprop  as tkp

runChoices = OrderedDict((
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
    
    fractionalIntensity  = tkp.Double(default=0,   minval=0.0, maxval=1.0)
    thresholdGradient    = tkp.Double(default=0.5, minval=0.0, maxval=1.0)
    headRadius           = tkp.Double(default=0.0, minval=0.0)
    xCoordinate          = tkp.Double(default=0.0, minval=0.0)
    yCoordinate          = tkp.Double(default=0.0, minval=0.0)
    zCoordinate          = tkp.Double(default=0.0, minval=0.0)


    def setOutputImage(self, value, valid, *a):
        """
        When a (valid) input image file name is selected, the output
        image is set to the same, name, with a suffix of '_brain'.
        """

        if not valid: return
        self.outputImage = value + '_brain'


    def __init__(self):
        """
        """

        BetOptions.inputImage.addListener(
            self, 'setOutputImage', self.setOutputImage)


    def genBetCmd(self):
        
        cmd = ['bet']

        if self.inputImage is None or self.inputImage == '':
            raise ValueError('Input image not specified')

        if self.outputImage is None or self.outputImage == '':
            raise ValueError('Output image not specified')

        if runChoices == '-A2' and \
           ((self.t2Image is None) or (self.t2Image == '')):
            raise ValueError('T2 image not specified') 

        cmd.append(self.inputImage)
        cmd.append(self.outputImage)

        runChoice = runChoices[self.runChoice]

        if runChoice != '':
            cmd.append(runChoice)

        if runChoice == '-A2':

            if self.t2Image is None or self.t2Image == '':
                raise ValueError('T2 image not specified')

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


class BetFrame(tk.Frame):
    
    def __init__(self, parent, betOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        self.tkpFrame = tkp.buildGUI(self, betOpts, betView, optLabels, optTooltips)
        self.tkpFrame.pack(fill=tk.BOTH, expand=1)

        self.buttonFrame = tk.Frame(self)
        self.runButton   = ttk.Button(self.buttonFrame,
                                      text='Run BET',
                                      command=parent.destroy)
        self.quitButton  = ttk.Button(self.buttonFrame,
                                      text='Quit',
                                      command=parent.destroy)

        self.runButton  .pack(fill=tk.X, expand=1, side=tk.LEFT) 
        self.quitButton .pack(fill=tk.X, expand=1, side=tk.RIGHT)
        self.buttonFrame.pack(fill=tk.X) 


if __name__ == '__main__':

    app     = tk.Tk()
    betopts = BetOptions()

    frame = BetFrame(app, betopts)

    print('Before')
    print(betopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(betopts)

    errors = betopts.validateAll()
    if len(errors)  == 0:
        print('Command:')
        print(' '.join(betopts.genBetCmd()))
    else:
        print('Errors:')
        print('  ' + '\n  '.join(errors))
