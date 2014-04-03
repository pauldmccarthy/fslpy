#!/usr/bin/env python
#
# flirt.py - FLIRT front end.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os
import sys

from collections import OrderedDict

import wx

import fsl.props as props

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


class Options(props.HasProperties):

    flirtMode   = props.Choice(flirtModes)

    inputImage  = props.FilePath(exists=True, required=lambda i: i.flirtMode == 'single')
    loResImage  = props.FilePath(exists=True, required=lambda i: i.flirtMode == 'multiple')
    hiResImage  = props.FilePath(exists=True, required=lambda i: i.flirtMode == 'multiple')
    refImage    = props.FilePath(exists=True, required=True)
    outputImage = props.FilePath(             required=True)

    sndyImages  = props.List(props.FilePath(exists=True))

    inToRefMode = props.Choice(modelDOFChoices)
    loToHiMode  = props.Choice(modelDOFChoices)
    hiToRefMode = props.Choice(modelDOFChoices)

    # Advanced -> Search
    searchMode      = props.Choice(searchModes)
    searchAngleXMin = props.Double(minval=-180.0, maxval=180.0)
    searchAngleXMax = props.Double(minval=-180.0, maxval=180.0)
    searchAngleYMin = props.Double(minval=-180.0, maxval=180.0)
    searchAngleYMax = props.Double(minval=-180.0, maxval=180.0)
    searchAngleZMin = props.Double(minval=-180.0, maxval=180.0)
    searchAngleZMax = props.Double(minval=-180.0, maxval=180.0)

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


searchOptions    = props.VGroup((
    'searchMode',
    props.HGroup(('searchAngleXMin', 'searchAngleXMax'), visibleWhen=lambda i:i.searchMode != 'nosearch'),
    props.HGroup(('searchAngleYMin', 'searchAngleYMax'), visibleWhen=lambda i:i.searchMode != 'nosearch'),
    props.HGroup(('searchAngleZMin', 'searchAngleZMax'), visibleWhen=lambda i:i.searchMode != 'nosearch')))

costFuncOptions  = props.VGroup((
    'costFunction',
    props.Widget('costHistBins', visibleWhen=lambda i:i.costFunction in ['correlation', 'mutualinfo', 'normmutualinfo'])))

interpOptions    = props.VGroup((
    'interpolation',
    props.VGroup(('sincWindow', 'sincWindowWidth'), visibleWhen=lambda i: i.interpolation == 'sinc')))

weightVolOptions = props.VGroup((
    'weightingReference',
    'weightingInput'))

flirtView = props.VGroup((
    'flirtMode',
    'refImage',
    props.Widget('inputImage',  visibleWhen=lambda i: i.flirtMode == 'single'),
    props.Widget('inToRefMode', visibleWhen=lambda i: i.flirtMode == 'single'), 
    props.Widget('hiResImage',  visibleWhen=lambda i: i.flirtMode == 'multiple'),
    props.Widget('hiToRefMode', visibleWhen=lambda i: i.flirtMode == 'multiple'),
    props.Widget('loResImage',  visibleWhen=lambda i: i.flirtMode == 'multiple'),
    props.Widget('loToHiMode',  visibleWhen=lambda i: i.flirtMode == 'multiple'), 
    'outputImage',
    'sndyImages',
    props.NotebookGroup(label='Advanced Options',
                        children=(searchOptions,
                                  costFuncOptions,
                                  interpOptions,
                                  weightVolOptions))))

def run():
    pass


def openHelp():
    """
    Opens BET help in a web browser.
    """

    fsldir = os.environ.get('FSLDIR', None)
    url    = 'file://{}/doc/redirects/flirt.html'.format(fsldir)

    if fsldir is not None:
        import webbrowser
        webbrowser.open(url)
    else:

        msg = 'The FSLDIR environment variable is not set - I don\'t '\
            'know where to find the FSL documentation.'

        wx.MessageDialog(
            None,
            message=msg,
            style=wx.OK | wx.ICON_ERROR).ShowModal()


def editPanel(parent, opts):

    buttons = OrderedDict((
        ('Go', run),
        ('Exit', parent.Destroy),
        ('Help', openHelp)))

    return props.buildGUI(
        parent, opts, flirtView, labels, tooltips, buttons)
