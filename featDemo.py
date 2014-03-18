#!/usr/bin/env python
#
# featDemo.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys

from collections import OrderedDict

import Tkinter as tk
import            ttk
import tkprop  as tkp

analysisTypeOpts = OrderedDict((
    ('firstLevel', 'First-level analysis'),
    ('highLevel',  'Higher-level analysis')))

analysisStageOpts = OrderedDict((
    ('full',       'Full analysis'),
    ('pre',        'Pre-stats'),
    ('pre-stats',  'Pre-stats + Stats'),
    ('stats',      'Stats'),
    ('stats-post', 'Stats + Post-stats'),
    ('post',       'Post-stats'),
    ('reg',        'Registration only')))

highLevelInputTypes = OrderedDict((
    ('featDirs',   'Inputs are lower-level FEAT directories'),
    ('copeImages', 'Inputs are 3D cope images from FEAT directories')))

sliceTimingOpts = OrderedDict((
    ('none',       'None'),
    ('regup',      'Regular up (0, 1, 2, ..., n-1)'),
    ('regdown',    'Regular down (n-1, n-2, ..., 0'),
    ('int',        'Interleaved (0, 2, 4, ..., 1, 3, 5, ...)'),
    ('orderFile',  'Use slice order file'),
    ('timingFile', 'Use slice timings file')))

perfusionOpts = OrderedDict((
    ('tag',     'First timepoint is tag'),
    ('control', 'First timepoint is control')))

motionParameterOpts = OrderedDict((
    ('none',     "Don't Add Motion Parameters"),
    ('standard', "Standard Motion Parameters"),
    ('extended', "Standard + Extended Motion Parameters")))

effectModellingOpts = OrderedDict((
    ('fixed',  'Fixed effects'),
    ('ols',    'Mixed effects: Simple OLS'),
    ('flame1', 'Mixed effects: FLAME 1'),
    ('flame2', 'Mixed effects: FLAME 1+2')))

zRenderingOpts = OrderedDict((
    ('actual', 'Use actual Z min/max'),
    ('preset', 'Use preset Z min/max')))

blobOpts = OrderedDict((
    ('solid',      'Solid blobs'),
    ('transparent','Transparent blobs')))

regSearchOpts = OrderedDict((
    ('none',   'No search'),
    ('normal', 'Normal search'),
    ('full',   'Full search')))

regDofOpts = OrderedDict((
    ('3',  '3 DOF'),
    ('6',  '6 DOF'),
    ('7',  '7 DOF'),
    ('9',  '9 DOF'),
    ('12', '12 DOF')))

regStructDofOpts = OrderedDict((
    ('3',   '3 DOF'),
    ('6',   '6 DOF'),
    ('7',   '7 DOF'),
    ('BBR', 'BBR'),
    ('12',  '12 DOF')))
                

class FeatOptions(tkp.HasProperties):

    analysisType   = tkp.Choice(analysisTypeOpts)
    analysisStages = tkp.Choice(analysisStageOpts)

    # Misc options
    balloonHelp              = tkp.Boolean(default=True)
    progressWatcher          = tkp.Boolean(default=True)
    brainBackgroundThreshold = tkp.Percentage(default=10)
    noiseLevel               = tkp.Percentage(default=0.66)
    temporalSmoothness       = tkp.Double(default=0.34, minval=-1.0, maxval=1.0)
    zThreshold               = tkp.Double(default=5.3, minval=0.0)

    # misc/higher level
    cleanUpFirstLevel        = tkp.Boolean(default=False)

    #
    # Data options
    #
    inputData            = tkp.List(minlen=1, listType=tkp.FilePath(exists=True))
    outputDirectory      = tkp.FilePath(isFile=False)
    totalVolumes         = tkp.Int(minval=0)
    deleteVolumes        = tkp.Int(minval=0)
    TR                   = tkp.Double(minval=0, default=3.0)
    highpassFilterCutoff = tkp.Int(minval=0, default=100)

    # data/higher level
    inputDataType        = tkp.Choice(highLevelInputTypes)
    higherLevelFeatInput = tkp.List(minlen=3, listType=tkp.FilePath(isFile=False, exists=True))
    higherLevelCopeInput = tkp.List(minlen=3, listType=tkp.FilePath(exists=True))

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
    b0_unwarpDir           = tkp.Choice(('x','-x','y','-y','z','-z'))
    b0_signalLossThreshold = tkp.Percentage(default=10)

    sliceTimingCorrection  = tkp.Choice(sliceTimingOpts)

    # slice timing file, displayed if the timing correction
    # choice is for a custom order/timing file
    sliceTimingFile       = tkp.FilePath(exists=True)
    sliceOrderFile        = tkp.FilePath(exists=True)
    
    brainExtraction       = tkp.Boolean(default=True)
    smoothingFWHM         = tkp.Double(minval=0.0, default=5.0)
    intensityNorm         = tkp.Boolean(default=False)
    perfusionSubtraction  = tkp.Boolean(default=False)

    # displayed if perfusion subtraction is enabled
    perfusionOption       = tkp.Choice(perfusionOpts)
    
    temporalHighpass      = tkp.Boolean(default=True)
    melodic               = tkp.Boolean(default=False)

    #
    # Stats options
    #
    useFILMPrewhitening    = tkp.Boolean(default=True)
    addMotionParameters    = tkp.Choice(motionParameterOpts)
    voxelwiseConfoundList  = tkp.FilePath(exists=True)
    applyExternalScript    = tkp.FilePath(exists=True)
    addAdditionalConfounds = tkp.FilePath(exists=True)

    # stats/higher level
    effectModelling = tkp.Choice(effectModellingOpts)
    outlierDeweighting = tkp.Boolean(default=False)

    #
    # Post-stats options
    #
    preThresholdMask = tkp.FilePath(exists=True)
    thresholding     = tkp.Choice(('None','Uncorrected','Voxel','Cluster'))

    # Thresholding sub-options
    # displayed if thresholding is not None
    pThreshold  = tkp.Double(minval=0.0, maxval=1.0, default=0.05)
    zThreshold  = tkp.Double(minval=0.0, default=2.3)

    renderZMinMax = tkp.Choice(zRenderingOpts)
    
    # displayed if renderZMinMax is 'preset'
    renderZMin    = tkp.Double(minval=0.0, default=2.0)
    renderZMax    = tkp.Double(minval=0.0, default=8.0)
    
    blobTypes     = tkp.Choice(blobOpts)
    createTSPlots = tkp.Boolean(default=True)

    #
    # Registration options
    #
    expandedFunctionalImage = tkp.FilePath(exists=True)
    mainStructuralImage     = tkp.FilePath(exists=True)
    standardSpaceImage      = tkp.FilePath(exists=True)

    # only shown if functional image is not none
    functionalSearch = tkp.Choice(regSearchOpts)
    functionalDof    = tkp.Choice(regDofOpts)

    # only shown if structural image is not none
    structuralSearch = tkp.Choice(regSearchOpts)
    structuralDof    = tkp.Choice(regStructDofOpts)

    # only shown if standard image is not none
    standardSearch = tkp.Choice(regSearchOpts)
    standardDof    = tkp.Choice(regDofOpts)
    nonLinearReg   = tkp.Boolean(default=False)
    # only shown if nonlinear reg is selected
    warpResolution = tkp.Double(minval=0.0, default=10.0)


    def __init__(self):
        """
        Adds some listeners to various inter-dependent properties.
        """

        def updateAnalysisStage(analysisType):
            if analysisType == 'highLevel':
                self.analysisStages = 'stats-post'
        
        FeatOptions.analysisType.addListener(self,
                                             'updateAnalysisStage',
                                              updateAnalysisStage)
        
labels = {
    # misc
    'balloonHelp'              : 'Balloon help',
    'progressWatcher'          : 'Progress watcher',
    'brainBackgroundThreshold' : 'Brain/background threshold',
    'noiseLevel'               : 'Noise level',
    'temporalSmoothness'       : 'Temporal smoothness',
    'zThreshold'               : 'Z threshold',

    # data
    'inputData'                : 'Select 4D data',
    'outputDirectory'          : 'Output directory',
    'totalVolumes'             : 'Total volumes',
    'deleteVolumes'            : 'Delete volumes',
    'TR'                       : 'TR (s)',
    'highpassFilterCutoff'     : 'High pass filter cutoff (s)',

    # pre-stats
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
    'sliceOrderFile'           : 'Slice order file',
    'sliceTimingFile'          : 'Slice timing file',
    'brainExtraction'          : 'BET brain extraction',
    'smoothingFWHM'            : 'Spatial smoothing FWHM (mm)',
    'intensityNorm'            : 'Intensity normalization',
    'perfusion'                : 'Perfusion subtraction',
    'temporalHighpass'         : 'Highpass',
    'melodic'                  : 'MELODIC ICA data exploration',

    # stats
    'useFILMPrewhitening'      : 'Use FILM Prewhitening',
    'addMotionParameters'      : 'Motion parameters',
    'voxelwiseConfoundList'    : 'Voxelwise Counfound List',
    'applyExternalScript'      : 'Apply external Script',
    'addAdditionalConfounds'   : 'Additional confound EVs',

    # post stats
    'preThresholdMask'         : 'Pre-threshold masking',
    'thresholding'             : 'Thresholding type',
    'pThreshold'               : 'P threshold',
    'zThreshold'               : 'Z threshold',
    'renderZMin'               : 'Min',
    'renderZMax'               : 'Max',
    'createTSPlots'            : 'Create time series plots',

    # registration
    'expandedFunctionalImage'  : 'Expanded functional image',
    'mainStructuralImage'      : 'Main structural image',
    'standardSpaceImage'       : 'Standard space image',
    'nonLinearReg'             : 'Non linear',
    'warpResolution'           : 'Warp resolution (mm)'
    
}

def tabEnabled(featOpts, tabName):

    aType  = featOpts.analysisType
    aStage = featOpts.analysisStages

    if tabName == 'Pre-stats':
        
        if aType == 'highLevel':
            return False
        
        if (aStage != 'full') and (aStage.find('pre') < 0):
            return False
        
    elif tabName == 'Stats':

        if (aStage != 'full') and (aStage.find('stats') < 0):
            return False
        
    elif tabName == 'Post-stats':

        if (aStage != 'full') and (aStage.find('post') < 0):
            return False        
        
    elif tabName == 'Registration':
        if aType == 'highLevel': return False

        if (aStage != 'full') and (aStage.find('reg') < 0):
            return False 
        
    return True

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
        tkp.VGroup(
            visibleWhen=lambda i:i.analysisType == 'firstLevel',
            children=(
                'inputData',
                'outputDirectory',
                'totalVolumes',
                'deleteVolumes',
                'TR',
                'highpassFilterCutoff')),
        tkp.VGroup(
            visibleWhen=lambda i:i.analysisType == 'highLevel',
            children=(
                'inputDataType',
                tkp.Widget('higherLevelFeatInput', visibleWhen=lambda i:i.inputDataType == 'featDirs'),
                tkp.Widget('higherLevelCopeInput', visibleWhen=lambda i:i.inputDataType == 'copeImages'),
                'outputDirectory'))))

prestatsView = tkp.VGroup(
    label='Pre-stats',
    visibleWhen=lambda i: tabEnabled(i, 'Pre-stats'),
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
        tkp.Widget('sliceTimingFile', visibleWhen=lambda i: i.sliceTimingCorrection == 'timingFile'),
        tkp.Widget('sliceOrderFile',  visibleWhen=lambda i: i.sliceTimingCorrection == 'orderFile'),
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

statsView = tkp.VGroup(
    label='Stats',
    visibleWhen=lambda i: tabEnabled(i, 'Stats'),
    children=(
        'useFILMPrewhitening',
        'addMotionParameters',
        'voxelwiseConfoundList',
        'applyExternalScript',
        'addAdditionalConfounds',
        tkp.Button(text='Model setup wizard'),
        tkp.Button(text='Full model setup')))

postStatsView = tkp.VGroup(
    label='Post-stats',
    visibleWhen=lambda i: tabEnabled(i, 'Post-stats'),
    children=(
        'preThresholdMask',
        tkp.VGroup(
            label='Thresholding',
            border=True,
            children=(
                'thresholding',
                tkp.Widget('pThreshold', visibleWhen=lambda i:i.thresholding != 'None'),
                tkp.Widget('zThreshold', visibleWhen=lambda i:i.thresholding == 'Cluster'))),
        tkp.Button('Contrast masking',   visibleWhen=lambda i:i.thresholding != 'None'),
        tkp.VGroup(
            label='Rendering',
            border=True,
            visibleWhen=lambda i: i.thresholding != 'None',
            children=(
                'renderZMinMax',
                tkp.Widget('renderZMin', visibleWhen=lambda i:i.renderZMinMax == 'preset'),
                tkp.Widget('renderZMax', visibleWhen=lambda i:i.renderZMinMax == 'preset'),
                'blobTypes')),
        'createTSPlots'))

regView = tkp.VGroup(
    label='Registration',
    visibleWhen=lambda i: tabEnabled(i, 'Registration'),
    children=(
        'expandedFunctionalImage',
        tkp.HGroup(
            label='Functional -> Expanded functional',
            border=True,
            visibleWhen=lambda i:i.expandedFunctionalImage is not None,
            children=('functionalSearch', 'functionalDof')),
        'mainStructuralImage',
        tkp.HGroup(
            label='Functional -> Structural',
            border=True,
            visibleWhen=lambda i:i.mainStructuralImage is not None,
            children=('structuralSearch', 'structuralDof')), 
        'standardSpaceImage',
        tkp.VGroup(
            label='Structural -> Standard',
            border=True,
            visibleWhen=lambda i:i.standardSpaceImage is not None,
            children=(
                tkp.HGroup(('standardSearch', 'standardDof')),
                tkp.HGroup(('nonLinearReg',
                            tkp.Widget('warpResolution',visibleWhen=lambda i:i.nonLinearReg)))))))

featView =tkp.VGroup((
    'analysisType',
    tkp.Widget('analysisStages', enabledWhen=lambda i: i.analysisType == 'firstLevel'),
    tkp.NotebookGroup((
        miscView,
        dataView,
        prestatsView,
        statsView,
        postStatsView,
        regView))))

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

    app   = tk.Tk()
    fopts = FeatOptions()
    frame = FeatFrame(app, fopts)

    app.title('FEAT')

    print('Before')
    print(fopts)

    # stupid hack for testing under OS X - forces the TK
    # window to be displayed above all other windows
    os.system('''/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true' ''')
    
    app.mainloop()

    print('After')
    print(fopts)
