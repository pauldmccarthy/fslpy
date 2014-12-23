#!/usr/bin/env python
#
# strings.py - Labels used throughout various parts of FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is a home for labels and tooltips used throughout FSLView.

 - labels

 - tooltips
"""

import logging

log = logging.getLogger(__name__)

import fsl.utils.typedict as td
import fsl.data.image     as fslimage
        
labels = td.TypeDict({
    
    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'SpacePanel'      : 'Space inspector',

    'OpenFileAction'      : 'Add image file',
    'OpenStandardAction'  : 'Add standard',
    'LoadColourMapAction' : 'Load custom colour map',


    ('CanvasPanel', 'screenshot')              : 'Take screenshot',
    ('CanvasPanel', 'toggleColourBar')         : 'Show/hide colour bar',
    ('CanvasPanel', 'toggleImageList')         : 'Show/hide image list',
    ('CanvasPanel', 'toggleDisplayProperties') : 'Show/hide display properties',
    ('CanvasPanel', 'toggleLocationPanel')     : 'Show/hide location panel',
    ('CanvasPanel', 'toggleCanvasProperties')  : 'Show/hide canvas properties',


    ('CanvasPanel', 'showCursor')         : 'Show location cursor',
    ('CanvasPanel', 'syncLocation')       : 'Sync location',
    ('CanvasPanel', 'syncImageOrder')     : 'Sync image order',
    ('CanvasPanel', 'syncVolume')         : 'Sync volume',
    ('CanvasPanel', 'profile')            : 'Profile',
    ('CanvasPanel', 'zoom')               : 'Zoom',
    ('CanvasPanel', 'colourBarLocation')  : 'Colour bar location',
    ('CanvasPanel', 'colourBarLabelSide') : 'Colour bar label side',

    ('OrthoPanel', 'showXCanvas') : 'Show X canvas',
    ('OrthoPanel', 'showYCanvas') : 'Show Y canvas',
    ('OrthoPanel', 'showZCanvas') : 'Show Z canvas',
    ('OrthoPanel', 'showLabels')  : 'Show labels',
    ('OrthoPanel', 'layout')      : 'Layout',
    ('OrthoPanel', 'xzoom')       : 'X zoom',
    ('OrthoPanel', 'yzoom')       : 'Y zoom',
    ('OrthoPanel', 'zzoom')       : 'Z zoom',

    ('Image', 'lowlong',   fslimage.ORIENT_A2P)               : 'Anterior',
    ('Image', 'lowlong',   fslimage.ORIENT_P2A)               : 'Posterior',
    ('Image', 'lowlong',   fslimage.ORIENT_L2R)               : 'Left',
    ('Image', 'lowlong',   fslimage.ORIENT_R2L)               : 'Right',
    ('Image', 'lowlong',   fslimage.ORIENT_I2S)               : 'Inferior',
    ('Image', 'lowlong',   fslimage.ORIENT_S2I)               : 'Superior',
    ('Image', 'lowlong',   fslimage.ORIENT_UNKNOWN)           : 'Unknown',
    ('Image', 'highlong',  fslimage.ORIENT_A2P)               : 'Posterior',
    ('Image', 'highlong',  fslimage.ORIENT_P2A)               : 'Anterior',
    ('Image', 'highlong',  fslimage.ORIENT_L2R)               : 'Right',
    ('Image', 'highlong',  fslimage.ORIENT_R2L)               : 'Left',
    ('Image', 'highlong',  fslimage.ORIENT_I2S)               : 'Superior',
    ('Image', 'highlong',  fslimage.ORIENT_S2I)               : 'Inferior',
    ('Image', 'highlong',  fslimage.ORIENT_UNKNOWN)           : 'Unknown',
    ('Image', 'lowshort',  fslimage.ORIENT_A2P)               : 'A',
    ('Image', 'lowshort',  fslimage.ORIENT_P2A)               : 'P',
    ('Image', 'lowshort',  fslimage.ORIENT_L2R)               : 'L',
    ('Image', 'lowshort',  fslimage.ORIENT_R2L)               : 'R',
    ('Image', 'lowshort',  fslimage.ORIENT_I2S)               : 'I',
    ('Image', 'lowshort',  fslimage.ORIENT_S2I)               : 'S',
    ('Image', 'lowshort',  fslimage.ORIENT_UNKNOWN)           : '?',
    ('Image', 'highshort', fslimage.ORIENT_A2P)               : 'P',
    ('Image', 'highshort', fslimage.ORIENT_P2A)               : 'A',
    ('Image', 'highshort', fslimage.ORIENT_L2R)               : 'R',
    ('Image', 'highshort', fslimage.ORIENT_R2L)               : 'L',
    ('Image', 'highshort', fslimage.ORIENT_I2S)               : 'S',
    ('Image', 'highshort', fslimage.ORIENT_S2I)               : 'I',
    ('Image', 'highshort', fslimage.ORIENT_UNKNOWN)           : '?',
    ('Image', 'space',     fslimage.NIFTI_XFORM_UNKNOWN)      : 'Unknown',
    ('Image', 'space',     fslimage.NIFTI_XFORM_SCANNER_ANAT) : 'Scanner anatomical',
    ('Image', 'space',     fslimage.NIFTI_XFORM_ALIGNED_ANAT) : 'Aligned anatomical',
    ('Image', 'space',     fslimage.NIFTI_XFORM_TALAIRACH)    : 'Talairach', 
    ('Image', 'space',     fslimage.NIFTI_XFORM_MNI_152)      : 'MNI152',


    ('LocationPanel', 'outOfBounds') : 'Out of bounds',
    ('LocationPanel', 'spaceLabel')  : 'space',
    ('LocationPanel', 'worldLabel')  : 'World location (mm)',
    ('LocationPanel', 'voxelLabel')  : 'Voxel coordinates',
    ('LocationPanel', 'volumeLabel') : 'Volume (index)' ,

    ('OrthoViewProfile', 'nav')    : 'Navigate',
    ('OrthoViewProfile', 'pan')    : 'Pan',
    ('OrthoViewProfile', 'zoom')   : 'Zoom',

    ('OrthoEditProfile', 'nav')    : 'Navigate',
    ('OrthoEditProfile', 'pan')    : 'Pan',
    ('OrthoEditProfile', 'zoom')   : 'Zoom',
    ('OrthoEditProfile', 'sel')    : 'Select',
    ('OrthoEditProfile', 'desel')  : 'Deselect',
    ('OrthoEditProfile', 'selint') : 'Select by intensity',

    ('OrthoViewProfile', 'centreCursor') : 'Centre cursor',
    ('OrthoViewProfile', 'resetZoom')    : 'Reset zoom',


    ('OrthoEditProfile', 'undo')                    : 'Undo',
    ('OrthoEditProfile', 'redo')                    : 'Redo',
    ('OrthoEditProfile', 'fillSelection')           : 'Fill selected region',
    ('OrthoEditProfile', 'clearSelection')          : 'Clear selection',
    ('OrthoEditProfile', 'createMaskFromSelection') : 'Create mask from selected region',
    ('OrthoEditProfile', 'createROIFromSelection')  : 'Create ROI from selected region',

    ('Profile', 'mode') : 'Mode',

    ('OrthoEditProfile', 'selectionMode')  : 'Selection mode',
    ('OrthoEditProfile', 'selectionSize')  : 'Selection size',
    ('OrthoEditProfile', 'selectionIs3D')  : '3D selection',
    ('OrthoEditProfile', 'fillValue')      : 'Fill value',
    ('OrthoEditProfile', 'intensityThres') : 'Intensity threshold',
    ('OrthoEditProfile', 'localFill')      : 'Only select adjacent voxels',
    ('OrthoEditProfile', 'searchRadius')   : 'Limit search to radius (mm)',
})
