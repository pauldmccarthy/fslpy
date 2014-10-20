#!/usr/bin/env python
#
# strings.py - Labels used throughout FSLView.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

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
