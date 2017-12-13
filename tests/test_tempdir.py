#!/usr/bin/env python
#
# test_tempdir.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os
import os.path as op

import fsl.utils.tempdir as tempdir


def test_tempdir():

    # use ctx manager with or without arg
    with tempdir.tempdir():
        d = os.getcwd()

    # dir is removed after ctx manager exit
    assert not op.exists(d)

    with tempdir.tempdir() as td:

        d = td

        assert op.exists(d)

        # pwd is dir when in ctx manager
        assert op.realpath(os.getcwd()) == op.realpath(td)

    assert not op.exists(d)
