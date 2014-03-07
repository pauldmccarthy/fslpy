#!/usr/bin/env python
#
# test.py -
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
    fractionalIntensity  = tkp.Double(default=0, minval=0.0, maxval=1.0)
    runChoice            = tkp.Choice(choices=runChoices.keys())
    t2Image              = tkp.FilePath(exists=True)
    outputExtracted      = tkp.Boolean(default=True)
    outputMaskImage      = tkp.Boolean(default=False)
    thresholdImages      = tkp.Boolean(default=False)
    outputSkull          = tkp.Boolean(default=False)
    outputSurfaceOverlay = tkp.Boolean(default=False)
    thresholdGradient    = tkp.Double(default=0.5, minval=0.0, maxval=1.0)
    xCoordinate          = tkp.Double(default=0.0, minval=0.0)
    yCoordinate          = tkp.Double(default=0.0, minval=0.0)
    zCoordinate          = tkp.Double(default=0.0, minval=0.0)

    def __str__(self):

        s = 'BetOptions\n'
        s = s + '  inputImage           = {}'.format(self.inputImage)           + '\n'
        s = s + '  outputImage          = {}'.format(self.outputImage)          + '\n'
        s = s + '  t2Image              = {}'.format(self.t2Image)              + '\n'
        s = s + '  fractionalIntensity  = {}'.format(self.fractionalIntensity)  + '\n'
        s = s + '  runChoice            = {}'.format(self.runChoice)            + '\n'
        s = s + '  outputExtracted      = {}'.format(self.outputExtracted)      + '\n'
        s = s + '  outputMaskImage      = {}'.format(self.outputMaskImage)      + '\n'
        s = s + '  thresholdImages      = {}'.format(self.thresholdImages)      + '\n'
        s = s + '  outputSkull          = {}'.format(self.outputSkull)          + '\n'
        s = s + '  outputSurfaceOverlay = {}'.format(self.outputSurfaceOverlay) + '\n'
        s = s + '  thresholdGradient    = {}'.format(self.thresholdGradient)    + '\n'
        s = s + '  xCoordinate          = {}'.format(self.xCoordinate)          + '\n'
        s = s + '  yCoordinate          = {}'.format(self.yCoordinate)          + '\n'
        s = s + '  zCoordinate          = {}'.format(self.zCoordinate)          + '\n'
        
        return s


optionNames = {
    'inputImage'           : 'Input image',
    'outputImage'          : 'Output image',
    'fractionalIntensity'  : 'Fractional intensity threshold; smaller values give larger brain outline estimates',
    'runChoice'            : 'Run options',
    't2Image'              : 'T2 image',
    'outputExtracted'      : 'Output brain-extracted image',                                                           
    'outputMaskImage'      : 'Output binary brain mask image',                                                         
    'thresholdImages'      : 'Apply thresholding to brain and mask image',                                             
    'outputSkull'          : 'Output exterior skull surface image',                                                    
    'outputSurfaceOverlay' : 'Output brain surface overlaid onto original image ',                                     
    'thresholdGradient'    : 'Threshold gradient; positive values give larger brain outline at bottom, smaller at top',
    'xCoordinate'          : 'X',
    'yCoordinate'          : 'Y',
    'zCoordinate'          : 'Z'
}


class BetFrame(tk.Frame):

    def __init__(self, parent, betopts):
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)
        
        self.betopts = betopts

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=1)

        self.stdOptFrame = tk.Frame(self.notebook)
        self.advOptFrame = tk.Frame(self.notebook)

        self.stdOptFrame.pack(fill=tk.BOTH, expand=1)
        self.advOptFrame.pack(fill=tk.BOTH, expand=1)

        self.stdOptFrame.columnconfigure(1, weight=1)
        self.advOptFrame.columnconfigure(1, weight=1)

        self.notebook.add(self.stdOptFrame, text='BET options')
        self.notebook.add(self.advOptFrame, text='Advanced options')

        for idx,option in enumerate(['inputImage',
                                     'outputImage',
                                     'fractionalIntensity',
                                     'runChoice',
                                     't2Image']):

            label  = ttk.Label(     self.stdOptFrame, text=optionNames[option])
            widget = tkp.makeWidget(self.stdOptFrame, self.betopts, option)

            label .grid(row=idx, column=0, sticky=tk.N+tk.E+tk.S+tk.W)
            widget.grid(row=idx, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

            self.stdOptFrame.rowconfigure(idx, weight=1)

            setattr(self, '{}Widget'.format(option), widget)
            setattr(self, '{}Label' .format(option), label)

        for idx,option in enumerate(['outputExtracted',
                                     'outputMaskImage',
                                     'thresholdImages',
                                     'outputSkull',
                                     'outputSurfaceOverlay',
                                     'thresholdGradient',
                                     'xCoordinate',
                                     'yCoordinate',
                                     'zCoordinate']):
            
            label  = ttk.Label(     self.advOptFrame, text=optionNames[option])
            widget = tkp.makeWidget(self.advOptFrame, self.betopts, option)

            label .grid(row=idx, column=0, sticky=tk.N+tk.E+tk.S+tk.W)
            widget.grid(row=idx, column=1, sticky=tk.N+tk.E+tk.S+tk.W)

            setattr(self, '{}Widget'.format(option), widget)
            setattr(self, '{}Label' .format(option), label)

            self.advOptFrame.rowconfigure(idx, weight=1)


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
    frame   = BetFrame(app, betopts)

    print('Before')
    print(betopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(betopts)
