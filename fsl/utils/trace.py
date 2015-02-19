#!/usr/bin/env python
#
# trace.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import logging
import inspect

log = logging.getLogger(__name__)

def trace(desc):

    stack = inspect.stack()[1:]
    lines = '{}\n'.format(desc)

    for i, frame in enumerate(stack):

        srcMod    = frame[1]
        srcLineNo = frame[2]

        if frame[4] is not None: srcLine = frame[4][frame[5]]
        else:                    srcLine = '<native>'

        lines = lines + '{}{}:{}: {}\n'.format(
            ' ' * (i + 1),
            srcMod, srcLineNo,
            srcLine.strip())

    log.debug(lines)
    
    return lines
