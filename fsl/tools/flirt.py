#!/usr/bin/env python
#
# flirt.py - FLIRT front end.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from collections import OrderedDict

import props

flirtModes = OrderedDict((
    ('single',   'Input image -> Reference image'),
    ('multiple', 'Low res image -> High res image -> Reference image')))


modelDOFChoices = OrderedDict((
    ('rigid3',    'Rigid Body (3 parameter model)'),
    ('translate', 'Translation Only (3 parameter model)'),
    ('rigid6',    'Rigid Body (6 parameter model)'),
    ('rescale',   'Global Rescale (7 parameter model)'),
    ('trad',      'Traditional (9 parameter model)'),
    ('affine',    'Affine (12 parameter model)')))


searchModes = OrderedDict((
    ('nosearch',  'Already virtually aligned (no search)'),
    ('orient',    'Not aligned, but same orientation'),
    ('misorient', 'Incorrectly oriented')))


costFunctions = OrderedDict((
    ('correlation',     'Correlation Ratio'),
    ('mutualinfo',      'Mutual Information'),
    ('normmutualinfo',  'Normalised Mutual Information'),
    ('normcorrelation', 'Normalised Correlation (intra-modal)'),
    ('leastsquares',    'Least Squares (intra-modal)')))

interpolationMethods = OrderedDict((
    ('trilinear', 'Tri-Linear'),
    ('nn',        'Nearest Neighbour'),
    ('spline',    'Spline'),
    ('sinc',      'Sinc')))


sincWindowOpts = OrderedDict((
    ('rect',     'Rectangular'),
    ('hanning',  'Hanning'),
    ('blackman', 'Blackman')))


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
        'searchMode',
        props.HGroup(('searchAngleXMin', 'searchAngleXMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch'),
        props.HGroup(('searchAngleYMin', 'searchAngleYMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch'),
        props.HGroup(('searchAngleZMin', 'searchAngleZMax'),
                     visibleWhen=lambda i: i.searchMode != 'nosearch')))

costFuncOptions  = props.VGroup(
    label='Cost Function',
    children=(
        'costFunction',
        props.Widget(
            'costHistBins',
            visibleWhen=lambda i: i.costFunction in ['correlation',
                                                     'mutualinfo',
                                                     'normmutualinfo'])))

interpOptions = props.VGroup(
    label='Interpolation',
    children=(
        'interpolation',
        props.VGroup(('sincWindow', 'sincWindowWidth'),
                     visibleWhen=lambda i: i.interpolation == 'sinc')))

weightVolOptions = props.VGroup(
    label='Weighting Volumes',
    children=(
        'weightingReference',
        'weightingInput'))

flirtView = props.VGroup((
    'flirtMode',
    'refImage',
    props.Widget('inputImage',  visibleWhen=inSingleMode),
    props.Widget('inToRefMode', visibleWhen=inSingleMode), 
    props.Widget('hiResImage',  visibleWhen=inMultipleMode),
    props.Widget('hiToRefMode', visibleWhen=inMultipleMode),
    props.Widget('loResImage',  visibleWhen=inMultipleMode),
    props.Widget('loToHiMode',  visibleWhen=inMultipleMode), 
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
FSL_CONTEXT   = lambda args: Options()
FSL_INTERFACE = interface
FSL_ACTIONS   = [('Run FLIRT', runFlirt)]
