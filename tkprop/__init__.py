#!/usr/bin/env python
#
# __init__.py - Sets up the tkprop package namespace.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from tkprop.properties import \
    PropertyBase, \
    HasProperties, \
    Boolean, \
    Int, \
    Double, \
    String, \
    Choice, \
    FilePath

from tkprop.widgets import \
    makeWidget

from tkprop.build import \
    buildGUI, \
    ViewItem, \
    Widget, \
    Group, \
    NotebookGroup, \
    HGroup, \
    VGroup
