#!/usr/bin/env python
#
# __init__.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
log = logging.getLogger(__name__)

import fsl.fslview.action as action

import openfile
import openstandard
import loadcolourmap

Action              = action       .Action
OpenFileAction      = openfile     .OpenFileAction
OpenStandardAction  = openstandard .OpenStandardAction
LoadColourMapAction = loadcolourmap.LoadColourMapAction

def listActions():
    """Convenience function which returns a list containing all
    :class:`~fsl.fslview.action.Action` classes in the :mod:`actions` package.
    """

    atts = globals()

    actions = []

    for name, val in atts.items():
        
        if not isinstance(val, type): continue
        if val == Action:             continue
            
        if issubclass(val, Action):
            actions.append(val)
            
    return actions
