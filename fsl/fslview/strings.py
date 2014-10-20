#!/usr/bin/env python
#
# strings.py - Labels used throughout FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.data.image as fslimage

from views   .orthopanel         import OrthoPanel
from views   .lightboxpanel      import LightBoxPanel
from views   .timeseriespanel    import TimeSeriesPanel
from views   .spacepanel         import SpacePanel

from controls.imagedisplaypanel  import ImageDisplayPanel
from controls.imagelistpanel     import ImageListPanel
from controls.locationpanel      import LocationPanel

from actions .screengrabaction   import ScreenGrabAction
from actions .openfileaction     import OpenFileAction
from actions .openstandardaction import OpenStandardAction


viewPanelTitles = {
    OrthoPanel      : 'Ortho view',
    LightBoxPanel   : 'Lightbox view',
    TimeSeriesPanel : 'Time series',
    SpacePanel      : 'Space inspector',
}


controlPanelTitles = {
    ImageDisplayPanel : 'Image display properties',
    ImageListPanel    : 'Image list',
    LocationPanel     : 'Cursor location'
}

actionTitles = {
    OpenFileAction     : 'Add image file',
    OpenStandardAction : 'Add standard',
    ScreenGrabAction   : 'Take screenshot'
}

viewPanelConfigMenuText = {
    OrthoPanel      : '{} display properties',
    LightBoxPanel   : '{} display properties',
    TimeSeriesPanel : '{} display properties'
}

orthoConfigMenu    = '{} display'
lightBoxConfigMenu = '{} display'

locationPanelOutOfBounds = 'Out of bounds'



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
