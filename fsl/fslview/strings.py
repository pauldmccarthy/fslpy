#!/usr/bin/env python
#
# strings.py - Labels used throughout FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.fslview.views    as views
import fsl.fslview.controls as controls


viewPanelTitles = {
    views.OrthoPanel      : 'Ortho view',
    views.LightBoxPanel   : 'Lightbox view',
    views.TimeSeriesPanel : 'Time series'
}


controlPanelTitles = {
    controls.ImageDisplayPanel : 'Image display properties',
    controls.ImageListPanel    : 'Image list',
    controls.LocationPanel     : 'Cursor location'
}


viewPanelConfigMenuText = {
    views.OrthoPanel      : '{} display properties',
    views.LightBoxPanel   : '{} display properties',
    views.TimeSeriesPanel : '{} display properties'
}


openFile = 'Add image file'
openStd  = 'Add standard'


orthoConfigMenu    = '{} display'
lightBoxConfigMenu = '{} display'

locationPanelOutOfBounds = 'Out of bounds'
