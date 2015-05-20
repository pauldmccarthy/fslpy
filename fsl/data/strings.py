#!/usr/bin/env python
#
# strings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from fsl.utils.typedict import TypeDict
import fsl.data.constants as constants

messages = TypeDict({

    'fslview.loading'              : 'Loading {} ...',
    'FSLViewSplash.default'        : 'Loading ...',

    'imageio.saveImage.error'      : 'An error occurred saving the file. '
                                     'Details: {}',
    'imageio.loadImage.decompress' : '{} is a large file ({} MB) - '
                                     'decompressing to {}, to allow memory '
                                     'mapping...',

    'imageio.loadImages.loading' : 'Loading {} ...',
    'imageio.loadImages.error'   : 'An error occurred loading the image {}\n\n'
                                   'Details: {}',

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

    'AtlasInfoPanel.nonVolumetric' : 'Atlas lookup can only be performed on '
                                     'volumetric images',

    'AtlasInfoPanel.chooseAnAtlas' : 'Choose an atlas!',
    'AtlasInfoPanel.atlasDisabled' : 'Atlases are not available',

    'CanvasPanel.screenshot'            : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved'   : 'Overlay {} needs saving before a '
                                          'screenshot can be taken.',
    'CanvasPanel.screenshot.pleaseWait' : 'Saving screenshot - '
                                          'please wait ...',
    'CanvasPanel.screenshot.error'      : 'Sorry, there was an error '
                                          'saving the screenshot. Try '
                                          'calling render directly with '
                                          'this command: \n{}',
})



titles = TypeDict({
    'imageio.saveImage.dialog' : 'Save image file',
    'imageio.addImages.dialog' : 'Open image files',
    
    'imageio.loadImages.error'  : 'Error loading image',

    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'HistogramPanel'  : 'Histogram',
    'SpacePanel'      : 'Space inspector',

    'CanvasPanel.screenshot'          : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved' : 'Save overlay before continuing',
    'CanvasPanel.screenshot.error'    : 'Error saving screenshot',

    'AtlasInfoPanel'      : 'Atlas information',
    'AtlasOverlayPanel'   : 'Atlas overlays',

    'OverlayListPanel'      : 'Overlay list',
    'AtlasPanel'            : 'Atlases',
    'LocationPanel'         : 'Location',
    'OverlayDisplayToolBar' : 'Display toolbar',
    'OverlayDisplayPanel'   : 'Display settings',
    'OrthoToolBar'          : 'Ortho view toolbar',
    'OrthoProfileToolBar'   : 'Ortho view mode toolbar',
    'OrthoSettingsPanel'    : 'Ortho view settings',
    'LightBoxToolBar'       : 'Lightbox view toolbar',
    'LightBoxSettingsPanel' : 'Lightbox view settings',
    'HistogramToolBar'      : 'Histogram settings', 
})


actions = TypeDict({

    'OpenFileAction'      : 'Add overlay file',
    'OpenStandardAction'  : 'Add standard',
    'CopyOverlayAction'   : 'Copy overlay',
    'SaveOverlayAction'   : 'Save overlay',
    'LoadColourMapAction' : 'Load custom colour map',

    'CanvasPanel.screenshot'              : 'Take screenshot',
    'CanvasPanel.toggleColourBar'         : 'Colour bar',
    'CanvasPanel.toggleOverlayList'       : 'Overlay list',
    'CanvasPanel.toggleDisplayProperties' : 'Overlay display properties',
    'CanvasPanel.toggleLocationPanel'     : 'Location panel',
    'CanvasPanel.toggleAtlasPanel'        : 'Atlas panel',
    
    'OrthoPanel.toggleOrthoToolBar'     : 'View properties',
    'OrthoPanel.toggleProfileToolBar'   : 'Mode controls',

    'OrthoToolBar.more'           : 'More settings',
    'LightBoxToolBar.more'        : 'More settings',
    'OverlayDisplayToolBar.more'  : 'More settings',
    
    'LightBoxPanel.toggleLightBoxToolBar' : 'View properties',


    'PlotPanel.screenshot' : 'Take screenshot',

    'HistogramPanel.toggleToolbar' : 'Histogram controls',


    'OrthoViewProfile.centreCursor' : 'Centre cursor',
    'OrthoViewProfile.resetZoom'    : 'Reset zoom',


    'OrthoEditProfile.undo'                    : 'Undo',
    'OrthoEditProfile.redo'                    : 'Redo',
    'OrthoEditProfile.fillSelection'           : 'Fill',
    'OrthoEditProfile.clearSelection'          : 'Clear',
    'OrthoEditProfile.createMaskFromSelection' : 'Mask',
    'OrthoEditProfile.createROIFromSelection'  : 'ROI',
})

labels = TypeDict({
    'LocationPanel.worldLocation'         : 'Coordinates: ',
    'LocationPanel.worldLocation.unknown' : 'Unknown',
    'LocationPanel.voxelLocation'         : 'Voxel location',
    'LocationPanel.volume'                : 'Volume',

    'CanvasPanel.screenshot.notSaved.save'   : 'Save overlay now',
    'CanvasPanel.screenshot.notSaved.skip'   : 'Skip overlay (will not appear '
                                               'in screenshot)',
    'CanvasPanel.screenshot.notSaved.cancel' : 'Cancel screenshot',
})


properties = TypeDict({
    
    'Profile.mode' : 'Profile',

    'CanvasPanel.syncLocation'       : 'Sync location',
    'CanvasPanel.syncOverlayOrder'   : 'Sync overlay order',
    'CanvasPanel.syncVolume'         : 'Sync volume',
    'CanvasPanel.profile'            : 'Mode',

    'SceneOpts.showCursor'         : 'Show location cursor',
    'SceneOpts.showColourBar'      : 'Show colour bar',
    'SceneOpts.performance'        : 'Rendering performance',
    'SceneOpts.zoom'               : 'Zoom',
    'SceneOpts.colourBarLocation'  : 'Colour bar location',
    'SceneOpts.colourBarLabelSide' : 'Colour bar label side',

    'LightBoxOpts.zax'            : 'Z axis',
    'LightBoxOpts.highlightSlice' : 'Highlight slice',
    'LightBoxOpts.showGridLines'  : 'Show grid lines',
    'LightBoxOpts.sliceSpacing'   : 'Slice spacing',
    'LightBoxOpts.zrange'         : 'Z range',

    'OrthoOpts.showXCanvas' : 'Show X canvas',
    'OrthoOpts.showYCanvas' : 'Show Y canvas',
    'OrthoOpts.showZCanvas' : 'Show Z canvas',
    'OrthoOpts.showLabels'  : 'Show labels',
    'OrthoOpts.layout'      : 'Layout',
    'OrthoOpts.xzoom'       : 'X zoom',
    'OrthoOpts.yzoom'       : 'Y zoom',
    'OrthoOpts.zzoom'       : 'Z zoom',

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
    
    'Display.name'              : 'Overlay name',
    'Display.overlayType'       : 'Overlay data type',
    'Display.enabled'           : 'Enabled',
    'Display.alpha'             : 'Opacity',
    'Display.brightness'        : 'Brightness',
    'Display.contrast'          : 'Contrast',
    'Display.interpolation'     : 'Interpolation',

    'ImageOpts.resolution' : 'Resolution',
    'ImageOpts.transform'  : 'Image transform',
    'ImageOpts.volume'     : 'Volume',
    
    'VolumeOpts.displayRange'  : 'Display range',
    'VolumeOpts.clippingRange' : 'Clipping range',
    'VolumeOpts.cmap'          : 'Colour map',
    'VolumeOpts.invert'        : 'Invert colour map',

    'MaskOpts.colour'         : 'Colour',
    'MaskOpts.invert'         : 'Invert',
    'MaskOpts.threshold'      : 'Threshold',

    'VectorOpts.xColour'       : 'X Colour',
    'VectorOpts.yColour'       : 'Y Colour',
    'VectorOpts.zColour'       : 'Z Colour',

    'VectorOpts.suppressX'     : 'Suppress X value',
    'VectorOpts.suppressY'     : 'Suppress Y value',
    'VectorOpts.suppressZ'     : 'Suppress Z value',
    'VectorOpts.modulate'      : 'Modulate by',
    'VectorOpts.modThreshold'  : 'Modulation threshold',

    'LineVectorOpts.directed'  : 'Interpret vectors as directed',
    'LineVectorOpts.lineWidth' : 'Line width',

    'ModelOpts.colour'     : 'Colour',
    'ModelOpts.outline'    : 'Show outline only',
    'ModelOpts.refImage'   : 'Reference image',
    'ModelOpts.coordSpace' : 'Model coordinate space',
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

    'SceneOpts.colourBarLocation.top'    : 'Top',
    'SceneOpts.colourBarLocation.bottom' : 'Bottom',
    'SceneOpts.colourBarLocation.left'   : 'Left',
    'SceneOpts.colourBarLocation.right'  : 'Right',

    'SceneOpts.performance.1' : 'Fastest',
    'SceneOpts.performance.2' : 'Faster',
    'SceneOpts.performance.3' : 'Good looking',
    'SceneOpts.performance.4' : 'Better looking',
    'SceneOpts.performance.5' : 'Best looking',

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

    'ImageOpts.transform.affine' : 'Use qform/sform transformation matrix',
    'ImageOpts.transform.pixdim' : 'Use pixdims only',
    'ImageOpts.transform.id'     : 'Do not use qform/sform or pixdims',

    'ModelOpts.refImage.none' : 'None',

    'Display.interpolation.none'   : 'No interpolation', 
    'Display.interpolation.linear' : 'Linear interpolation', 
    'Display.interpolation.spline' : 'Spline interpolation',

    'Display.overlayType.volume'     : '3D/4D volume',
    'Display.overlayType.mask'       : '3D/4D mask image',
    'Display.overlayType.rgbvector'  : '3-direction vector image (RGB)',
    'Display.overlayType.linevector' : '3-direction vector image (Line)',
    'Display.overlayType.model'      : '3D model' 
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
