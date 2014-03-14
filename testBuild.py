#!/usr/bin/env python
#
# testBuild.py - Demonstration of the tkprop package.
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
    ('Run standard brain extraction using bet2'                             , ''),
    ('Robust brain centre estimation (iterates bet2 several times)'         , '-R'),
    ('Eye & optic nerve cleanup (can be useful in SIENA)'                   , '-S'),
    ('Bias field & neck cleanup (can be useful in SIENA)'                   , '-B'),
    ('Improve BET if FOV is very small in Z'                                , '-Z'),
    ('Apply to 4D FMRI data'                                                , '-F'),
    ('Run bet2 and then betsurf to get additional skull and scalp surfaces' , '-A'),
    ('As above, when also feeding in non-brain extracted T2'                , '-A2')))


class BetOptions(tkp.HasProperties):
    
    inputImage           = tkp.FilePath(exists=True)
    outputImage          = tkp.FilePath()
    t2Image              = tkp.FilePath(exists=True)
    
    runChoice            = tkp.Choice(choices=runChoices.keys())
    
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


def generateBetCmd(bopts):

    cmd = ['bet']

    if bopts.inputImage is None or bopts.inputImage == '':
        raise ValueError('Input image not specified')

    if bopts.outputImage is None or bopts.outputImage == '':
        raise ValueError('Output image not specified')

    if runChoices == '-A2' and \
       ((bopts.t2Image is None) or (bopts.t2Image == '')):
        raise ValueError('T2 image not specified') 

    cmd.append(bopts.inputImage)
    cmd.append(bopts.outputImage)

    runChoice = runChoices[bopts.runChoice]

    if runChoice != '':
        cmd.append(runChoice)

    if runChoice == '-A2':

        if bopts.t2Image is None or bopts.t2Image == '':
            raise ValueError('T2 image not specified')

        cmd.append(bopts.t2Image)        

    if not bopts.outputExtracted:      cmd.append('-n')
    if     bopts.outputMaskImage:      cmd.append('-m')
    if     bopts.outputSkull:          cmd.append('-s')
    if     bopts.outputSurfaceOverlay: cmd.append('-o')
    if     bopts.outputMesh:           cmd.append('-e')
    if     bopts.thresholdImages:      cmd.append('-t')

    cmd.append('-f')
    cmd.append('{}'.format(bopts.fractionalIntensity))

    cmd.append('-g')
    cmd.append('{}'.format(bopts.thresholdGradient))

    if bopts.headRadius > 0.0:
        cmd.append('-r')
        cmd.append('{}'.format(bopts.headRadius))

    if all((bopts.xCoordinate > 0.0,
            bopts.yCoordinate > 0.0,
            bopts.zCoordinate > 0.0)):
        cmd.append('-c')
        cmd.append('{}'.format(bopts.xCoordinate))
        cmd.append('{}'.format(bopts.yCoordinate))
        cmd.append('{}'.format(bopts.zCoordinate))

    return cmd
 
    
optNames = {
    'inputImage'           : 'Input image',
    'outputImage'          : 'Output image',
    'runChoice'            : 'Run options',
    't2Image'              : 'T2 image',
    'outputExtracted'      : 'Output brain-extracted image', 
    'outputMaskImage'      : 'Output binary brain mask image', 
    'thresholdImages'      : 'Apply thresholding to brain and mask image', 
    'outputSkull'          : 'Output exterior skull surface image',
    'outputMesh'           : 'Generate brain surface as mesh in .vtk format', 
    'outputSurfaceOverlay' : 'Output brain surface overlaid onto original image ',
    'fractionalIntensity'  : 'Fractional intensity threshold; smaller values give larger brain outline estimates',
    'thresholdGradient'    : 'Threshold gradient; positive values give larger brain outline at bottom, smaller at top',
    'headRadius'           : 'head radius (mm not voxels); initial surface sphere is set to half of this',
    'xCoordinate'          : 'X',
    'yCoordinate'          : 'Y',
    'zCoordinate'          : 'Z'
}

betView = tkp.NotebookGroup((
    tkp.VGroup(
        label='BET options',
        showLabels=True,
        children=(
            tkp.Widget('inputImage',          label=optNames['inputImage']),
            tkp.Widget('outputImage',         label=optNames['outputImage']),
            tkp.Widget('fractionalIntensity', label=optNames['fractionalIntensity']),
            tkp.Widget('runChoice',           label=optNames['runChoice']),
            tkp.Widget('t2Image',             label=optNames['t2Image'],
                       visibleWhen=lambda i: i.runChoice.startswith('As above'))
        )),
    tkp.VGroup(
        label='Advanced options',
        showLabels=True,
        children=(
            tkp.Widget('outputExtracted',      label=optNames['outputExtracted']),
            tkp.Widget('outputMaskImage',      label=optNames['outputMaskImage']),
            tkp.Widget('thresholdImages',      label=optNames['thresholdImages']),
            tkp.Widget('outputSkull',          label=optNames['outputSkull']),
            tkp.Widget('outputSurfaceOverlay', label=optNames['outputSurfaceOverlay']),
            tkp.Widget('outputMesh',           label=optNames['outputMesh']),
            tkp.Widget('thresholdGradient',    label=optNames['thresholdGradient']),
            tkp.Widget('headRadius',           label=optNames['headRadius']),
            tkp.HGroup(
                label='Coordinates (voxels) for centre of initial brain surface sphere',
                showLabels=True,
                children=(
                    tkp.Widget('xCoordinate', label=optNames['xCoordinate']),
                    tkp.Widget('yCoordinate', label=optNames['yCoordinate']),
                    tkp.Widget('zCoordinate', label=optNames['zCoordinate'])
                ))
        ))
))

class BetFrame(tk.Frame):
    
    def __init__(self, parent, betOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        self.tkpFrame = tkp.buildGUI(self, betOpts, betView)
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

    print('Command:')
    print(' '.join(generateBetCmd(betopts)))
