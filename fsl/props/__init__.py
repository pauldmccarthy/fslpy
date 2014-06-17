#!/usr/bin/env python
#
# __init__.py - Sets up the fsl.props package namespace.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

from properties import (
    PropertyBase,
    HasProperties,
    Boolean,
    Int,
    Real,
    Percentage,
    String,
    FilePath,
    Choice,
    List,
    ColourMap,
    Bounds,
    Point)


try:
    from widgets import makeWidget
    
    from build import (
        buildGUI, 
        ViewItem, 
        Button, 
        Widget, 
        Group, 
        NotebookGroup,
        HGroup, 
        VGroup)
    
except Exception as e:
    log.warn('GUI property module import failed: {}'.format(e), exc_info=True)
