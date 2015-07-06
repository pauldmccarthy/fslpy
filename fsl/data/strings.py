#!/usr/bin/env python
#
# strings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from fsl.utils.typedict import TypeDict
import fsl.data.constants as constants

messages = TypeDict({

    'fslview.loading'              : 'Loading {}',
    'FSLViewSplash.default'        : 'Loading ...',

    'image.saveImage.error'      : 'An error occurred saving the file. '
                                   'Details: {}',
    
    'image.loadImage.decompress' : '{} is a large file ({} MB) - '
                                   'decompressing to {}, to allow memory '
                                   'mapping...',

    'ProcessingDialog.error' : 'An error has occurred: {}'
                               '\n\nDetails: {}',

    'overlay.loadOverlays.loading'     : 'Loading {} ...',
    'overlay.loadOverlays.error'       : 'An error occurred loading the image '
                                         '{}\n\nDetails: {}',

    'overlay.loadOverlays.unknownType' : 'Unknown data type',

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
                                     'images oriented to MNI152 space',

    'AtlasInfoPanel.noReference' : 'No reference image available',

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

    'PlotPanel.screenshot'              : 'Save screenshot',

    'PlotPanel.screenshot.error'       : 'An error occurred while saving the '
                                         'screenshot.\n\n'
                                         'Details: {}',

    'HistogramPanel.calcHist'           : 'Calculating histogram for {} ...',


    'LookupTablePanel.notLutOverlay' : 'Choose an overlay which '
                                       'uses a lookup table',

    'LookupTablePanel.labelExists' : 'The {} LUT already contains a '
                                     'label with value {}',

    'NewLutDialog.newLut' : 'Enter a name for the new LUT', 
    
})



titles = TypeDict({
    'image.saveImage.dialog' : 'Save image file',

    'ProcessingDialog.error' : 'Error',
    
    'overlay.addOverlays.dialog' : 'Open overlay files',
    
    'overlay.loadOverlays.error'  : 'Error loading overlay',

    'OrthoPanel'      : 'Ortho View',
    'LightBoxPanel'   : 'Lightbox View',
    'TimeSeriesPanel' : 'Time series',
    'HistogramPanel'  : 'Histogram',
    'SpacePanel'      : 'Space inspector',

    'CanvasPanel.screenshot'          : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved' : 'Save overlay before continuing',
    'CanvasPanel.screenshot.error'    : 'Error saving screenshot',

    'PlotPanel.screenshot.error'      : 'Error saving screenshot',

    'AtlasInfoPanel'      : 'Atlas information',
    'AtlasOverlayPanel'   : 'Atlas overlays',

    'OverlayListPanel'       : 'Overlay list',
    'AtlasPanel'             : 'Atlases',
    'LocationPanel'          : 'Location',
    'OverlayDisplayToolBar'  : 'Display toolbar',
    'OverlayDisplayPanel'    : 'Display settings',
    'OrthoToolBar'           : 'Ortho view toolbar',
    'OrthoProfileToolBar'    : 'Ortho view mode toolbar',
    'OrthoSettingsPanel'     : 'Ortho view settings',
    'LightBoxToolBar'        : 'Lightbox view toolbar',
    'LightBoxSettingsPanel'  : 'Lightbox view settings',
    'LookupTablePanel'       : 'Lookup tables',
    'LutLabelDialog'         : 'New LUT label',
    'NewLutDialog'           : 'New LUT',
    'TimeSeriesListPanel'    : 'Time series list',
    'TimeSeriesControlPanel' : 'Time series control',
    'HistogramListPanel'     : 'Histogram list',
    'HistogramControlPanel'  : 'Histogram control',

    'LookupTablePanel.loadLut'     : 'Select a lookup table file',
    'LookupTablePanel.labelExists' : 'Label already exists',
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
    'CanvasPanel.toggleLookupTablePanel'  : 'Lookup tables',
    
    'OrthoPanel.toggleOrthoToolBar'     : 'View properties',
    'OrthoPanel.toggleProfileToolBar'   : 'Mode controls',

    'OrthoToolBar.more'           : 'More settings',
    'LightBoxToolBar.more'        : 'More settings',
    'OverlayDisplayToolBar.more'  : 'More settings',
    
    'LightBoxPanel.toggleLightBoxToolBar' : 'View properties',

    'PlotPanel.screenshot'                    : 'Take screenshot',
    'TimeSeriesPanel.toggleTimeSeriesList'    : 'Time series list',
    'TimeSeriesPanel.toggleTimeSeriesControl' : 'Time series control', 
    'HistogramPanel.toggleHistogramList'      : 'Histogram list',
    'HistogramPanel.toggleHistogramControl'   : 'Histogram control', 

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
    'LocationPanel.noData'                : 'No data',
    'LocationPanel.outOfBounds'           : 'Out of bounds',
    'LocationPanel.notAvailable'          : 'N/A',

    'CanvasPanel.screenshot.notSaved.save'   : 'Save overlay now',
    'CanvasPanel.screenshot.notSaved.skip'   : 'Skip overlay (will not appear '
                                               'in screenshot)',
    'CanvasPanel.screenshot.notSaved.cancel' : 'Cancel screenshot',


    'LookupTablePanel.addLabel' : 'Add label',
    'LookupTablePanel.newLut'   : 'New',
    'LookupTablePanel.copyLut'  : 'Copy',
    'LookupTablePanel.saveLut'  : 'Save',
    'LookupTablePanel.loadLut'  : 'Load',

    'LutLabelDialog.value'    : 'Value',
    'LutLabelDialog.name'     : 'Name',
    'LutLabelDialog.colour'   : 'Colour',
    'LutLabelDialog.ok'       : 'Ok',
    'LutLabelDialog.cancel'   : 'Cancel',
    'LutLabelDialog.newLabel' : 'New label',

    'NewLutDialog.ok'     : 'Ok',
    'NewLutDialog.cancel' : 'Cancel',
    'NewLutDialog.newLut' : 'New LUT',

    'PlotPanel.plotSettings'    : 'General plot settings',
    'PlotPanel.currentSettings' : 'Settings for currently '
                                              'selected plot ({})',
    'PlotPanel.xlim'            : 'X limits',
    'PlotPanel.ylim'            : 'Y limits',
    'PlotPanel.labels'          : 'Labels',
    'PlotPanel.xlabel'          : 'X',
    'PlotPanel.ylabel'          : 'Y',
    
})


properties = TypeDict({
    
    'Profile.mode' : 'Profile',

    'CanvasPanel.syncLocation'     : 'Sync location',
    'CanvasPanel.syncOverlayOrder' : 'Sync overlay order',
    'CanvasPanel.profile'          : 'Mode',

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

    'PlotPanel.legend'    : 'Show legend',
    'PlotPanel.ticks'     : 'Show ticks',
    'PlotPanel.grid'      : 'Show grid',
    'PlotPanel.smooth'    : 'Smooth',
    'PlotPanel.autoScale' : 'Auto-scale',
    'PlotPanel.xLogScale' : 'Log scale (x axis)',
    'PlotPanel.yLogScale' : 'Log scale (y axis)',
    'PlotPanel.xlabel'    : 'X label',
    'PlotPanel.ylabel'    : 'Y label',
    
    'TimeSeriesPanel.demean'           : 'Demean',
    'TimeSeriesPanel.usePixdim'        : 'Use pixdims',
    'TimeSeriesPanel.showCurrent'      : 'Plot time series for current voxel',
    'TimeSeriesPanel.plotFullModelFit' : 'Plot full model fit',
    'TimeSeriesPanel.plotResiduals'    : 'Plot residuals',
    
    'HistogramPanel.histType'    : 'Histogram type',
    'HistogramPanel.autoBin'     : 'Automatic histogram binning', 
    'HistogramPanel.showCurrent' : 'Plot histogram for current overlay',
    
    'HistogramSeries.nbins'           : 'Number of bins',
    'HistogramSeries.ignoreZeros'     : 'Ignore zeros',
    'HistogramSeries.includeOutliers' : 'Include values out of data range',
    'HistogramSeries.volume'          : 'Volume',
    'HistogramSeries.dataRange'       : 'Data range',
    'HistogramSeries.showOverlay'     : 'Show 3D histogram overlay',

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

    'ImageOpts.resolution' : 'Resolution',
    'ImageOpts.transform'  : 'Image transform',
    'ImageOpts.volume'     : 'Volume',
    
    'VolumeOpts.displayRange'  : 'Display range',
    'VolumeOpts.clippingRange' : 'Clipping range',
    'VolumeOpts.cmap'          : 'Colour map',
    'VolumeOpts.invert'        : 'Invert colour map',
    'VolumeOpts.interpolation' : 'Interpolation',

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

    'RGBVectorOpts.interpolation' : 'Interpolation',

    'LineVectorOpts.directed'  : 'Interpret vectors as directed',
    'LineVectorOpts.lineWidth' : 'Line width',

    'ModelOpts.colour'     : 'Colour',
    'ModelOpts.outline'    : 'Show outline only',
    'ModelOpts.refImage'   : 'Reference image',
    'ModelOpts.coordSpace' : 'Model coordinate space',
    'ModelOpts.showName'   : 'Show model name',

    'LabelOpts.lut'          : 'Look-up table',
    'LabelOpts.outline'      : 'Show outline only',
    'LabelOpts.outlineWidth' : 'Outline width',
    'LabelOpts.showNames'    : 'Show label names',
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

    'VolumeOpts.interpolation.none'   : 'No interpolation', 
    'VolumeOpts.interpolation.linear' : 'Linear interpolation', 
    'VolumeOpts.interpolation.spline' : 'Spline interpolation',

    'Display.overlayType.volume'     : '3D/4D volume',
    'Display.overlayType.mask'       : '3D/4D mask image',
    'Display.overlayType.label'      : 'Label image',
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
