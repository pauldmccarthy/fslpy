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
                
            elif not isinstance(elem, (str, int)):
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
})

try:
    


    
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
