#!/usr/bin/env python
#
# melodicimage.py - An Image subclass which has some MELODIC-specific
# functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`MelodicImage` class, an :class:`.Image`
sub-class which encapsulates data from a MELODIC analysis.
"""
import os.path as op

import image          as fslimage
import melodicresults as melresults


class MelodicImage(fslimage.Image):
    """
    """

    def __init__(self, image, *args, **kwargs):
        """
        """


        if op.isdir(image):

            dirname  = image
            filename = 'melodic_IC'


        else:
            dirname  = op.dirname( image)
            filename = op.basename(image)

        dirname = dirname.rstrip(op.sep)

        if not melresults.isMelodicDir(dirname):
            raise ValueError('{} does not appear to be a '
                             'MELODIC directory'.format(dirname)) 
        
        if not filename.startswith('melodic_IC'):
            raise ValueError('{} does not appear to be a MELODIC '
                             'component file'.format(filename))
            
        fslimage.Image.__init__(self,
                                op.join(dirname, filename),
                                *args,
                                **kwargs)

        self.__melmix = melresults.getComponentTimeSeries(dirname)

        
    def getComponentTimeSeries(self, component):
        return self.__melmix[:, component]


    def numComponents(self):
        return self.shape[3]
