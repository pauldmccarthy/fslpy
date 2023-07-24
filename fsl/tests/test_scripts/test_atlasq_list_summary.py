#!/usr/bin/env python
#
# test_list_summary.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import              os
import itertools as it

import              pytest

import fsl.data.atlases   as fslatlases
import fsl.scripts.atlasq as fslatlasq

from .. import CaptureStdout


pytestmark = pytest.mark.fsltest


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')


def test_list():

    fslatlases.rescanAtlases()

    adescs  = fslatlases.listAtlases()
    capture = CaptureStdout()

    tests     = ['list', 'list --extended']
    extendeds = [False, True]

    for test, extended in zip(tests, extendeds):
        capture.reset()

        with capture:
            fslatlasq.main(test.split())

        stdout = capture.stdout

        for desc in adescs:
            assert desc.atlasID in stdout
            assert desc.name    in stdout

            assert (desc.specPath in stdout) == extended

            for image in it.chain(desc.images, desc.summaryImages):
                assert (image in stdout) == extended
                assert (image in stdout) == extended


def test_summary():

    fslatlases.rescanAtlases()

    adescs  = fslatlases.listAtlases()
    capture = CaptureStdout()

    for desc in adescs:

        tests = [desc.atlasID, desc.name]

        for test in tests:

            capture.reset()

            with capture:
                fslatlasq.main(['summary', test])

            stdout = capture.stdout

            assert desc.atlasID   in stdout
            assert desc.name      in stdout
            assert desc.specPath  in stdout
            assert desc.atlasType in stdout

            for image in it.chain(desc.images, desc.summaryImages):
                assert image in stdout

            for label in desc.labels:
                assert label.name in stdout
