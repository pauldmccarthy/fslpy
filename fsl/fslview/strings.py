#!/usr/bin/env python
#
# strings.py - Labels used throughout FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from views   .orthopanel        import OrthoPanel
from views   .lightboxpanel     import LightBoxPanel
from views   .timeseriespanel   import TimeSeriesPanel
from controls.imagedisplaypanel import ImageDisplayPanel
from controls.imagelistpanel    import ImageListPanel
from controls.locationpanel     import LocationPanel


viewPanelTitles = {
    OrthoPanel      : 'Ortho view',
    LightBoxPanel   : 'Lightbox view',
    TimeSeriesPanel : 'Time series'
}


controlPanelTitles = {
    ImageDisplayPanel : 'Image display properties',
    ImageListPanel    : 'Image list',
    LocationPanel     : 'Cursor location'
}


viewPanelConfigMenuText = {
    OrthoPanel      : '{} display properties',
    LightBoxPanel   : '{} display properties',
    TimeSeriesPanel : '{} display properties'
}


openFile = 'Add image file'
openStd  = 'Add standard'


orthoConfigMenu    = '{} display'
lightBoxConfigMenu = '{} display'

locationPanelOutOfBounds = 'Out of bounds'
