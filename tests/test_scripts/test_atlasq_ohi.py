#!/usr/bin/env python
#
# test_ohi.py - Test the fsl.atlasq ohi interface, which mimics the behaviour
#               of the old atlasquery tool.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import os.path as op
import            os
import            shlex

import            pytest

import numpy as np

import fsl.scripts.atlasq as fslatlasq
import fsl.data.atlases   as fslatlases

from .. import (tempdir,
                make_random_mask,
                CaptureStdout)


pytestmark = pytest.mark.fsltest


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')


def test_dumpatlases():
    """Test the ohi --dumpatlases option. """

    capture = CaptureStdout()

    with capture:
        fslatlasq.main('ohi --dumpatlases'.split())

    atlases = fslatlases.listAtlases()
    atlases = [a.name for a in atlases]
    atlases = sorted(atlases)

    assert capture.stdout.strip() == '\n'.join(atlases)


@pytest.mark.longtest
def test_coords(seed):
    """Test the ohi -a "atlas" -c "coords" mode. """

    def expectedProbOutput(atlas, coords):
        probs    = atlas.proportions(coords)
        expected = '<b>{}</b><br>'.format(atlas.desc.name)
        nzprobs  = []

        for i, p in enumerate(probs):
            if p > 0:
                label = atlas.desc.labels[i].name
                nzprobs.append((p, label))

        if len(nzprobs) > 0:
            nzprobs = reversed(sorted(nzprobs, key=lambda b: b[0]))
            nzprobs = ['{:d}% {}'.format(int(round(p)), l) for
                       (p, l) in nzprobs]
            expected += ', '.join(nzprobs)
        else:
            expected += 'No label found!'

        return expected

    def expectedLabelOutput(atlas, coords):
        label    = atlas.label(coords)
        expected = '<b>{}</b><br>'.format(atlas.desc.name)

        if label is None:
            return expected + 'Unclassified'
        else:
            return expected + atlas.desc.find(value=int(label)).name

    capture = CaptureStdout()

    # random coordinates in MNI152 space,
    # with some coordinates out of bounds
    ncoords = 50
    xc      = -100  + 190 * np.random.random(ncoords)
    yc      = -130  + 220 * np.random.random(ncoords)
    zc      = -80   + 120 * np.random.random(ncoords)
    coords  = np.vstack((xc, yc, zc)).T

    fslatlases.rescanAtlases()
    atlases = fslatlases.listAtlases()

    for ad in atlases:

        # atlasquery/ohi always uses 2mm resolution
        atlas = fslatlases.loadAtlas(
            ad.atlasID,
            resolution=2,
            calcRange=False,
            loadData=False)

        print(ad.name)

        for x, y, z in coords:

            cmd = 'ohi -a "{}" -c "{},{},{}"'.format(ad.name, x, y, z)

            capture.reset()
            with capture:
                fslatlasq.main(shlex.split(cmd))

            if isinstance(atlas, fslatlases.ProbabilisticAtlas):
                expected = expectedProbOutput(atlas, (x, y, z))

            # LabelAtlas
            else:
                expected = expectedLabelOutput(atlas, (x, y, z))

            assert capture.stdout.strip() == expected.strip()


def test_bad_atlas():
    """Test the ohi -a "atlas" ..., with a non-existent atlas. """

    capture = CaptureStdout()

    atlases = fslatlases.listAtlases()
    atlases = sorted([a.name for a in atlases])

    expected = ['Invalid atlas name. Try one of:'] + atlases
    expected = '\n'.join(expected)

    cmds = ['ohi -a "non-existent atlas" -c "0,0,0"',
            'ohi -a "non-existent atlas" -m "nomask"']

    for cmd in cmds:
        capture.reset()
        with capture:
            fslatlasq.main(shlex.split(cmd))
            assert capture.stdout.strip() == expected


@pytest.mark.longtest
def test_mask(seed):
    """Test the ohi -a "atlas" -m "mask" mode, with label and probabilistic
    atlases.
    """

    def expectedLabelOutput(mask, atlas):

        labels, props = atlas.maskLabel(mask)
        exp           = []

        for lbl, prop in zip(labels, props):
            name = desc.find(value=int(lbl)).name
            exp.append('{}:{:0.4f}'.format(name, prop))

        return '\n'.join(exp)

    def expectedProbOutput(mask, atlas):

        props  = atlas.maskProportions(mask)
        labels = [l.index for l in atlas.desc.labels]
        exp    = []

        for lbl, prop in zip(labels, props):
            if prop > 0:
                exp.append('{}:{:0.4f}'.format(desc.labels[int(lbl)].name,
                                               prop))

        return '\n'.join(exp)

    fslatlases.rescanAtlases()

    capture     = CaptureStdout()
    atlases     = fslatlases.listAtlases()

    with tempdir() as td:

        maskfile = op.join(td, 'mask.nii')

        for desc in atlases:

            # atlasquery always uses 2mm
            # resolution versions of atlases
            atlas2mm = fslatlases.loadAtlas(desc.atlasID, resolution=2)

            # Test with 1mm and 2mm masks
            for res in [1, 2]:
                atlasimg = fslatlases.loadAtlas(desc.atlasID, resolution=res)
                maskimg  = make_random_mask(maskfile,
                                            atlasimg.shape[:3],
                                            atlasimg.voxToWorldMat)

                cmd      = 'ohi -a "{}" -m {}'.format(desc.name, maskfile)
                print(cmd)

                capture.reset()
                with capture:
                    fslatlasq.main(shlex.split(cmd))

                if isinstance(atlasimg, fslatlases.LabelAtlas):
                    expected = expectedLabelOutput(maskimg, atlas2mm)
                elif isinstance(atlasimg, fslatlases.ProbabilisticAtlas):
                    expected = expectedProbOutput(maskimg, atlas2mm)

                assert capture.stdout.strip() == expected
