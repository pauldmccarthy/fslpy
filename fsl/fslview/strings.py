#!/usr/bin/env python
#
# strings.py - Labels used throughout various parts of FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging

log = logging.getLogger(__name__)

import fsl.data.image as fslimage

"""Refactorings are afoot. One big dictionary where keys must be strings.

[className]
[className.propName]
[className.propName.optName]

[className.attName]

[actionClassName]
[className.actionName]

And a second dictionary for tooltips
"""

class _TypeDict(dict):
    def __getitem__(self, key):
        
        if isinstance(key, type):
            key = key.__name__
            
        return dict.__getitem__(self, key)


labels = _TypeDict({
    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'SpacePanel'      : 'Space inspector',

    'OpenFileAction'      : 'Add image file',
    'OpenStandardAction'  : 'Add standard',
    'LoadColourMapAction' : 'Load custom colour map'
})

try:
    
    locationPanelOutOfBounds = 'Out of bounds'
    locationPanelSpaceLabel  = '{} space'
    locationPanelWorldLabel  = 'World location (mm)'
    locationPanelVoxelLabel  = 'Voxel coordinates'
    locationPanelVolumeLabel = 'Volume (index)'

    
    from profiles.orthoviewprofile import OrthoViewProfile
    from profiles.orthoeditprofile import OrthoEditProfile

    profileModeTitles = {
        OrthoViewProfile : {
            'nav'  : 'Navigate',
            'pan'  : 'Pan',
            'zoom' : 'Zoom'},

        OrthoEditProfile : {
            'nav'    : 'Navigate',
            'pan'    : 'Pan',
            'zoom'   : 'Zoom',
            'sel'    : 'Select',
            'desel'  : 'Deselect',
            'selint' : 'Select by intensity'}
    }

    
except Exception as e:
    log.warn('Error importing modules for strings: {}'.format(e))


imageAxisLowLongLabels = {
    fslimage.ORIENT_A2P     : 'Anterior',
    fslimage.ORIENT_P2A     : 'Posterior',
    fslimage.ORIENT_L2R     : 'Left',
    fslimage.ORIENT_R2L     : 'Right',
    fslimage.ORIENT_I2S     : 'Inferior',
    fslimage.ORIENT_S2I     : 'Superior',
    fslimage.ORIENT_UNKNOWN : 'Unknown'}

imageAxisHighLongLabels = {
    fslimage.ORIENT_A2P     : 'Posterior',
    fslimage.ORIENT_P2A     : 'Anterior',
    fslimage.ORIENT_L2R     : 'Right',
    fslimage.ORIENT_R2L     : 'Left',
    fslimage.ORIENT_I2S     : 'Superior',
    fslimage.ORIENT_S2I     : 'Inferior',
    fslimage.ORIENT_UNKNOWN : 'Unknown'}

imageAxisLowShortLabels = {
    fslimage.ORIENT_A2P     : 'A',
    fslimage.ORIENT_P2A     : 'P',
    fslimage.ORIENT_L2R     : 'L',
    fslimage.ORIENT_R2L     : 'R',
    fslimage.ORIENT_I2S     : 'I',
    fslimage.ORIENT_S2I     : 'S',
    fslimage.ORIENT_UNKNOWN : '?'}

imageAxisHighShortLabels = {
    fslimage.ORIENT_A2P     : 'P',
    fslimage.ORIENT_P2A     : 'A',
    fslimage.ORIENT_L2R     : 'R',
    fslimage.ORIENT_R2L     : 'L',
    fslimage.ORIENT_I2S     : 'S',
    fslimage.ORIENT_S2I     : 'I',
    fslimage.ORIENT_UNKNOWN : '?'}

imageSpaceLabels = {
    fslimage.NIFTI_XFORM_UNKNOWN      : 'Unknown',
    fslimage.NIFTI_XFORM_SCANNER_ANAT : 'Scanner anatomical',
    fslimage.NIFTI_XFORM_ALIGNED_ANAT : 'Aligned anatomical',
    fslimage.NIFTI_XFORM_TALAIRACH    : 'Talairach', 
    fslimage.NIFTI_XFORM_MNI_152      : 'MNI152'}
