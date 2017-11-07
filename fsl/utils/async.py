#!/usr/bin/env python
#
# async.py - Deprecaed - use the idle module instead.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module is deprecated - use the :mod:`.idle` module instead. """


import logging
import warnings

from .idle import (run,  # noqa
                   idleReset,
                   getIdleTimeout,
                   setIdleTimeout,
                   inIdle,
                   cancelIdle,
                   idle,
                   idleWhen,
                   wait,
                   TaskThreadVeto,
                   TaskThread,
                   mutex)


log = logging.getLogger(__name__)


warnings.warn('fsl.utils.async is deprecated and will be removed '
              'in fslpy 2.0.0 - use fsl.utils.idle instead',
              DeprecationWarning)
log.warning('fsl.utils.async is deprecated and will be removed '
            'in fslpy 2.0.0 - use fsl.utils.idle instead')
