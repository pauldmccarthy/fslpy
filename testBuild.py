#!/usr/bin/env python
#
# testBuild.py -
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


optNames = {
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

view = tkp.NotebookGroup((
    tkp.VGroup(
        label='BET options',
        showLabels=True,
        children=(
            tkp.Widget('inputImage',          label=optNames['inputImage']),
            tkp.Widget('outputImage',         label=optNames['inputImage']),
            tkp.Widget('fractionalIntensity', label=optNames['fractionalIntensity']),
            tkp.Widget('runChoice',           label=optNames['runChoice']),
            tkp.Widget('t2Image',             label=optNames['t2Image'],
                       visibleWhen=('runChoice', lambda v: v.startswith('As above')))
        )),
    tkp.VGroup(
        label='Advanced options',
        showLabels=True,
        children=(
            tkp.Widget('outputExtracted'     , label=optNames['outputExtracted']),
            tkp.Widget('outputMaskImage'     , label=optNames['outputMaskImage']),
            tkp.Widget('thresholdImages'     , label=optNames['thresholdImages']),
            tkp.Widget('outputSkull'         , label=optNames['outputSkull']),
            tkp.Widget('outputSurfaceOverlay', label=optNames['outputSurfaceOverlay']),
            tkp.Widget('thresholdGradient'   , label=optNames['thresholdGradient']),
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


if __name__ == '__main__':

    app     = tk.Tk()
    betopts = BetOptions()

    frame = tkp.buildGUI(app, betopts, view)

    frame.pack(fill=tk.BOTH, expand=1)

    print('Before')
    print(betopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(betopts)
