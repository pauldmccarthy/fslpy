#!/usr/bin/env python
#
# strings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from fsl.utils.typedict import TypeDict
import fsl.data.constants as constants

messages = TypeDict({

    'imageio.saveImage.error'      : 'An error occurred saving the file. '
                                     'Details: {}',

    'imageio.loadImage.decompress' : '{} is a large file ({} MB) - '
                                     'decompressing to {}, to allow memory '
                                     'mapping...',
})



titles = TypeDict({
    'imageio.saveImage.dialog' : 'Save image file',
    'imageio.addImages.dialog' : 'Open image files',

    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'SpacePanel'      : 'Space inspector', 

})


actions = TypeDict({

    'OpenFileAction'      : 'Add image file',
    'OpenStandardAction'  : 'Add standard',
    'CopyImageAction'     : 'Copy image',
    'SaveImageAction'     : 'Save image',
    'LoadColourMapAction' : 'Load custom colour map',

    'CanvasPanel.screenshot'              : 'Take screenshot',
    'CanvasPanel.toggleColourBar'         : 'Show/hide colour bar',
    'CanvasPanel.toggleImageList'         : 'Show/hide image list',
    'CanvasPanel.toggleDisplayProperties' : 'Show/hide display properties',
    'CanvasPanel.toggleLocationPanel'     : 'Show/hide location panel',
    'CanvasPanel.toggleCanvasProperties'  : 'Show/hide canvas properties',


    'OrthoViewProfile.centreCursor' : 'Centre cursor',
    'OrthoViewProfile.resetZoom'    : 'Reset zoom',


    'OrthoEditProfile.undo'                    : 'Undo',
    'OrthoEditProfile.redo'                    : 'Redo',
    'OrthoEditProfile.fillSelection'           : 'Fill selected region',
    'OrthoEditProfile.clearSelection'          : 'Clear selection',
    'OrthoEditProfile.createMaskFromSelection' : 'Create mask from '
                                                 'selected region',
    'OrthoEditProfile.createROIFromSelection'  : 'Create ROI from ' 
                                                 'selected region',
})

labels = TypeDict({
    'LocationPanel.worldLabel'  : 'World location (mm)',
    'LocationPanel.voxelLabel'  : 'Voxel location',
    'LocationPanel.volumeLabel' : 'Volume',
    'LocationPanel.spaceLabel'  : 'Space',
    'LocationPanel.outOfBounds' : 'Out of bounds',
})


properties = TypeDict({
    
    'Profile.mode' : 'Mode',

    'CanvasPanel.showCursor'         : 'Show location cursor',
    'CanvasPanel.syncLocation'       : 'Sync location',
    'CanvasPanel.syncImageOrder'     : 'Sync image order',
    'CanvasPanel.syncVolume'         : 'Sync volume',
    'CanvasPanel.profile'            : 'Profile',
    'CanvasPanel.zoom'               : 'Zoom',
    'CanvasPanel.colourBarLocation'  : 'Colour bar location',
    'CanvasPanel.colourBarLabelSide' : 'Colour bar label side',

    'LightBoxPanel.zax'            : 'Z axis',
    'LightBoxPanel.highlightSlice' : 'Highlight slice',
    'LightBoxPanel.showGridLines'  : 'Show grid lines',
    'LightBoxPanel.sliceSpacing'   : 'Slice spacing',
    'LightBoxPanel.zrange'         : 'Z range',

    'OrthoPanel.showXCanvas' : 'Show X canvas',
    'OrthoPanel.showYCanvas' : 'Show Y canvas',
    'OrthoPanel.showZCanvas' : 'Show Z canvas',
    'OrthoPanel.showLabels'  : 'Show labels',
    'OrthoPanel.layout'      : 'Layout',
    'OrthoPanel.xzoom'       : 'X zoom',
    'OrthoPanel.yzoom'       : 'Y zoom',
    'OrthoPanel.zzoom'       : 'Z zoom',


    'OrthoEditProfile.selectionMode'  : 'Selection mode',
    'OrthoEditProfile.selectionSize'  : 'Selection size',
    'OrthoEditProfile.selectionIs3D'  : '3D selection',
    'OrthoEditProfile.fillValue'      : 'Fill value',
    'OrthoEditProfile.intensityThres' : 'Intensity threshold',
    'OrthoEditProfile.localFill'      : 'Only select adjacent voxels',
    'OrthoEditProfile.searchRadius'   : 'Limit search to radius (mm)',


    'ImageDisplay.name'           : 'Image name',
    'ImageDisplay.enabled'        : 'Enabled',
    'ImageDisplay.displayRange'   : 'Display range',
    'ImageDisplay.alpha'          : 'Opacity',
    'ImageDisplay.clipLow'        : 'Low clipping',
    'ImageDisplay.clipHigh'       : 'High clipping',
    'ImageDisplay.interpolation'  : 'Interpolation',
    'ImageDisplay.resolution'     : 'Resolution',
    'ImageDisplay.volume'         : 'Volume',
    'ImageDisplay.syncVolume'     : 'Synchronise volume',
    'ImageDisplay.transform'      : 'Image transform',
    'ImageDisplay.imageType'      : 'Image data type',
    'ImageDisplay.cmap'           : 'Colour map',
})


profiles = TypeDict({
    'CanvasPanel.view' : 'View',
    'OrthoPanel.edit'  : 'Edit',
})

modes = TypeDict({
    ('OrthoViewProfile', 'nav')    : 'Navigate',
    ('OrthoViewProfile', 'pan')    : 'Pan',
    ('OrthoViewProfile', 'zoom')   : 'Zoom',

    ('OrthoEditProfile', 'nav')    : 'Navigate',
    ('OrthoEditProfile', 'pan')    : 'Pan',
    ('OrthoEditProfile', 'zoom')   : 'Zoom',
    ('OrthoEditProfile', 'sel')    : 'Select',
    ('OrthoEditProfile', 'desel')  : 'Deselect',
    ('OrthoEditProfile', 'selint') : 'Select by intensity',

})



choices = TypeDict({

    'CanvasPanel.colourBarLocation.top'    : 'Top',
    'CanvasPanel.colourBarLocation.bottom' : 'Bottom',
    'CanvasPanel.colourBarLocation.left'   : 'Left',
    'CanvasPanel.colourBarLocation.right'  : 'Right',
    
    'ColourBarCanvas.orientation.horizontal' : 'Horizontal',
    'ColourBarCanvas.orientation.vertical'   : 'Vertical',
    
    'ColourBarCanvas.labelSide.top-left'     : 'Top / Left',
    'ColourBarCanvas.labelSide.bottom-right' : 'Bottom / Right', 

    'ImageDisplay.displayRange.min' : 'Min.',
    'ImageDisplay.displayRange.max' : 'Max.',
    
    'ImageDisplay.transform.affine' : 'Use qform/sform transformation matrix',
    'ImageDisplay.transform.pixdim' : 'Use pixdims only',
    'ImageDisplay.transform.id'     : 'Do not use qform/sform or pixdims',

    'ImageDisplay.interpolation.none'   : 'No interpolation', 
    'ImageDisplay.interpolation.linear' : 'Linear interpolation', 
    'ImageDisplay.interpolation.spline' : 'Spline interpolation', 
})


anatomy = TypeDict({

    ('Image', 'lowlong',   constants.ORIENT_A2P)               : 'Anterior',
    ('Image', 'lowlong',   constants.ORIENT_P2A)               : 'Posterior',
    ('Image', 'lowlong',   constants.ORIENT_L2R)               : 'Left',
    ('Image', 'lowlong',   constants.ORIENT_R2L)               : 'Right',
    ('Image', 'lowlong',   constants.ORIENT_I2S)               : 'Inferior',
    ('Image', 'lowlong',   constants.ORIENT_S2I)               : 'Superior',
    ('Image', 'lowlong',   constants.ORIENT_UNKNOWN)           : 'Unknown',
    ('Image', 'highlong',  constants.ORIENT_A2P)               : 'Posterior',
    ('Image', 'highlong',  constants.ORIENT_P2A)               : 'Anterior',
    ('Image', 'highlong',  constants.ORIENT_L2R)               : 'Right',
    ('Image', 'highlong',  constants.ORIENT_R2L)               : 'Left',
    ('Image', 'highlong',  constants.ORIENT_I2S)               : 'Superior',
    ('Image', 'highlong',  constants.ORIENT_S2I)               : 'Inferior',
    ('Image', 'highlong',  constants.ORIENT_UNKNOWN)           : 'Unknown',
    ('Image', 'lowshort',  constants.ORIENT_A2P)               : 'A',
    ('Image', 'lowshort',  constants.ORIENT_P2A)               : 'P',
    ('Image', 'lowshort',  constants.ORIENT_L2R)               : 'L',
    ('Image', 'lowshort',  constants.ORIENT_R2L)               : 'R',
    ('Image', 'lowshort',  constants.ORIENT_I2S)               : 'I',
    ('Image', 'lowshort',  constants.ORIENT_S2I)               : 'S',
    ('Image', 'lowshort',  constants.ORIENT_UNKNOWN)           : '?',
    ('Image', 'highshort', constants.ORIENT_A2P)               : 'P',
    ('Image', 'highshort', constants.ORIENT_P2A)               : 'A',
    ('Image', 'highshort', constants.ORIENT_L2R)               : 'R',
    ('Image', 'highshort', constants.ORIENT_R2L)               : 'L',
    ('Image', 'highshort', constants.ORIENT_I2S)               : 'S',
    ('Image', 'highshort', constants.ORIENT_S2I)               : 'I',
    ('Image', 'highshort', constants.ORIENT_UNKNOWN)           : '?',
    ('Image', 'space',     constants.NIFTI_XFORM_UNKNOWN)      : 'Unknown',
    ('Image', 'space',     constants.NIFTI_XFORM_SCANNER_ANAT) : 'Scanner anatomical',
    ('Image', 'space',     constants.NIFTI_XFORM_ALIGNED_ANAT) : 'Aligned anatomical',
    ('Image', 'space',     constants.NIFTI_XFORM_TALAIRACH)    : 'Talairach', 
    ('Image', 'space',     constants.NIFTI_XFORM_MNI_152)      : 'MNI152',
})