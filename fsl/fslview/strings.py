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
[className, propName]
[className, propName, optName]

[className, attName]

[actionClassName]
[className, actionName]

And a second dictionary for tooltips
"""


class _TypeDict(dict):
    """A custom dictionary which allows classes or class instances to be used
    as keys for value lookups, but internally transforms any class/instance
    keys into strings. Tuple keys are supported. Value assignment with
    class/instance keys is not supported.

    If a class/instance is passed in as a key, and there is no value
    associated with that class, a search is performed on all of the base
    classes of that class to see if any values are present for them.
    """
    
    def __getitem__(self, key):
        
        origKey = key
        bases   = []

        # Make the code a bit easier by
        # treating non-tuple keys as tuples
        if not isinstance(key, tuple):
            key = tuple([key])

        newKey = []

        # Transform any class/instance elements into
        # their string representation (the class name)
        for elem in key:
            
            if isinstance(elem, type):
                newKey.append(elem.__name__)
                bases .append(elem.__bases__)
                
            elif not isinstance(elem, str):
                newKey.append(elem.__class__.__name__)
                bases .append(elem.__class__.__bases__)
                
            else:
                newKey.append(elem)
                bases .append(None)

        key = newKey
            
        while True:

            # If the key was not a tuple turn
            # it back into a single element key
            # for the lookup
            if len(key) == 1: lKey = key[0]
            else:             lKey = tuple(key)

            val = dict.get(self, lKey, None)
            
            if val is not None:
                return val

            # No more base classes to search for - there
            # really is no value associated with this key
            elif all([b is None for b in bases]):
                raise KeyError(key)

            # Search through the base classes to see
            # if a value is present for one of them
            for i, (elem, elemBases) in enumerate(zip(key, bases)):
                if elemBases is None:
                    continue

                # test each of the base classes 
                # of the current tuple element
                for elemBase in elemBases:

                    newKey    = list(key)
                    newKey[i] = elemBase.__name__

                    try:             return self.__getitem__(tuple(newKey))
                    except KeyError: continue

            # No value for any base classes either
            raise KeyError(origKey)

        
labels = _TypeDict({
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
