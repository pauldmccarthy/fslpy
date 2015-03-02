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

    'actions.loadcolourmap.loadcmap'    : 'Open colour map file',
    'actions.loadcolourmap.namecmap'    : 'Enter a name for the colour map - '
                                          'please use only letters, numbers, '
                                          'and underscores.',
    'actions.loadcolourmap.installcmap' : 'Do you want to install '
                                          'this colour map permanently?',
    'actions.loadcolourmap.alreadyinstalled' : 'A colour map with that name '
                                               'already exists - choose a '
                                               'different name.',
    'actions.loadcolourmap.invalidname'      : 'Please use only letters, '
                                               'numbers, and underscores.',
    'actions.loadcolourmap.installerror'     : 'An error occurred while '
                                               'installing the colour map',

    'AtlasInfoPanel.notMNISpace'   : 'Atlas lookup can only be performed on '
                                     'images registered to MNI152 space',

    'AtlasInfoPanel.chooseAnAtlas' : 'Choose an atlas!'
})



titles = TypeDict({
    'imageio.saveImage.dialog' : 'Save image file',
    'imageio.addImages.dialog' : 'Open image files',

    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'HistogramPanel'  : 'Histogram',
    'SpacePanel'      : 'Space inspector', 

    'AtlasInfoPanel'      : 'Atlas information',
    'AtlasOverlayPanel'   : 'Atlas overlays',

    'ImageListPanel'        : 'Image list',
    'AtlasPanel'            : 'Atlases',
    'LocationPanel'         : 'Location',
    'ImageDisplayToolBar'   : 'Display toolbar',
    'ImageDisplayPanel'     : 'Display settings',
    'OrthoToolBar'          : 'Ortho view toolbar',
    'OrthoProfileToolBar'   : 'Ortho view profile toolbar',
    'OrthoSettingsPanel'    : 'Ortho view settings',
    'LightBoxToolBar'       : 'Lightbox view toolbar',
    'LightBoxSettingsPanel' : 'Lightbox view settings',
    'HistogramToolBar'      : 'Histogram settings', 
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
    'CanvasPanel.toggleAtlasPanel'        : 'Show/hide atlas panel',
    
    'OrthoPanel.toggleOrthoToolBar'     : 'Show/hide view properties',
    'OrthoPanel.toggleProfileToolBar'   : 'Show/hide view controls',

    'OrthoToolBar.more'           : 'More settings',
 

    'LightBoxPanel.toggleLightBoxToolBar' : 'Show/hide view controls',


    'PlotPanel.screenshot' : 'Take screenshot',

    'HistogramPanel.toggleToolbar' : 'Show/hide histogram controls',


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
    'LocationPanel.worldLocation' : 'World location (mm)',
    'LocationPanel.voxelLocation' : 'Voxel location',
    'LocationPanel.volume'        : 'Volume',
    'LocationPanel.space'         : 'Space',
    'LocationPanel.intensity'     : 'Intensity',
    'LocationPanel.outOfBounds'   : 'Out of bounds',

    'ImageDisplayToolBar.more'    : 'More settings',
    'LightBoxToolBar.more'        : 'More settings',
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

    'HistogramPanel.dataRange'  : 'Data range',
    'HistogramPanel.autoHist'   : 'Automatic histogram binning', 
    'HistogramPanel.nbins'      : 'Number of bins', 


    'OrthoEditProfile.selectionSize'          : 'Selection size',
    'OrthoEditProfile.selectionIs3D'          : '3D selection',
    'OrthoEditProfile.fillValue'              : 'Fill value',
    'OrthoEditProfile.intensityThres'         : 'Intensity threshold',
    'OrthoEditProfile.localFill'              : 'Only select adjacent voxels',
    'OrthoEditProfile.searchRadius'           : 'Limit search to radius (mm)',
    'OrthoEditProfile.selectionOverlayColour' : 'Selection overlay',
    'OrthoEditProfile.selectionCursorColour'  : 'Selection cursor',
    

    'Display.name'              : 'Image name',
    'Display.enabled'           : 'Enabled',
    'Display.alpha'             : 'Opacity',
    'Display.brightness'        : 'Brightness',
    'Display.contrast'          : 'Contrast',
    'Display.interpolation'     : 'Interpolation',
    'Display.resolution'        : 'Resolution',
    'Display.volume'            : 'Volume',
    'Display.syncVolume'        : 'Synchronise volume',
    'Display.transform'         : 'Image transform',
    'Display.imageType'         : 'Image data type',
    
    'VolumeOpts.displayRange' : 'Display range',
    'VolumeOpts.clipLow'      : 'Low clipping',
    'VolumeOpts.clipHigh'     : 'High clipping',
    'VolumeOpts.cmap'         : 'Colour map',

    'MaskOpts.colour'         : 'Colour',
    'MaskOpts.invert'         : 'Invert',
    'MaskOpts.threshold'      : 'Threshold',

    'VectorOpts.displayMode'   : 'Display mode',
    'VectorOpts.xColour'       : 'X Colour',
    'VectorOpts.yColour'       : 'Y Colour',
    'VectorOpts.zColour'       : 'Z Colour',

    'VectorOpts.suppressX'     : 'Suppress X value',
    'VectorOpts.suppressY'     : 'Suppress Y value',
    'VectorOpts.suppressZ'     : 'Suppress Z value',
    'VectorOpts.modulate'      : 'Modulate by',
    'VectorOpts.modThreshold'  : 'Modulation threshold',
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


    ('LightBoxViewProfile', 'view')   : 'View',
    ('LightBoxViewProfile', 'zoom')   : 'Zoom',

})



choices = TypeDict({

    'CanvasPanel.colourBarLocation.top'    : 'Top',
    'CanvasPanel.colourBarLocation.bottom' : 'Bottom',
    'CanvasPanel.colourBarLocation.left'   : 'Left',
    'CanvasPanel.colourBarLocation.right'  : 'Right',

    'HistogramPanel.dataRange.min' : 'Min.',
    'HistogramPanel.dataRange.max' : 'Max.',
    
    'ColourBarCanvas.orientation.horizontal' : 'Horizontal',
    'ColourBarCanvas.orientation.vertical'   : 'Vertical',
    
    'ColourBarCanvas.labelSide.top-left'     : 'Top / Left',
    'ColourBarCanvas.labelSide.bottom-right' : 'Bottom / Right', 

    'VolumeOpts.displayRange.min' : 'Min.',
    'VolumeOpts.displayRange.max' : 'Max.',

    'VectorOpts.displayType.line' : 'Lines',
    'VectorOpts.displayType.rgb'  : 'RGB',

    'VectorOpts.modulate.none'    : 'No modulation',
    
    'Display.transform.affine' : 'Use qform/sform transformation matrix',
    'Display.transform.pixdim' : 'Use pixdims only',
    'Display.transform.id'     : 'Do not use qform/sform or pixdims',

    'Display.interpolation.none'   : 'No interpolation', 
    'Display.interpolation.linear' : 'Linear interpolation', 
    'Display.interpolation.spline' : 'Spline interpolation', 
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
    ('Image', 'space',     constants.NIFTI_XFORM_SCANNER_ANAT) : 'Scanner '
                                                                 'anatomical',
    ('Image', 'space',     constants.NIFTI_XFORM_ALIGNED_ANAT) : 'Aligned '
                                                                 'anatomical',
    ('Image', 'space',     constants.NIFTI_XFORM_TALAIRACH)    : 'Talairach', 
    ('Image', 'space',     constants.NIFTI_XFORM_MNI_152)      : 'MNI152',
})
