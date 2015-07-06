#!/usr/bin/env python
#
# featimage.py - An Image subclass which has some FEAT-specific functionality.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`FeatImage` class, a subclass of
:class:`.Image` designed for the ``filtered_func_data`` file of a FEAT
analysis.
"""

import os.path as op

import image as fslimage


def isFEATData(path):
    keys = ['.feat{}filtered_func_data' .format(op.sep),
            '.gfeat{}filtered_func_data'.format(op.sep)]

    isfeat = any([k in path for k in keys])
    
    return isfeat


class FEATImage(fslimage.Image):

    def __init__(self, image, **kwargs):
        fslimage.Image.__init__(self, image, **kwargs)

        if not isFEATData(self.dataSource):
            raise ValueError('{} does not appear to be data from a '
                             'FEAT analysis'.format(self.dataSource))


    # A FEATImage is an Image which has 
    # some extra utility methods, something 
    # like all of the below things:

    # def numParameterEstimates(self):
    #     return 0
    
    # def numCOPEs(self):
    #     return 0

    
    # def getParameterEstimate(self, num):
    #     pass

    
    # def getFullModelFit(self):
    #     pass

    
    # def getPartialModelFIt(self, contrast):
    #     pass

    
    # def getCOPEs(self):
    #     pass


    # def getZStats(self):
    #     pass

    
    # def getThresholdedZStats(self):
    #     pass

    
    # def getSomethingForClusters(self):
    #     pass


    # # Return a copy of this image, transformed
    # # to the specified spaced (e.g. MNI152,
    # # structural, functional, etc)
    # def getInSpace(self, space):
    #     pass
