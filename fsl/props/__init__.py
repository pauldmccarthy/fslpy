#!/usr/bin/env python
#
# __init__.py - Sets up the fsl.props package namespace.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from properties import \
    PropertyBase,  \
    HasProperties, \
    Boolean,       \
    Int,           \
    Double,        \
    Percentage,    \
    String,        \
    FilePath,      \
    Choice,        \
    List,          \
    ColourMap,     \
    Bounds

from widgets import \
    makeWidget

from build import \
    buildGUI,      \
    ViewItem,      \
    Button,        \
    Widget,        \
    Group,         \
    NotebookGroup, \
    HGroup,        \
    VGroup
