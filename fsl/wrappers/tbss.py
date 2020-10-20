#!/usr/bin/env python3
#
# tbss.py - Wrappers for FSL command-line tools for tract based spatial
# statistics (TBSS).
#
# Author: Evan Edmond <eedmond@gmail.com>
#

"""This module contains wrapper functions for various `TBSS
<https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TBSS/>`_ command-line tools.
"""


import fsl.utils.assertions as asrt
from . import wrapperutils  as wutils


@wutils.fslwrapper
def preproc(*images):
    """Wrapper for the ``tbss_1_preproc`` command.
    Usage: ``tbss_1_preproc(<image1>, <image2>, ...)``
    """
    for img in images:
        asrt.assertIsNifti(img)

    return ["tbss_1_preproc"] + list(images)


@wutils.fslwrapper
def reg(**kwargs):
    """Wrapper for the ``tbss_2_reg`` command.
    Refer to the ``tbss_2_reg`` command-line help for details on all arguments.
    """

    valmap = {
        'T' : wutils.SHOW_IF_TRUE,
        'n' : wutils.SHOW_IF_TRUE,
    }

    cmd = ["tbss_2_reg"]
    cmd += wutils.applyArgStyle("-", valmap=valmap, valsep=" ", **kwargs)

    return cmd

@wutils.fslwrapper
def postreg(**kwargs):
    """Wrapper for the ``tbss_3_postreg`` command.
    Refer to the ``tbss_3_postreg`` command-line help for details on all
    arguments.
    """

    valmap = {
        'T' : wutils.SHOW_IF_TRUE,
        'S' : wutils.SHOW_IF_TRUE,
    }

    cmd = ["tbss_3_postreg"]
    cmd += wutils.applyArgStyle("-", valmap=valmap, **kwargs)

    return cmd


@wutils.fslwrapper
def prestats(threshold):
    """Wrapper for the ``tbss_4_prestats`` command.
    The normal recommendation for <threshold> is 0.2
    """

    return ["tbss_4_prestats", f'{threshold}']


@wutils.fslwrapper
def non_FA(alt_img_root):
    """Wrapper for the ``tbss_non_FA`` command.
    e.g.: ``tbss_non_FA("L2")``
    """

    return ["tbss_non_FA", alt_img_root]


@wutils.fileOrImage("stats_image", "mean_FA", "output")
@wutils.fslwrapper
def fill(stats_image, threshold, mean_FA, output, **kwargs):
    """Wrapper for the ``tbss_fill`` command.
    Refer to the ``tbss_fill`` command-line help for details on all arguments.
    """
    valmap = {
        'n' : wutils.SHOW_IF_TRUE,
    }

    cmd = ["tbss_fill", stats_image, f'{threshold}', mean_FA, output]
    cmd += wutils.applyArgStyle("-", valmap=valmap, **kwargs)

    return cmd
