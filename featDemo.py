#!/usr/bin/env python
#
# featDemo.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys

import Tkinter as tk
import            ttk
import tkprop  as tkp


sliceTimingChoices = [
    'None',
    'Regular up (0, 1, 2, ..., n-1)',
    'Regular down (n-1, n-2, ..., 0',
    'Interleaved (0, 2, 4, ..., 1, 3, 5, ...)',
    'Use slice order file',
    'Use slice timings file'
]

# Currently only supports first-level analysis/full analysis
class FeatOptions(tkp.HasProperties):

    #
    # Misc options
    #

    # Have not yet implemented tooltip functionality. There
    # are numerous ways we could do so ...
    #
    # 1. We could think of a different way to provide help  (e.g.
    #    a '?' button next to every option which pops up a dialog).
    #
    # 2. Or we could have two optional parameters to the
    #    tkp.buildGUI function:
    #
    #   - a dict with property names as keys, and tooltip text
    #     as values
    #   - the name of a boolean property, on this HasProperties
    #     object, which controls whether tooltips are shown.
    #
    # 3. Or we could add a 'tooltip' attribute to build.ViewItem
    #    objects, passed in at the constructor. In addition to this
    #    the buildFromGUI function takes an optional parameter, the
    #    name of a boolean property which controls whether tooltips
    #    are enabled.
    #
    # I think I like the third option best.
    #
    balloonHelp              = tkp.Boolean(default=True)
    progressWatcher          = tkp.Boolean(default=True)
    brainBackgroundThreshold = tkp.Percentage(default=10)

    # Misc -> design efficiency options
    noiseLevel         = tkp.Percentage(default=0.66)
    temporalSmoothness = tkp.Double(default=0.34, minval=-1.0, maxval=1.0)
    zThreshold         = tkp.Double(default=5.3, minval=0.0)

    #
    # Data options
    #
    inputData            = tkp.List(minlen=1, listType=tkp.FilePath(exists=True))
    outputDirectory      = tkp.FilePath(isFile=False)
    totalVolumes         = tkp.Int(minval=0)
    deleteVolumes        = tkp.Int(minval=0)
    TR                   = tkp.Double(minval=0, default=3.0)
    highpassFilterCutoff = tkp.Int(minval=0, default=100)

    #
    # Pre-stats options
    #
    altReferenceImage = tkp.FilePath(exists=True)
    motionCorrection  = tkp.Choice(('MCFLIRT', 'None'))
    b0Unwarping       = tkp.Boolean(default=False)

    # B0 unwarping sub-options - displayed if b0Unwarping is true
    b0_fieldmap            = tkp.FilePath(exists=True)
    b0_fieldmapMag         = tkp.FilePath(exists=True)
    b0_echoSpacing         = tkp.Double(minval=0.0, default=0.7)
    b0_TE                  = tkp.Double(minval=0.0, default=35)
    b0_unwarpDir           = tkp.Choice(('-x','x','-y','y','-z','z'))
    b0_signalLossThreshold = tkp.Percentage(default=10)

    sliceTimingCorrection = tkp.Choice(sliceTimingChoices)

    # slice timing file, displayed if the timing correction
    # choice is for a custom order/timing file
    sliceTimingFile       = tkp.FilePath(exists=True)
    
    brainExtraction       = tkp.Boolean(default=True)
    smoothingFWHM         = tkp.Double(minval=0.0, default=5.0)
    intensityNorm         = tkp.Boolean(default=False)
    perfusionSubtraction  = tkp.Boolean(default=False)

    # displayed if perfusion subtraction is enabled
    perfusionOption       = tkp.Choice(('First timepoint is tag',
                                        'First timepoint is control'))
    
    temporalHighpass      = tkp.Boolean(default=True)
    melodic               = tkp.Boolean(default=False)

    #
    # Stats options
    #
    useFILMPrewhitening = tkp.Boolean(default=True)
    addMotionParameters = tkp.Choice(("Don't Add Motion Parameters",
                                      "Standard Motion Parameters",
                                      "Standard + Extended Motion Parameters"))
    
    voxelwiseConfoundList  = tkp.FilePath(exists=True)
    applyExternalScript    = tkp.FilePath(exists=True)
    addAdditionalConfounds = tkp.FilePath(exists=True)

    #
    # Post-stats options
    #
    preThresholdMask = tkp.FilePath(exists=True)
    thresholding     = tkp.Choice(('None','Uncorrected','Voxel','Cluster'))

    # Thresholding sub-options
    # displayed if thresholding is not None
    pThreshold  = tkp.Double(minval=0.0, maxval=1.0, default=0.05)
    zThreshold  = tkp.Double(minval=0.0, default=2.3)

    renderZMinMax = tkp.Choice(('Use actual Z min/max',
                                'Use preset Z min/max'))
    
    # displayed if renderZMinMax is 'preset'
    renderZMin    = tkp.Double(minval=0.0, default=2.0)
    renderZMax    = tkp.Double(minval=0.0, default=8.0)
    
    blobTypes     = tkp.Choice(('Solid blobs',
                                'Transparent blobs'))

    createTSPlots = tkp.Boolean(default=True)

    #
    # Post-stats options
    #
    expandedFunctionalImage = tkp.FilePath(exists=True)
    mainStructuralImage     = tkp.FilePath(exists=True)
    standardSpaceImage      = tkp.FilePath(exists=True)

    # only shown if functional image is not none
    functionalSearch = tkp.Choice(('No search',
                                   'Normal search',
                                   'Full search'))
    functionalDof    = tkp.Choice(('3 DOF',
                                   '6 DOF',
                                   '7 DOF',
                                   '9 DOF',
                                   '12 DOF'))

    # only shown if structural image is not none
    structuralSearch = tkp.Choice(('No search',
                                   'Normal search',
                                   'Full search'))
    structuralDof    = tkp.Choice(('3 DOF',
                                   '6 DOF',
                                   '7 DOF',
                                   'BBR',
                                   '12 DOF'))

    # only shown if standard image is not none
    standardSearch = tkp.Choice(('No search',
                                 'Normal search',
                                 'Full search'))
    standardDof    = tkp.Choice(('3 DOF',
                                 '6 DOF',
                                 '7 DOF',
                                 '9 DOF',
                                 '12 DOF'))
    nonlinearReg = tkp.Boolean(default=False)
    # only shown if nonlinear reg is selected
    warpResolution = tkp.Double(minval=0.0, default=10.0)


labels = {
    'balloonHelp'              : 'Balloon help',
    'progressWatcher'          : 'Progress watcher',
    'brainBackgroundThreshold' : 'Brain/background threshold',
    'noiseLevel'               : 'Noise level',
    'temporalSmoothness'       : 'Temporal smoothness',
    'zThreshold'               : 'Z threshold',
    'inputData'                : 'Select 4D data',
    'outputDirectory'          : 'Output directory',
    'totalVolumes'             : 'Total volumes',
    'deleteVolumes'            : 'Delete volumes',
    'TR'                       : 'TR (s)',
    'highpassFilterCutoff'     : 'High pass filter cutoff (s)',
    'altReferenceImage'        : 'Alternative reference image',
    'motionCorrection'         : 'Motion correction',
    'b0Unwarping'              : 'B0 Unwarping',
    'b0_fieldmap'              : 'Fieldmap',
    'b0_fieldmapMag'           : 'Fieldmap mag',
    'b0_echoSpacing'           : 'Effective EPI echos spacing (ms)',
    'b0_TE'                    : 'EPI TE (ms)',
    'b0_unwarpDir'             : 'Unwarp direction',
    'b0_signalLossThreshold'   : '% Signal loss threshold',
    'sliceTimingCorrection'    : 'Slice timing correction',
    'sliceTimingFile'          : 'Slice timing file',
    'brainExtraction'          : 'BET brain extraction',
    'smoothingFWHM'            : 'Spatial smoothing FWHM (mm)',
    'intensityNorm'            : 'Intensity normalization',
    'perfusion'                : 'Perfusion subtraction',
#    'pertfusionSubtraction'         : '',
#    'pertfusionOption'         : '',
    'temporalHighpass'         : 'Highpass',
    'melodic'                  : 'MELODIC ICA data exploration'
}

miscView = tkp.VGroup(
    label='Misc',
    children=(
        'balloonHelp',
        'progressWatcher',
        'brainBackgroundThreshold',
        tkp.VGroup(
            label='Design efficiency',
            border=True,
            children=(
                'noiseLevel',
                'temporalSmoothness',
                'zThreshold',
                tkp.Button(text='Estimate noise and smoothness'),
                tkp.Button(text='Estimate highpass filter')))))

dataView = tkp.VGroup(
    label='Data',
    children=(
        'inputData',
        'outputDirectory',
        'totalVolumes',
        'deleteVolumes',
        'TR',
        'highpassFilterCutoff'))

prestatsView = tkp.VGroup(
    label='Pre-stats',
    children=(
        'altReferenceImage',
        'motionCorrection',
        'b0Unwarping',
        tkp.VGroup(
            label='B0 Unwarping options',
            border=True,
            visibleWhen=lambda i: i.b0Unwarping,
            children=(
                'b0_fieldmap',
                'b0_fieldmapMag',
                'b0_echoSpacing',
                'b0_TE',
                'b0_unwarpDir',
                'b0_signalLossThreshold')),
        'sliceTimingCorrection',
        tkp.Widget('sliceTimingFile',
                   visibleWhen=lambda i: i.sliceTimingCorrection.startswith('Use')),
        'brainExtraction',
        'smoothingFWHM',
        'intensityNorm',
        tkp.HGroup(
            showLabels=False,
            key='perfusion',
            children=(
                'perfusionSubtraction',
                tkp.Widget('perfusionOption',
                           visibleWhen=lambda i: i.perfusionSubtraction))),
        'temporalHighpass',
        'melodic'))

featView = tkp.NotebookGroup((
    miscView,
    dataView,
    prestatsView))

    

class FeatFrame(tk.Frame):
    
    def __init__(self, parent, featOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        self.tkpFrame = tkp.buildGUI(self, featOpts, featView, labels)
        self.tkpFrame.pack(fill=tk.BOTH, expand=1)

        self.buttonFrame = tk.Frame(self)
        self.runButton   = ttk.Button(self.buttonFrame,
                                      text='Run FEAT',
                                      command=parent.destroy)
        self.quitButton  = ttk.Button(self.buttonFrame,
                                      text='Quit',
                                      command=parent.destroy)

        self.runButton  .pack(fill=tk.X, expand=1, side=tk.LEFT) 
        self.quitButton .pack(fill=tk.X, expand=1, side=tk.RIGHT)
        self.buttonFrame.pack(fill=tk.X) 


if __name__ == '__main__':

    app  = tk.Tk()
    fopts = FeatOptions()

    frame = FeatFrame(app, fopts)

    print('Before')
    print(fopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(fopts)
