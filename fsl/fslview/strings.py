#!/usr/bin/env python
#
# strings.py - Labels used throughout FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.fslview.views as views

imageDisplayTitle = 'Image display properties'
imageListTitle    = 'Image list'
locationTitle     = 'Cursor location'

openFile = 'Add image file'
openStd  = 'Add standard'

orthoConfigMenu    = '{} display'
lightBoxConfigMenu = '{} display'


locationPanelOutOfBounds = 'Out of bounds'


viewPanelTitles = {
    views.OrthoPanel      : 'Ortho view',
    views.LightBoxPanel   : 'Lightbox view',
    views.TimeSeriesPanel : 'Time series'
}

viewPanelConfigMenuText = {
    views.OrthoPanel      : '{} display properties',
    views.LightBoxPanel   : '{} display properties',
    views.TimeSeriesPanel : '{} display properties'
}
