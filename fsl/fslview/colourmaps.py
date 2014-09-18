#!/usr/bin/env python
#
# colourmaps.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import glob

import numpy             as np
import matplotlib.colors as colors
import matplotlib.cm     as mplcm

import logging
log = logging.getLogger(__name__)


default   =  'Greys_r'
cmapNames = ['Greys_r',
             'Greys',
             'Reds',
             'Reds_r',
             'Blues',
             'Blues_r',
             'Greens',
             'Greens_r',
             'pink',
             'pink_r',
             'hot',
             'hot_r',
             'cool',
             'cool_r', 
             'autumn',
             'autumn_r',
             'copper',
             'copper_r']


for cmapFile in glob.glob(op.join(op.dirname(__file__),
                                  'colourmaps',
                                  '*.cmap')):

    try:
        name = op.basename(cmapFile).split('.')[0]
        data = np.loadtxt(cmapFile)
        cmap = colors.ListedColormap(data, name)

        log.debug('Loading and registering custom '
                  'colour map: {}'.format(cmapFile))

        mplcm.register_cmap(name, cmap)
        cmapNames.append(name)
        
    except:
        log.warn('Error processing custom colour '
                 'map file: {}'.format(cmapFile))
