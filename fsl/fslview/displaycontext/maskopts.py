#!/usr/bin/env python
#
# maskdisplay.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import props


class MaskOpts(props.SyncableHasProperties):

    colour = props.Colour()
    invert = props.Boolean(default=False)

    def __init__(self, image, parent=None):
        props.SyncableHasProperties.__init__(self, parent)
