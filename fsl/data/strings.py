#!/usr/bin/env python
#
# strings.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module contains a collection of strings used throughout ``fslpy`` for
display purposes. Most of the strings are used by FSLeyes.


The strings are stored in :class:`.TypeDict` dictionaries, roughly organised
into the following categories:


 ================== =====================================================
 :data:`messages`   Messages to be displayed to the user.
 :data:`titles`     Titles of windows, panels, and dialogs.
 :data:`actions`    Names of actions tied to menu options, buttons, etc.
 :data:`labels`     Labels for miscellaneous things.
 :data:`properties` Display names for ``props.HasProperties`` properties.
 :data:`choices`    Display names for ``props.HasProperties`` choice
                     properties.
 :data:`anatomy`    Anatomical and orientation labels.
 :data:`nifti`      Labels for NIFTI header fields.
 :data:`feat`       FEAT specific names and labels.
 ================== =====================================================
"""


from fsl.utils.typedict import TypeDict
import fsl.data.constants as constants


messages = TypeDict({

    'FSLDirDialog.FSLDirNotSet'    : 'The $FSLDIR environment variable '
                                     'is not set - \n{} may not behave '
                                     'correctly.',
    'FSLDirDialog.selectFSLDir'    : 'Select the directory in which '
                                     'FSL is installed',

    'fsleyes.loading'              : 'Loading {}',
    'FSLEyesSplash.default'        : 'Loading ...',

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

    'AtlasPanel.loadingAtlas' : 'Loading {} atlas ...',

    'AtlasOverlayPanel.loadRegions' : 'Loading region descriptions for {} ...',

    'AtlasInfoPanel.notMNISpace'   : 'The selected overlay does not appear to '
                                     'be in MNI152 space - atlas '
                                     'information might not be accurate!' ,

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

    'CanvasPanel.showCommandLineArgs.title'   : 'Scene parameters',
    'CanvasPanel.showCommandLineArgs.message' : 'Use these parameters on the '
                                                'command line to recreate '
                                                'the current scene',

    'PlotPanel.screenshot'              : 'Save screenshot',

    'PlotPanel.screenshot.error'       : 'An error occurred while saving the '
                                         'screenshot.\n\n'
                                         'Details: {}',

    'HistogramPanel.calcHist'           : 'Calculating histogram for {} ...',

    'LookupTablePanel.labelExists' : 'The {} LUT already contains a '
                                     'label with value {}',

    'NewLutDialog.newLut' : 'Enter a name for the new LUT',

    'ClusterPanel.noOverlays'     : 'Add a FEAT overlay',
    'ClusterPanel.notFEAT'        : 'Choose a FEAT overlay',
    'ClusterPanel.noClusters'     : 'No cluster results exist '
                                    'in this FEAT analysis',
    'ClusterPanel.badData'        : 'Cluster data could not be parsed - '
                                    'check your cluster_*.txt files.',
    'ClusterPanel.loadingCluster' : 'Loading data for cluster {} ...',

    'OrthoEditProfile.displaySpaceChange' : 'Setting {} as the display '
                                            'space reference image - this '
                                            'is necessary for editing.',


    'MelodicClassificationPanel.disabled' : 'Choose a melodic image.',

    'MelodicClassificationPanel.loadError' : 'An error occurred while loading '
                                             'the file {}.\n\nDetails: {}',
    'MelodicClassificationPanel.saveError' : 'An error occurred while saving '
                                             'the file {}.\n\nDetails: {}', 
})


titles = TypeDict({

    'FSLDirDialog'           : '$FSLDIR is not set',
    
    'image.saveImage.dialog' : 'Save image file',

    'ProcessingDialog.error' : 'Error',
    
    'overlay.addOverlays.dialog' : 'Open overlay files',
    
    'overlay.loadOverlays.error'  : 'Error loading overlay',

    'OrthoPanel'         : 'Ortho View',
    'LightBoxPanel'      : 'Lightbox View',
    'TimeSeriesPanel'    : 'Time series',
    'PowerSpectrumPanel' : 'Power spectra',
    'HistogramPanel'     : 'Histogram',

    'CanvasPanel.screenshot'          : 'Save screenshot',
    'CanvasPanel.screenshot.notSaved' : 'Save overlay before continuing',
    'CanvasPanel.screenshot.error'    : 'Error saving screenshot',

    'PlotPanel.screenshot.error'      : 'Error saving screenshot',

    'AtlasInfoPanel'      : 'Atlas information',
    'AtlasOverlayPanel'   : 'Atlas overlays',

    'OverlayListPanel'          : 'Overlay list',
    'AtlasPanel'                : 'Atlases',
    'LocationPanel'             : 'Location',
    'OverlayDisplayToolBar'     : 'Display toolbar',
    'CanvasSettingsPanel'       : 'View settings',
    'OverlayDisplayPanel'       : 'Display settings',
    'OrthoToolBar'              : 'Ortho view toolbar',
    'OrthoEditToolBar'          : 'Ortho view edit toolbar',
    'LightBoxToolBar'           : 'Lightbox view toolbar',
    'LookupTablePanel'          : 'Lookup tables',
    'LutLabelDialog'            : 'New LUT label',
    'NewLutDialog'              : 'New LUT',

    'PlotListPanel'             : 'Plot list',
    'TimeSeriesControlPanel'    : 'Time series control',
    'HistogramControlPanel'     : 'Histogram control',
    'PowerSpectrumControlPanel' : 'Power spectrum control',
    'ClusterPanel'              : 'Cluster browser',
    'OverlayInfoPanel'          : 'Overlay information',
    'ShellPanel'                : 'Python shell',

    'MelodicClassificationPanel' : 'Melodic IC classification',

    'LookupTablePanel.loadLut'     : 'Select a lookup table file',
    'LookupTablePanel.labelExists' : 'Label already exists',

    'MelodicClassificationPanel.loadDialog' : 'Load FIX/Melview file...',
    'MelodicClassificationPanel.saveDialog' : 'Save FIX/Melview file...',
    'MelodicClassificationPanel.loadError'  : 'Error loading FIX/Melview file',
    'MelodicClassificationPanel.saveError'  : 'Error saving FIX/Melview file',
})


actions = TypeDict({

    'OpenFileAction'        : 'Add overlay file',
    'OpenStandardAction'    : 'Add standard',
    'CopyOverlayAction'     : 'Copy overlay',
    'SaveOverlayAction'     : 'Save overlay',
    'LoadColourMapAction'   : 'Load custom colour map',
    'SavePerspectiveAction' : 'Save current perspective',

    'FSLEyesFrame.closeViewPanel' : 'Close',

    'CanvasPanel.screenshot'                : 'Take screenshot',
    'CanvasPanel.showCommandLineArgs'       : 'Show command line for scene',
    'CanvasPanel.toggleColourBar'           : 'Colour bar',
    'CanvasPanel.toggleOverlayList'         : 'Overlay list',
    'CanvasPanel.toggleDisplayProperties'   : 'Overlay display toolbar',
    'CanvasPanel.toggleLocationPanel'       : 'Location panel',
    'CanvasPanel.toggleAtlasPanel'          : 'Atlas panel',
    'CanvasPanel.toggleLookupTablePanel'    : 'Lookup tables',
    'CanvasPanel.toggleClusterPanel'        : 'Cluster browser',
    'CanvasPanel.toggleOverlayInfo'         : 'Overlay information',
    'CanvasPanel.toggleClassificationPanel' : 'Melodic IC classification',
    'CanvasPanel.toggleShell'               : 'Python shell',
    
    'OrthoPanel.toggleOrthoToolBar'     : 'Ortho toolbar',
    'OrthoPanel.toggleEditToolBar'      : 'Edit toolbar',

    'OrthoToolBar.showMoreSettings'          : 'More settings',
    'LightBoxToolBar.showMoreSettings'       : 'More settings',
    'OverlayDisplayToolBar.showMoreSettings' : 'More settings',
    
    'LightBoxPanel.toggleLightBoxToolBar' : 'Lightbox toolbar',

    'PlotPanel.screenshot'                          : 'Take screenshot',
    'TimeSeriesPanel.toggleTimeSeriesList'          : 'Time series list',
    'TimeSeriesPanel.toggleTimeSeriesControl'       : 'Time series control', 
    'HistogramPanel.toggleHistogramList'            : 'Histogram list',
    'HistogramPanel.toggleHistogramControl'         : 'Histogram control',
    'PowerSpectrumPanel.togglePowerSpectrumList'    : 'Power spectrum list',
    'PowerSpectrumPanel.togglePowerSpectrumControl' : 'Power spectrum '
                                                      'control', 

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

    'FSLDirDialog.locate' : 'Locate $FSLDIR',
    'FSLDirDialog.skip'   : 'Skip',
    
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


    'LookupTablePanel.addLabel'    : 'Add label',
    'LookupTablePanel.removeLabel' : 'Remove label',
    'LookupTablePanel.newLut'      : 'New LUT',
    'LookupTablePanel.copyLut'     : 'Copy LUT',
    'LookupTablePanel.saveLut'     : 'Save LUT',
    'LookupTablePanel.loadLut'     : 'Load LUT',

    'LutLabelDialog.value'    : 'Value',
    'LutLabelDialog.name'     : 'Name',
    'LutLabelDialog.colour'   : 'Colour',
    'LutLabelDialog.ok'       : 'Ok',
    'LutLabelDialog.cancel'   : 'Cancel',
    'LutLabelDialog.newLabel' : 'New label',

    'NewLutDialog.ok'     : 'Ok',
    'NewLutDialog.cancel' : 'Cancel',
    'NewLutDialog.newLut' : 'New LUT',


    'PlotControlPanel.plotSettings'       : 'General plot settings',
    'PlotControlPanel.customPlotSettings' : 'Custom plot settings',
    'PlotControlPanel.currentDSSettings'  : 'Plot settings for '
                                            'selected overlay ({})',
    'PlotControlPanel.customDSSettings'   : 'Custom plot settings for '
                                            'selected overlay ({})',
    'PlotControlPanel.xlim'               : 'X limits',
    'PlotControlPanel.ylim'               : 'Y limits',
    'PlotControlPanel.labels'             : 'Labels',
    'PlotControlPanel.xlabel'             : 'X',
    'PlotControlPanel.ylabel'             : 'Y',
 

    'TimeSeriesControlPanel.customPlotSettings' : 'Time series settings',
    'TimeSeriesControlPanel.customDSSettings'   : 'FEAT settings for '
                                                  'selected overlay ({})',

    'PowerSpectrumControlPanel.customPlotSettings' : 'Power spectrum plot '
                                                     'settings',

    'HistogramControlPanel.customPlotSettings' : 'Histogram plot settings',
    'HistogramControlPanel.customDSSettings'   : 'Histogram settings for '
                                                  'selected overlay ({})',
 
    'FEATModelFitTimeSeries.full' : 'Full model fit',
    'FEATModelFitTimeSeries.cope' : 'COPE{} fit: {}',
    'FEATModelFitTimeSeries.pe'   : 'PE{} fit',

    'FEATPartialFitTimeSeries.cope' : 'Reduced against COPE{}: {}',
    'FEATPartialFitTimeSeries.pe'   : 'Reduced against PE{}',

    'FEATResidualTimeSeries'     : 'Residuals',

    'ClusterPanel.clustName'     : 'Z statistics for COPE{} ({})',
    
    'ClusterPanel.index'         : 'Cluster index',
    'ClusterPanel.nvoxels'       : 'Size (voxels)',
    'ClusterPanel.p'             : 'P',
    'ClusterPanel.logp'          : '-log10(P)',
    'ClusterPanel.zmax'          : 'Z Max',
    'ClusterPanel.zmaxcoords'    : 'Z Max location',
    'ClusterPanel.zcogcoords'    : 'Z Max COG location',
    'ClusterPanel.copemax'       : 'COPE Max',
    'ClusterPanel.copemaxcoords' : 'COPE Max location',
    'ClusterPanel.copemean'      : 'COPE mean',
    
    'ClusterPanel.addZStats'    : 'Add Z statistics',
    'ClusterPanel.addClustMask' : 'Add cluster mask',


    'OverlayDisplayPanel.Display'        : 'General display settings',
    'OverlayDisplayPanel.VolumeOpts'     : 'Volume settings',
    'OverlayDisplayPanel.MaskOpts'       : 'Mask settings',
    'OverlayDisplayPanel.LabelOpts'      : 'Label settings',
    'OverlayDisplayPanel.RGBVectorOpts'  : 'RGB vector settings',
    'OverlayDisplayPanel.LineVectorOpts' : 'Line vector settings',
    'OverlayDisplayPanel.ModelOpts'      : 'Model settings',
    
    'OverlayDisplayPanel.loadCmap'       : 'Load colour map',

    'CanvasSettingsPanel.scene'    : 'Scene settings',
    'CanvasSettingsPanel.ortho'    : 'Ortho view settings',
    'CanvasSettingsPanel.lightbox' : 'Lightbox settings',

    'OverlayInfoPanel.Image.dimensions'   : 'Dimensions',
    'OverlayInfoPanel.Image.transform'    : 'Transform/space',
    'OverlayInfoPanel.Image.orient'       : 'Orientation',
    
    'OverlayInfoPanel.Image'                    : 'NIFTI1 image',
    'OverlayInfoPanel.FEATImage'                : 'NIFTI1 image '
                                                  '(FEAT analysis)',
    'OverlayInfoPanel.FEATImage.featInfo'       : 'FEAT information',
    'OverlayInfoPanel.MelodicImage'             : 'NIFTI1 image '
                                                  '(MELODIC analysis)', 
    'OverlayInfoPanel.MelodicImage.melodicInfo' : 'MELODIC information',
    'OverlayInfoPanel.Model'                    : 'VTK model',
    'OverlayInfoPanel.Model.numVertices'        : 'Number of vertices',
    'OverlayInfoPanel.Model.numIndices'         : 'Number of indices',
    'OverlayInfoPanel.dataSource'               : 'Data source',

    'MelodicClassificationPanel.componentTab'   : 'Components',
    'MelodicClassificationPanel.labelTab'       : 'Labels',
    'MelodicClassificationPanel.loadButton'     : 'Load from file',
    'MelodicClassificationPanel.saveButton'     : 'Save to file',
    'MelodicClassificationPanel.clearButton'    : 'Clear all labels',

    'ComponentGrid.componentColumn'             : 'IC #',
    'ComponentGrid.labelColumn'                 : 'Labels',
    'LabelGrid.componentColumn'                 : 'IC #',
    'LabelGrid.labelColumn'                     : 'Label', 
})


properties = TypeDict({
    
    'Profile.mode'                   : 'Profile',
    
    'DisplayContext.displaySpace'    : 'Display space',

    'CanvasPanel.syncLocation'       : 'Sync location',
    'CanvasPanel.syncOverlayOrder'   : 'Sync overlay order',
    'CanvasPanel.syncOverlayDisplay' : 'Sync overlay display settings',
    'CanvasPanel.movieMode'          : 'Movie mode',
    'CanvasPanel.movieRate'          : 'Movie update rate',
    'CanvasPanel.profile'            : 'Mode',

    'SceneOpts.showCursor'         : 'Show location cursor',
    'SceneOpts.bgColour'           : 'Background colour',
    'SceneOpts.cursorColour'       : 'Location cursor colour',
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
    
    'TimeSeriesPanel.plotMode'         : 'Plotting mode',
    'TimeSeriesPanel.usePixdim'        : 'Use pixdims',
    'TimeSeriesPanel.plotMelodicICs'   : 'Plot component time courses for '
                                         'Melodic images',
    'TimeSeriesPanel.showMode'         : 'Time series to plot',
    'TimeSeriesPanel.plotFullModelFit' : 'Plot full model fit',
    'TimeSeriesPanel.plotResiduals'    : 'Plot residuals',
    
    'HistogramPanel.histType'    : 'Histogram type',
    'HistogramPanel.showMode'    : 'Histogram series to plot',

    'PowerSpectrumPanel.showMode'        : 'Power spectra to plot',
    'PowerSpectrumPanel.plotFrequencies' : 'Show frequencies along x axis ',
    'PowerSpectrumPanel.plotMelodicICs'  : 'Plot component power spectra for '
                                           'Melodic images',

    'DataSeries.colour'    : 'Colour',
    'DataSeries.alpha'     : 'Line transparency',
    'DataSeries.lineWidth' : 'Line width',
    'DataSeries.lineStyle' : 'Line style',
    
    'HistogramSeries.nbins'           : 'Number of bins',
    'HistogramSeries.autoBin'         : 'Automatic histogram binning',
    'HistogramSeries.ignoreZeros'     : 'Ignore zeros',
    'HistogramSeries.includeOutliers' : 'Include values out of data range',
    'HistogramSeries.volume'          : 'Volume',
    'HistogramSeries.dataRange'       : 'Data range',
    'HistogramSeries.showOverlay'     : 'Show 3D histogram overlay',

    'PowerSpectrumSeries.varNorm'     : 'Normalise to unit variance',

    'FEATTimeSeries.plotFullModelFit' : 'Plot full model fit',
    'FEATTimeSeries.plotEVs'          : 'Plot EV{} ({})',
    'FEATTimeSeries.plotPEFits'       : 'Plot PE{} fit ({})',
    'FEATTimeSeries.plotCOPEFits'     : 'Plot COPE{} fit ({})',
    'FEATTimeSeries.plotResiduals'    : 'Plot residuals',
    'FEATTimeSeries.plotPartial'      : 'Plot partial model fit against',
    'FEATTimeSeries.plotData'         : 'Plot data',

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
    
    'VolumeOpts.displayRange'   : 'Display range',
    'VolumeOpts.clippingRange'  : 'Clipping range',
    'VolumeOpts.cmap'           : 'Colour map',
    'VolumeOpts.invert'         : 'Invert colour map',
    'VolumeOpts.invertClipping' : 'Invert clipping range',
    'VolumeOpts.interpolation'  : 'Interpolation',

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

    'ModelOpts.colour'       : 'Colour',
    'ModelOpts.outline'      : 'Show outline only',
    'ModelOpts.outlineWidth' : 'Outline width',
    'ModelOpts.refImage'     : 'Reference image',
    'ModelOpts.coordSpace'   : 'Model coordinate space',
    'ModelOpts.showName'     : 'Show model name',

    'LabelOpts.lut'          : 'Look-up table',
    'LabelOpts.outline'      : 'Show outline only',
    'LabelOpts.outlineWidth' : 'Outline width',
    'LabelOpts.showNames'    : 'Show label names',
})


choices = TypeDict({

    'DisplayContext.displaySpace' : {'world'  : 'World coordinates',
                                     'pixdim' : 'Scaled voxels'},

    'SceneOpts.colourBarLocation'  : {'top'          : 'Top',
                                      'bottom'       : 'Bottom',
                                      'left'         : 'Left',
                                      'right'        : 'Right'},
    'SceneOpts.colourBarLabelSide' : {'top-left'     : 'Top / Left',
                                      'bottom-right' : 'Bottom / Right'},

    'SceneOpts.performance' : {1 : 'Fastest',
                               2 : 'Faster',
                               3 : 'Good looking',
                               4 : 'Best looking'},

    'CanvasOpts.zax' : {0 : 'X axis',
                        1 : 'Y axis',
                        2 : 'Z axis'},

    'OrthoOpts.layout' : {'horizontal' : 'Horizontal',
                          'vertical'   : 'Vertical',
                          'grid'       : 'Grid'},

    'HistogramPanel.dataRange.min' : 'Min.',
    'HistogramPanel.dataRange.max' : 'Max.',

    'LightBoxOpts.zrange.min' : 'Min.',
    'LightBoxOpts.zrange.max' : 'Max.',    

    'VolumeOpts.displayRange.min' : 'Min.',
    'VolumeOpts.displayRange.max' : 'Max.',

    'VectorOpts.displayType.line' : 'Lines',
    'VectorOpts.displayType.rgb'  : 'RGB',

    'VectorOpts.modulate.none'    : 'No modulation',

    'ModelOpts.refImage.none'     : 'No reference image',

    'ImageOpts.transform' : {'affine' : 'Use qform/sform transformation '
                                        'matrix',
                             'pixdim' : 'Use pixdims only',
                             'id'     : 'Do not use qform/sform or pixdims',
                             'custom' : 'Apply a custom transformation '
                                        'matrix'},

    'VolumeOpts.interpolation' : {'none'   : 'No interpolation', 
                                  'linear' : 'Linear interpolation', 
                                  'spline' : 'Spline interpolation'},

    'Display.overlayType' : {'volume'     : '3D/4D volume',
                             'mask'       : '3D/4D mask image',
                             'label'      : 'Label image',
                             'rgbvector'  : '3-direction vector image (RGB)',
                             'linevector' : '3-direction vector image (Line)',
                             'model'      : '3D model'},

    'HistogramPanel.histType' : {'probability' : 'Probability',
                                 'count'       : 'Count'},

    'DataSeries.lineStyle' : {'-'  : 'Solid line',
                              '--' : 'Dashed line',
                              '-.' : 'Dash-dot line',
                              ':'  : 'Dotted line'},
    
    'TimeSeriesPanel.plotMode' : {'normal'        : 'Normal - no '
                                                    'scaling/offsets',
                                  'demean'        : 'Demeaned',
                                  'normalise'     : 'Normalised',
                                  'percentChange' : 'Percent changed'},
    'TimeSeriesPanel.showMode' : {'current' : 'Show the time series for '
                                              'the currently selected overlay',
                                  'all'     : 'Show the time series '
                                              'for all overlays',
                                  'none'    : 'Only show the time series '
                                              'in the time series list'},
    'HistogramPanel.showMode'  : {'current' : 'Show the histogram for '
                                              'the currently selected overlay',
                                  'all'     : 'Show the histograms '
                                              'for all overlays',
                                  'none'    : 'Only show the histograms '
                                              'in the time series list'},
    
    'PowerSpectrumPanel.showMode' : {'current' : 'Show the power spectrum for '
                                                 'the currently selected '
                                                 'overlay',
                                     'all'     : 'Show the power spectra '
                                                 'for all overlays',
                                     'none'    : 'Only show the power spectra '
                                                 'in the power spectra list'} 
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


nifti = TypeDict({

    'dimensions' : 'Number of dimensions',
    
    'datatype'    : 'Data type',
    'vox_units'   : 'XYZ units',
    'time_units'  : 'Time units',
    'descrip'     : 'Description',
    'qform_code'  : 'QForm code',
    'sform_code'  : 'SForm code',
    'intent_code' : 'Intent code',
    'intent_name' : 'Intent name',

    'voxOrient.0'   : 'X voxel orientation',
    'voxOrient.1'   : 'Y voxel orientation',
    'voxOrient.2'   : 'Z voxel orientation',
    'worldOrient.0' : 'X world orientation',
    'worldOrient.1' : 'Y world orientation',
    'worldOrient.2' : 'Z world orientation',

    'qform' : 'QForm matrix',
    'sform' : 'SForm matrix',

    'dim1' : 'dim1',
    'dim2' : 'dim2',
    'dim3' : 'dim3',
    'dim4' : 'dim4',
    'dim5' : 'dim5',
    'dim6' : 'dim6',
    'dim7' : 'dim7',

    'pixdim1' : 'pixdim1',
    'pixdim2' : 'pixdim2',
    'pixdim3' : 'pixdim3',
    'pixdim4' : 'pixdim4',
    'pixdim5' : 'pixdim5',
    'pixdim6' : 'pixdim6',
    'pixdim7' : 'pixdim7', 

    ('datatype', 0)    : 'UNKNOWN',
    ('datatype', 1)    : 'BINARY',
    ('datatype', 2)    : 'UINT8',
    ('datatype', 4)    : 'INT16',
    ('datatype', 8)    : 'INT32',
    ('datatype', 16)   : 'FLOAT32',
    ('datatype', 32)   : 'COMPLEX64',
    ('datatype', 64)   : 'DOUBLE64',
    ('datatype', 128)  : 'RGB',
    ('datatype', 255)  : 'ALL',
    ('datatype', 256)  : 'INT8',
    ('datatype', 512)  : 'UINT16',
    ('datatype', 768)  : 'UINT32',
    ('datatype', 1024) : 'INT64',
    ('datatype', 1280) : 'UINT64',
    ('datatype', 1536) : 'FLOAT128',
    ('datatype', 1792) : 'COMPLEX128',
    ('datatype', 2048) : 'COMPLEX256',
    ('datatype', 2304) : 'RGBA32',

    ('intent_code',  0)     :  'NIFTI_INTENT_CODE_NONE',
    ('intent_code',  2)     :  'NIFTI_INTENT_CODE_CORREL',
    ('intent_code',  3)     :  'NIFTI_INTENT_CODE_TTEST',
    ('intent_code',  4)     :  'NIFTI_INTENT_CODE_FTEST',
    ('intent_code',  5)     :  'NIFTI_INTENT_CODE_ZSCORE',
    ('intent_code',  6)     :  'NIFTI_INTENT_CODE_CHISQ',
    ('intent_code',  7)     :  'NIFTI_INTENT_CODE_BETA',
    ('intent_code',  8)     :  'NIFTI_INTENT_CODE_BINOM',
    ('intent_code',  9)     :  'NIFTI_INTENT_CODE_GAMMA',
    ('intent_code',  10)    :  'NIFTI_INTENT_CODE_POISSON',
    ('intent_code',  11)    :  'NIFTI_INTENT_CODE_NORMAL',
    ('intent_code',  12)    :  'NIFTI_INTENT_CODE_FTEST_NONC',
    ('intent_code',  13)    :  'NIFTI_INTENT_CODE_CHISQ_NONC',
    ('intent_code',  14)    :  'NIFTI_INTENT_CODE_LOGISTIC',
    ('intent_code',  15)    :  'NIFTI_INTENT_CODE_LAPLACE',
    ('intent_code',  16)    :  'NIFTI_INTENT_CODE_UNIFORM',
    ('intent_code',  17)    :  'NIFTI_INTENT_CODE_TTEST_NONC',
    ('intent_code',  18)    :  'NIFTI_INTENT_CODE_WEIBULL',
    ('intent_code',  19)    :  'NIFTI_INTENT_CODE_CHI',
    ('intent_code',  20)    :  'NIFTI_INTENT_CODE_INVGAUSS',
    ('intent_code',  21)    :  'NIFTI_INTENT_CODE_EXTVAL',
    ('intent_code',  22)    :  'NIFTI_INTENT_CODE_PVAL',
    ('intent_code',  23)    :  'NIFTI_INTENT_CODE_LOGPVAL',
    ('intent_code',  24)    :  'NIFTI_INTENT_CODE_LOG10)  :PVAL',
    ('intent_code',  2)     :  'NIFTI_FIRST_STATCODE',
    ('intent_code',  24)    :  'NIFTI_LAST_STATCODE',
    ('intent_code',  1001)  :  'NIFTI_INTENT_CODE_ESTIMATE',
    ('intent_code',  1002)  :  'NIFTI_INTENT_CODE_LABEL',
    ('intent_code',  1003)  :  'NIFTI_INTENT_CODE_NEURONAME',
    ('intent_code',  1004)  :  'NIFTI_INTENT_CODE_GENMATRIX',
    ('intent_code',  1005)  :  'NIFTI_INTENT_CODE_SYMMATRIX',
    ('intent_code',  1006)  :  'NIFTI_INTENT_CODE_DISPVECT',
    ('intent_code',  1007)  :  'NIFTI_INTENT_CODE_VECTOR',
    ('intent_code',  1008)  :  'NIFTI_INTENT_CODE_POINTSET',
    ('intent_code',  1009)  :  'NIFTI_INTENT_CODE_TRIANGLE',
    ('intent_code',  1010)  :  'NIFTI_INTENT_CODE_QUATERNION',
    ('intent_code',  1011)  :  'NIFTI_INTENT_CODE_DIMLESS',
    ('intent_code',  2001)  :  'NIFTI_INTENT_CODE_TIME_SERIES',
    ('intent_code',  2002)  :  'NIFTI_INTENT_CODE_NODE_INDEX',
    ('intent_code',  2003)  :  'NIFTI_INTENT_CODE_RGB_VECTOR',
    ('intent_code',  2004)  :  'NIFTI_INTENT_CODE_RGBA_VECTOR',
    ('intent_code',  2005)  :  'NIFTI_INTENT_CODE_SHAPE',
})


feat = TypeDict({
    'analysisName' : 'Analysis name',
    'numPoints'    : 'Number of volumes',
    'numEVs'       : 'Number of EVs',
    'numContrasts' : 'Number of contrasts',
    'report'       : 'Link to report',
})


melodic = TypeDict({
    'dataFile'       : 'Data file',
    'partOfAnalysis' : 'Part of analysis',
    'numComponents'  : 'Number of ICs',
    'tr'             : 'TR time',
    'report'         : 'Link to report',
})

perspectives = {
    'melview' : 'Melodic mode',
    'feat'    : 'FEAT mode',
}
