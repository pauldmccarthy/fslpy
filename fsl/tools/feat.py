#!/usr/bin/env python
#
# feat.py - 
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys
import logging

from collections import OrderedDict

import wx

import fsl.props as props

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
                

class Options(props.HasProperties):

    analysisType   = props.Choice(analysisTypeOpts)
    analysisStages = props.Choice(analysisStageOpts)

    # Misc options
    balloonHelp              = props.Boolean(default=True)
    progressWatcher          = props.Boolean(default=True)
    brainBackgroundThreshold = props.Percentage(default=10)
    efficNoiseLevel          = props.Percentage(default=0.66)
    efficTemporalSmoothness  = props.Double(default=0.34, minval=-1.0, maxval=1.0)
    efficZThreshold          = props.Double(default=5.3, minval=0.0)

    # misc/higher level
    cleanUpFirstLevel        = props.Boolean(default=False)

    #
    # Data options
    #
    inputData            = props.List(minlen=1, listType=props.FilePath(exists=True, required=True))
    outputDirectory      = props.FilePath(isFile=False, required=True)
    totalVolumes         = props.Int(minval=0)
    deleteVolumes        = props.Int(minval=0)
    TR                   = props.Double(minval=0, default=3.0)
    highpassFilterCutoff = props.Int(minval=0, default=100)

    # data/higher level
    inputDataType        = props.Choice(highLevelInputTypes)
    higherLevelFeatInput = props.List(minlen=3, listType=props.FilePath(isFile=False, exists=True, required=lambda i:i.inputDataType=='featDirs'))
    higherLevelCopeInput = props.List(minlen=3, listType=props.FilePath(              exists=True, required=lambda i:i.inputDataType=='copeImages'))

    #
    # Pre-stats options
    #
    altReferenceImage = props.FilePath(exists=True)
    motionCorrection  = props.Choice(('MCFLIRT', 'None'))
    b0Unwarping       = props.Boolean(default=False)

    # B0 unwarping sub-options - displayed if b0Unwarping is true
    b0_fieldmap            = props.FilePath(exists=True, required=lambda i:i.b0Unwarping)
    b0_fieldmapMag         = props.FilePath(exists=True, required=lambda i:i.b0Unwarping)
    b0_echoSpacing         = props.Double(minval=0.0, default=0.7)
    b0_TE                  = props.Double(minval=0.0, default=35)
    b0_unwarpDir           = props.Choice(('x','-x','y','-y','z','-z'))
    b0_signalLossThreshold = props.Percentage(default=10)

    sliceTimingCorrection  = props.Choice(sliceTimingOpts)

    # slice timing file, displayed if the timing correction
    # choice is for a custom order/timing file
    sliceTimingFile       = props.FilePath(exists=True, required=lambda i:i.sliceTimingCorrection=='timingFile')
    sliceOrderFile        = props.FilePath(exists=True, required=lambda i:i.sliceTimingCorrection=='orderFile')
    
    brainExtraction       = props.Boolean(default=True)
    smoothingFWHM         = props.Double(minval=0.0, default=5.0)
    intensityNorm         = props.Boolean(default=False)
    perfusionSubtraction  = props.Boolean(default=False)

    # displayed if perfusion subtraction is enabled
    perfusionOption       = props.Choice(perfusionOpts)
    
    temporalHighpass      = props.Boolean(default=True)
    melodic               = props.Boolean(default=False)

    #
    # Stats options
    #
    useFILMPrewhitening    = props.Boolean(default=True)
    addMotionParameters    = props.Choice(motionParameterOpts)
    voxelwiseConfoundList  = props.FilePath(exists=True)
    applyExternalScript    = props.FilePath(exists=True)
    addAdditionalConfounds = props.FilePath(exists=True)

    # stats/higher level
    effectModelling = props.Choice(effectModellingOpts)
    outlierDeweighting = props.Boolean(default=False)

    #
    # Post-stats options
    #
    preThresholdMask = props.FilePath(exists=True)
    thresholding     = props.Choice(('None','Uncorrected','Voxel','Cluster'))

    # Thresholding sub-options
    # displayed if thresholding is not None
    pThreshold  = props.Double(minval=0.0, maxval=1.0, default=0.05)
    zThreshold  = props.Double(minval=0.0, default=2.3)

    renderZMinMax = props.Choice(zRenderingOpts)
    
    # displayed if renderZMinMax is 'preset'
    renderZMin    = props.Double(minval=0.0, default=2.0)
    renderZMax    = props.Double(minval=0.0, default=8.0)
    
    blobTypes     = props.Choice(blobOpts)
    createTSPlots = props.Boolean(default=True)

    #
    # Registration options
    #
    expandedFunctionalImage = props.FilePath(exists=True)
    mainStructuralImage     = props.FilePath(exists=True)
    standardSpaceImage      = props.FilePath(exists=True)

    # only shown if functional image is not none
    functionalSearch = props.Choice(regSearchOpts)
    functionalDof    = props.Choice(regDofOpts)

    # only shown if structural image is not none
    structuralSearch = props.Choice(regSearchOpts)
    structuralDof    = props.Choice(regStructDofOpts)

    # only shown if standard image is not none
    standardSearch = props.Choice(regSearchOpts)
    standardDof    = props.Choice(regDofOpts)
    nonLinearReg   = props.Boolean(default=False)
    # only shown if nonlinear reg is selected
    warpResolution = props.Double(minval=0.0, default=10.0)

    def __init__(self):
        """
        Adds some listeners to various inter-dependent properties.
        """

        def updateAnalysisStage(analysisType, *a):
            if analysisType == 'highLevel':
                self.analysisStages = 'stats-post'
        
        Options.analysisType.addListener(self,
                                         'updateAnalysisStage',
                                         updateAnalysisStage)
        
labels = {
    # misc
    'balloonHelp'              : 'Balloon help',
    'progressWatcher'          : 'Progress watcher',
    'brainBackgroundThreshold' : 'Brain/background threshold',
    'efficNoiseLevel'          : 'Noise level',
    'efficTemporalSmoothness'  : 'Temporal smoothness',
    'efficZThreshold'          : 'Z threshold',

    # data
    'inputData'                : 'Select 4D data',
    'outputDirectory'          : 'Output directory',
    'totalVolumes'             : 'Total volumes',
    'deleteVolumes'            : 'Delete volumes',
    'TR'                       : 'TR (s)',
    'highpassFilterCutoff'     : 'High pass filter cutoff (s)',
    'higherLevelFeatInput'     : 'Feat directories',
    'higherLevelCopeInput'     : 'COPE images',

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

tooltips = {}

def tabEnabled(featOpts, tabName):

    aType  = featOpts.analysisType
    aStage = featOpts.analysisStages

    enabled = True

    if tabName == 'Pre-stats':
        
        if aType == 'highLevel':
            enabled = False
        
        elif (aStage != 'full') and (aStage.find('pre') < 0):
            enabled = False
        
    elif tabName == 'Stats':

        if (aStage != 'full') and (aStage.find('stats') < 0):
            enabled = False
        
    elif tabName == 'Post-stats':

        if (aStage != 'full') and (aStage.find('post') < 0):
            enabled = False        
        
    elif tabName == 'Registration':
        if aType == 'highLevel': enabled = False
        
    return enabled

miscView = props.VGroup(
    label='Misc',
    children=(
        'balloonHelp',
        'progressWatcher',
        'brainBackgroundThreshold',
        props.VGroup(
            label='Design efficiency',
            border=True,
            children=(
                'efficNoiseLevel',
                'efficTemporalSmoothness',
                'efficZThreshold',
                props.Button(text='Estimate noise and smoothness'),
                props.Button(text='Estimate highpass filter')))))

dataView = props.VGroup(
    label='Data',
    children=(
        props.VGroup(
            visibleWhen=lambda i:i.analysisType == 'firstLevel',
            children=(
                'inputData',
                'outputDirectory',
                'totalVolumes',
                'deleteVolumes',
                'TR',
                'highpassFilterCutoff')),
        props.VGroup(
            visibleWhen=lambda i:i.analysisType == 'highLevel',
            children=(
                'inputDataType',
                props.Widget('higherLevelFeatInput', visibleWhen=lambda i:i.inputDataType == 'featDirs'),
                props.Widget('higherLevelCopeInput', visibleWhen=lambda i:i.inputDataType == 'copeImages'),
                'outputDirectory'))))

prestatsView = props.VGroup(
    label='Pre-stats',
    enabledWhen=lambda i: tabEnabled(i, 'Pre-stats'),
    children=(
        'altReferenceImage',
        'motionCorrection',
        'b0Unwarping',
        props.VGroup(
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
        props.Widget('sliceTimingFile', visibleWhen=lambda i: i.sliceTimingCorrection == 'timingFile'),
        props.Widget('sliceOrderFile',  visibleWhen=lambda i: i.sliceTimingCorrection == 'orderFile'),
        'brainExtraction',
        'smoothingFWHM',
        'intensityNorm',
        props.HGroup(
            showLabels=False,
            key='perfusion',
            children=(
                'perfusionSubtraction',
                props.Widget('perfusionOption',
                           visibleWhen=lambda i: i.perfusionSubtraction))),
        'temporalHighpass',
        'melodic'))

statsView = props.VGroup(
    label='Stats',
    enabledWhen=lambda i: tabEnabled(i, 'Stats'),
    children=(
        'useFILMPrewhitening',
        'addMotionParameters',
        'voxelwiseConfoundList',
        'applyExternalScript',
        'addAdditionalConfounds',
        props.Button(text='Model setup wizard'),
        props.Button(text='Full model setup')))

postStatsView = props.VGroup(
    label='Post-stats',
    enabledWhen=lambda i: tabEnabled(i, 'Post-stats'),
    children=(
        'preThresholdMask',
        'createTSPlots',
        props.VGroup(
            label='Thresholding',
            border=True,
            children=(
                'thresholding',
                props.Widget('pThreshold',         visibleWhen=lambda i:i.thresholding != 'None'),
                props.Widget('zThreshold',         visibleWhen=lambda i:i.thresholding == 'Cluster'),
                props.Button('Contrast masking',   visibleWhen=lambda i:i.thresholding != 'None'))),
        props.VGroup(
            label='Rendering',
            border=True,
            visibleWhen=lambda i: i.thresholding != 'None',
            children=(
                'renderZMinMax',
                props.Widget('renderZMin', visibleWhen=lambda i:i.renderZMinMax == 'preset'),
                props.Widget('renderZMax', visibleWhen=lambda i:i.renderZMinMax == 'preset'),
                'blobTypes'))))

regView = props.VGroup(
    label='Registration',
    enabledWhen=lambda i: tabEnabled(i, 'Registration'),
    children=(
        'expandedFunctionalImage',
        props.HGroup(
            label='Functional -> Expanded functional',
            border=True,
            visibleWhen=lambda i:i.expandedFunctionalImage is not None,
            children=('functionalSearch', 'functionalDof')),
        'mainStructuralImage',
        props.HGroup(
            label='Functional -> Structural',
            border=True,
            visibleWhen=lambda i:i.mainStructuralImage is not None,
            children=('structuralSearch', 'structuralDof')), 
        'standardSpaceImage',
        props.VGroup(
            label='Structural -> Standard',
            border=True,
            visibleWhen=lambda i:i.standardSpaceImage is not None,
            children=(
                props.HGroup(('standardSearch', 'standardDof')),
                props.HGroup(('nonLinearReg',
                            props.Widget('warpResolution',visibleWhen=lambda i:i.nonLinearReg)))))))

featView =props.VGroup((
    'analysisType',
    props.Widget('analysisStages', enabledWhen=lambda i: i.analysisType == 'firstLevel'),
    props.NotebookGroup((
        miscView,
        dataView,
        prestatsView,
        statsView,
        postStatsView,
        regView))))


def editPanel(parent, featOpts):

    buttons = OrderedDict((
        ('Run FEAT', parent.Destroy),
        ('Quit',     parent.Destroy)))

    return props.buildGUI(
        parent, featOpts, featView, labels, tooltips, buttons)
