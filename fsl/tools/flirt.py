#!/usr/bin/env python
#
# flirt.py - FLIRT front end.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module implements a non-functional front end to the FSL flirt tool.
"""


import props
props.initGUI()

flirtModes           = ['single',
                        'multiple']
modelDOFChoices      = ['rigid3',  
                        'translate',
                        'rigid6',  
                        'rescale', 
                        'trad',    
                        'affine']
searchModes          = ['nosearch',
                        'orient',
                        'misorient']
costFunctions        = ['correlation',   
                        'mutualinfo',    
                        'normmutualinfo',
                        'normcorrelation',
                        'leastsquares']
interpolationMethods = ['trilinear',
                        'nn',
                        'spline',
                        'sinc']
sincWindowOpts       = ['rect',
                        'hanning',
                        'blackman']


flirtModeLabels = {
    'single'   : 'Input image -> Reference image',
    'multiple' : 'Low res image -> High res image -> Reference image'}


modelDOFChoiceLabels = {
    'rigid3'    : 'Rigid Body (3 parameter model)',
    'translate' : 'Translation Only (3 parameter model)',
    'rigid6'    : 'Rigid Body (6 parameter model)',
    'rescale'   : 'Global Rescale (7 parameter model)',
    'trad'      : 'Traditional (9 parameter model)',
    'affine'    : 'Affine (12 parameter model)'}


searchModeLabels = {
    'nosearch'  : 'Already virtually aligned (no search)',
    'orient'    : 'Not aligned, but same orientation',
    'misorient' : 'Incorrectly oriented'}


costFunctionLabels = {
    'correlation'     : 'Correlation Ratio',
    'mutualinfo'      : 'Mutual Information',
    'normmutualinfo'  : 'Normalised Mutual Information',
    'normcorrelation' : 'Normalised Correlation (intra-modal)',
    'leastsquares'    : 'Least Squares (intra-modal)'}

interpolationMethodLabels = {
    'trilinear' : 'Tri-Linear',
    'nn'        : 'Nearest Neighbour',
    'spline'    : 'Spline',
    'sinc'      : 'Sinc'}


sincWindowOptLabels = {
    'rect'     : 'Rectangular',
    'hanning'  : 'Hanning',
    'blackman' : 'Blackman'}


def inSingleMode(  opts): return opts.flirtMode == 'single'
def inMultipleMode(opts): return opts.flirtMode == 'multiple'


class Options(props.HasProperties):


    flirtMode   = props.Choice(flirtModes)

    inputImage  = props.FilePath(exists=True, required=inSingleMode)
    loResImage  = props.FilePath(exists=True, required=inMultipleMode)
    hiResImage  = props.FilePath(exists=True, required=inMultipleMode)
    refImage    = props.FilePath(exists=True, required=True)
    outputImage = props.FilePath(             required=True)

    sndyImages  = props.List(props.FilePath(exists=True))

    inToRefMode = props.Choice(modelDOFChoices)
    loToHiMode  = props.Choice(modelDOFChoices)
    hiToRefMode = props.Choice(modelDOFChoices)

    # Advanced -> Search
    searchMode      = props.Choice(searchModes)
    searchAngleXMin = props.Real(minval=-180.0, maxval=180.0)
    searchAngleXMax = props.Real(minval=-180.0, maxval=180.0)
    searchAngleYMin = props.Real(minval=-180.0, maxval=180.0)
    searchAngleYMax = props.Real(minval=-180.0, maxval=180.0)
    searchAngleZMin = props.Real(minval=-180.0, maxval=180.0)
    searchAngleZMax = props.Real(minval=-180.0, maxval=180.0)

    # Advanced -> Cost function
    costFunction    = props.Choice(costFunctions)
    costHistBins    = props.Int(minval=0, default=256)


    # Advanced -> Interpolation
    interpolation   = props.Choice(interpolationMethods)
    sincWindow      = props.Choice(sincWindowOpts)
    sincWindowWidth = props.Int(minval=0, default=7)

    # Advanced -> Weighting
    weightingReference = props.FilePath(exists=True)
    weightingInput     = props.FilePath(exists=True)

    
labels   = None
tooltips = None


searchOptions    = props.VGroup(
    label='Search',
    children=(
        props.Widget('searchMode', labels=searchModeLabels),
        props.HGroup(('searchAngleXMin', 'searchAngleXMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch'),
        props.HGroup(('searchAngleYMin', 'searchAngleYMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch'),
        props.HGroup(('searchAngleZMin', 'searchAngleZMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch')))

costFuncOptions  = props.VGroup(
    label='Cost Function',
    children=(
        props.Widget('costFunction', labels=costFunctionLabels),
        props.Widget(
            'costHistBins',
            visibleWhen=lambda i: i.costFunction in ['correlation',
                                                     'mutualinfo',
                                                     'normmutualinfo'])))

interpOptions = props.VGroup(
    label='Interpolation',
    children=(
        props.Widget('interpolation', labels=interpolationMethodLabels),
        props.VGroup((props.Widget('sincWindow', labels=sincWindowOptLabels),
                      'sincWindowWidth'),
                     visibleWhen=lambda i: i.interpolation == 'sinc')))

weightVolOptions = props.VGroup(
    label='Weighting Volumes',
    children=(
        'weightingReference',
        'weightingInput'))

flirtView = props.VGroup((
    props.Widget('flirtMode', labels=flirtModeLabels),
    'refImage',
    props.Widget('inputImage', visibleWhen=inSingleMode),
    props.Widget('inToRefMode',
                 labels=modelDOFChoiceLabels,
                 visibleWhen=inSingleMode), 
    props.Widget('hiResImage',  visibleWhen=inMultipleMode),
    props.Widget('hiToRefMode',
                 labels=modelDOFChoiceLabels,
                 visibleWhen=inMultipleMode),
    props.Widget('loResImage',  visibleWhen=inMultipleMode),
    props.Widget('loToHiMode',
                 labels=modelDOFChoiceLabels,
                 visibleWhen=inMultipleMode), 
    'outputImage',
    'sndyImages',
    props.NotebookGroup(label='Advanced Options',
                        border=True,
                        children=(searchOptions,
                                  costFuncOptions,
                                  interpOptions,
                                  weightVolOptions))))


def runFlirt(parent, opts):
    pass


def interface(parent, args, opts):
    return props.buildGUI(
        parent, opts, flirtView, labels, tooltips)


FSL_TOOLNAME  = 'FLIRT'
FSL_HELPPAGE  = 'flirt'
FSL_CONTEXT   = lambda *a: Options()
FSL_INTERFACE = interface
FSL_ACTIONS   = [('Run FLIRT', runFlirt)]
