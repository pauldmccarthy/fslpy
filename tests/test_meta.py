#!/usr/bin/env python
#
# test_meta.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import fsl.utils.meta as meta


def test_meta():
    m = meta.Meta()

    data = {'a': 1, 'b' : 2, 'c' : 3}

    for k, v in data.items():
        m.setMeta(k, v)

    for k, v in data.items():
        assert m.getMeta(k) == v

    assert list(data.keys())   == list(m.metaKeys())
    assert list(data.values()) == list(m.metaValues())
    assert list(data.items())  == list(m.metaItems())
