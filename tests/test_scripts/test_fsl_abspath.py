#!/usr/bin/env python
#
# test_fsl_abspath.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op

import fsl.scripts.fsl_abspath as fsl_abspath

from tests import tempdir, CaptureStdout


def test_usage():
    assert fsl_abspath.main([]) != 0


def test_fsl_abspath():

    # fsl_abspath just calls os.path.realpath

    with tempdir() as td:

        oneup = op.dirname(td)

        # (input, expected)
        tests = [
            ('file',    f'{td}/file'),
            ('./file',  f'{td}/file'),
            ('../file', f'{oneup}/file'),

            ('/file',         '/file'),
            ('/one/two/file', '/one/two/file'),
        ]

        for input, expected in tests:
            cap = CaptureStdout()

            with cap:
                ret = fsl_abspath.main([input])

            assert ret == 0
            assert cap.stdout.strip() == expected
