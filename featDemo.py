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
    'noiseLevelEstimate'       : 'Estimate from data',
    'highpassEstimate'         : 'Estimate High Pass Filter',
    'zThreshold'               : 'Z threshold',
    'inputData'                : 'Select 4D data',
    'outputDirectory'          : 'Output directory',
    'totalVolumes'             : 'Total volumes',
    'deleteVolumes'            : 'Delete volumes',
    'TR'                       : 'TR (s)',
    'highpassFilterCutoff'     : 'Hgih pass filter cutoff (s)'
}

tooltips = {
    'balloonHelp'              : "And don't expect this message to appear whilst you've turned this option off!",
    'progressWatcher'          : 'Start a web browser to watch the analysis progress?',
    'brainBackgroundThreshold' : 'This is automatically calculated, as a % of the maximum input image intensity. It is used in intensity normalisation, brain mask generation and various other places in the analysis.',
    'noiseLevel'               : 'The "Noise level %" and "Temporal smoothness" together characterise the noise in the data, to be used only in the design efficiency estimation.\n\nThe "Noise level %" is the standard deviation (over time) for a typical voxel, expressed as a percentage of the baseline signal level.\n\nThe "Temporal smoothness" is the smoothness coefficient in a simple AR(1) autocorrelation model (much simpler than that actually used in the FILM timeseries analysis but good enough for the efficiency calculation here).\n\nIf you want to get a rough estimate of this noise level and smoothness from your actual input data, press the "Estimate from data" button (after you have told FEAT where your input data is). This takes about 30-60 seconds to estimate. This applies just the spatial and temporal filtering (i.e., no motion correction) that you have specified in the "Pre-stats" section, and gives a reasonable approximation of the noise characteristics that will remain in the fully preprocessed data, once FEAT has run.',
    'zThreshold'               : 'This is the Z value used to determine what level of activation would be statistically significant, to be used only in the design efficiency calculation. Increasing this will result in higher estimates of required effect.',

    'outputDirectory'          : 'If this is left blank, the output directory name is derived from the input data name.\n\nIf, however, you wish to explicitly choose the output directory name, for example, so that you can include in the name a hint about the particular analysis that was carried out, you can set this here.\n\nThis output directory naming behaviour is modified if you are setting up multiple analyses, where you are selecting multiple input data sets and will end up with multiple output directories. In this case, whatever you enter here will be used and appended to what would have been the default output directory name if you had entered nothing.',
    'totalVolumes'             : 'The number of FMRI volumes in the time series, including any initial volumes that you wish to delete. This will get set automatically once valid input data has been selected.\n\nAlternatively you can set this number by hand before selecting data so that you can setup and view a model without having any data, for experimental planning purposes etc.',
    'deleteVolumes'            : 'The number of initial FMRI volumes to delete before any further processing. Typically your experiment would have begun after these initial scans (sometimes called "dummy scans"). These should be the volumes that are not wanted because steady-state imaging has not yet been reached - typically two or three volumes. These volumes are deleted as soon as the analysis is started.',
    'TR'                       : 'The time (in seconds) between scanning successive FMRI volumes.',
    'highpassFilterCutoff'     : 'The high pass frequency cutoff point (seconds), that is, the longest temporal period that you will allow.\n\nA sensible setting in the case of an rArA or rArBrArB type block design is the (r+A) or (r+A+r+B) total cycle time.\n\nFor event-related designs the rule is not so simple, but in general the cutoff can typically be reduced at least to 50s.\n\nThis value is setup here rather than in Pre-stats because in FEAT it also affects the generation of the model; the same high pass filtering is applied to the model as to the data, to get the best possible match between the model and data.'
    
}

featView = tkp.NotebookGroup((
    tkp.VGroup(
        label='Misc',
        children=(
            'balloonHelp',
            'progressWatcher',
            'brainBackgroundThreshold',
            'noiseLevel',
            'temporalSmoothness',
            'zThreshold',
            tkp.Button('noiseLevelEstimate'),
            tkp.Button('highpassEstimate'))),
    tkp.VGroup(
        label='Data',
        children=(
            'inputData',
            'outputDirectory',
            'totalVolumes',
            'deleteVolumes',
            'TR',
            'highpassFilterCutoff')),
    tkp.VGroup(
        label='Pre-stats',
        children=(
            'altReferenceImage',
            'motionCorrection',
            'b0Unwarping',
            tkp.VGroup(
                label='B0 Unwarping options',
                children=(
                    'b0_fieldmap',
                    'b0_fieldmapMag',
                    'b0_echoSpacing',
                    'b0_TE',
                    'b0_unwarpDir',
                    'b0_signalLossThreshold')),
            'sliceTimingCorrection',
            'sliceTimingFile')),
    
))
    

class FeatFrame(tk.Frame):
    
    def __init__(self, parent, featOpts):
        
        tk.Frame.__init__(self, parent)
        self.pack(fill=tk.BOTH, expand=1)

        self.tkpFrame = tkp.buildGUI(self, featOpts, featView, labels, tooltips)
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
