#!/usr/bin/env python
#
# test_query.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


import                  os
import os.path       as op
import                  re
import itertools     as it
import numpy         as np
import scipy.ndimage as ndi

import                  pytest

import fsl.transform.affine     as affine
import fsl.data.atlases         as fslatlases
import fsl.utils.image.resample as resample
import fsl.data.image           as fslimage
import fsl.scripts.atlasq       as fslatlasq

from .. import (tempdir,
                make_random_mask,
                CaptureStdout)


pytestmark = pytest.mark.fsltest


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')


atlases  = ['mni', 'talairach']

# False: do not use the --label flag
# True:  use the --label flag
#
# ('label', True) should be equivalent to ('label', False)
use_labels = [True, False]

# mask_1 == 1mm mask image
# mask_2 == 2mm mask image
query_types  = ['coordinate',
                'voxel',
                'mask_1',
                'mask_2']

# 'in':   query is inside the atlas (results expected)
# 'zero': query is inside the atlas, but out of any region (no results
#         expected)
# 'out':  query is outside the atlas (no results expected)
query_is_in  = ['in', 'zero', 'out']
resolutions  = [1, 2]
output_types = ['normal', 'short']

tests = list(it.product(atlases,
                        use_labels,
                        query_types,
                        query_is_in,
                        resolutions,
                        output_types))

# side-test - multiple queries together,
# in both short and normal output formats

def test_query_voxel(seed):
    _test_query([t for t in tests if t[2] == 'voxel'])
def test_query_coord(seed):
    _test_query([t for t in tests if t[2] == 'coordinate'])

@pytest.mark.longtest
def test_query_mask(seed):
    _test_query([t for t in tests if t[2].startswith('mask')])


def _test_query(tests):

    fslatlases.rescanAtlases()
    capture  = CaptureStdout()
    print()

    for atlas, use_label, q_type, q_in, res, o_type in tests:

        with tempdir() as td:

            if q_type in ('voxel', 'coordinate'):
                genfunc  = _gen_coord_voxel_query
                evalfunc = _eval_coord_voxel_query
            else:
                genfunc  = _gen_mask_query
                evalfunc = _eval_mask_query

            print('Test: {} {}mm label={} type={} in={} type={}'.format(
                atlas, res, use_label, q_type, q_in, o_type))

            query = genfunc(atlas, use_label, q_type, q_in, res)
            cmd   = _build_command_line(
                atlas, query, use_label, q_type, res, o_type)

            print('fslatlasq {}'.format(' '.join(cmd)))

            capture.reset()
            with capture:
                fslatlasq.main(cmd)

            evalfunc(capture.stdout,
                     atlas,
                     query,
                     use_label,
                     q_type,
                     q_in,
                     res,
                     o_type)


def _get_atlas(aid, use_label, res):
    return fslatlases.loadAtlas(aid, loadSummary=use_label, resolution=res)


_zero_masks = {}
def _get_zero_mask(a_img, atlas, use_label, res):

    # Make a mask which tells us which
    # voxels in the atlas are all zeros
    zmask = _zero_masks.get((atlas, use_label, res), None)

    if zmask is None:
        if isinstance(a_img, fslatlases.LabelAtlas):
            zmask = a_img[:] == 0
        elif isinstance(a_img, fslatlases.ProbabilisticAtlas):
            zmask = np.all(a_img[:] == 0, axis=-1)
        _zero_masks[atlas, use_label, res] = zmask

    return zmask


def _gen_coord_voxel_query(atlas, use_label, q_type, q_in, res):

    a_img = _get_atlas(atlas, use_label, res)
    voxel = q_type == 'voxel'

    if voxel: dtype = int
    else:     dtype = float

    if q_in == 'out':

        if voxel:
            dlo = (0, 0, 0)
            dhi = a_img.shape
        else:
            dlo, dhi = affine.axisBounds(a_img.shape, a_img.voxToWorldMat)

        dlen = [hi - lo for lo, hi in zip(dlo, dhi)]

        coords = []
        for d in range(3):

            # over
            if np.random.random() > 0.5:
                coords.append(dlo[d] + dlen[d] + dlen[d] * np.random.random())
            # or under
            else:
                coords.append(dlo[d] - dlen[d] * np.random.random())

        coords = np.array(coords, dtype=dtype)

    else:

        # Make a mask which tells us which
        # voxels in the atlas are all zeros
        zmask = _get_zero_mask(a_img, atlas, use_label, res)

        # get indices to voxels which are
        # either all zero, or which are
        # not all all zero, depending on
        # the value of q_in
        if q_in == 'in': zidxs = np.where(zmask == 0)
        else:            zidxs = np.where(zmask)

        # Randomly choose a voxel
        cidx   = np.random.randint(0, len(zidxs[0]))
        coords = [zidxs[0][cidx], zidxs[1][cidx], zidxs[2][cidx]]
        coords = np.array(coords, dtype=dtype)

        if not voxel:
            coords = affine.transform(coords, a_img.voxToWorldMat)

    return tuple([dtype(c) for c in coords])


def _eval_coord_voxel_query(
        stdout, atlas, query, use_label, q_type, q_in, res, o_type):

    a_img = _get_atlas(atlas, use_label, res)

    voxel   = q_type == 'voxel'
    prob    = a_img.desc.atlasType == 'probabilistic'
    x, y, z = query

    if voxel: squery = '{:0.0f} {:0.0f} {:0.0f}'.format(*query)
    else:     squery = '{:0.2f} {:0.2f} {:0.2f}'.format(*query)

    if voxel: lsquery = 'voxel {}'     .format(squery)
    else:     lsquery = 'coordinate {}'.format(squery)

    def evalLabelNormalOutput(explabel):

        assert lsquery in stdout

        # all label atlases have an entry for 0
        if q_in == 'in' or (q_in == 'zero' and not prob):

            explabel = int(explabel)

            if prob: labelobj = a_img.desc.labels[explabel - 1]
            else:    labelobj = a_img.desc.labels[explabel]

            assert labelobj.name           in stdout
            assert ' {} '.format(explabel) in stdout

            if prob:
                assert ' {} '.format(labelobj.index) in stdout

        else:
            assert 'No label' in stdout

    def evalLabelShortOutput(explabel):

        if q_in == 'in' or (q_in == 'zero' and not prob):

            explabel = int(explabel)

            if prob: labelobj = a_img.desc.labels[explabel - 1]
            else:    labelobj = a_img.desc.labels[explabel]

            exp = [q_type, squery, labelobj.name]

        else:
            exp = [q_type, squery, 'No label']

        _stdout = re.sub(r'\s+', ' ', stdout).strip()
        assert _stdout.strip() == ' '.join(exp).strip()

    def evalProbNormalOutput(expprops):

        assert lsquery in stdout

        if q_in == 'in':
            lines = stdout.split('\n')
            explabels = [a_img.desc.labels[i] for i in range(len(expprops))]

            for explabel, expprop in zip(explabels, expprops):
                if expprop == 0:
                    continue

                hits = [l for l in lines if explabel.name in l]

                assert len(hits) == 1

                line = hits[0]

                assert ' {} '   .format(explabel.index)     in line
                assert ' {} '   .format(explabel.index + 1) in line
                assert '{:0.4f}'.format(expprop)            in line
        else:
            assert 'No results' in stdout

    def evalProbShortOutput(expprops):

        if q_in == 'in':

            exp    = [q_type, squery]
            labels = [a_img.desc.labels[i].name for i in range(len(expprops))]

            for expprop, explabel in reversed(sorted(zip(expprops, labels))):

                if expprop == 0:
                    break

                exp.append('{} {:0.4f}'.format(explabel, expprop))

        else:
            exp = [q_type, squery]

        _stdout = re.sub(r'\s+', ' ', stdout).strip()
        assert _stdout == ' '.join(exp)

    if isinstance(a_img, fslatlases.LabelAtlas):
        explabel = a_img.label(query, voxel=voxel)
        if o_type == 'normal': evalLabelNormalOutput(explabel)
        else:                  evalLabelShortOutput(explabel)
    elif isinstance(a_img, fslatlases.ProbabilisticAtlas):
        expprops = a_img.values(query, voxel=voxel)
        if o_type == 'normal': evalProbNormalOutput(expprops)
        else:                  evalProbShortOutput(expprops)


def _gen_mask_query(atlas, use_label, q_type, q_in, res):

    maskres  = int(q_type[-1])


    maskfile = 'mask.nii.gz'
    a_img    = _get_atlas(atlas, use_label, res)

    if q_in == 'out':
        make_random_mask(maskfile, (20, 20, 20), np.eye(4))
    else:

        zmask = _get_zero_mask(a_img, atlas, use_label, res)

        if q_in == 'in':
            zmask = zmask == 0

        mask = make_random_mask(
            maskfile, a_img.shape[:3], a_img.voxToWorldMat, zmask, minones=20)

        if maskres != res:

            zmask = ndi.binary_erosion(zmask, iterations=3)
            mask[zmask == 0] = 0

            a = _get_atlas(atlas, True, maskres)

            # Make sure that when the mask gets
            # resampled into the atlas resolution,
            # it is still either in or out of the
            # atlas space
            mask, xform = resample.resample(
                mask, a.shape[:3], dtype=np.float32, order=1)

            thres = np.percentile(mask[mask > 0], 75)

            mask[mask >= thres] = 1
            mask[mask <  thres] = 0

            mask = np.array(mask, dtype=np.uint8)
            mask = fslimage.Image(mask, xform=xform)

            mask.save(maskfile)

    return maskfile


def _eval_mask_query(
        stdout, atlas, query, use_label, q_type, q_in, res, o_type):

    maskimg = fslimage.Image(query)
    aimg    = _get_atlas(atlas, use_label, res)
    prob    = aimg.desc.atlasType == 'probabilistic'

    def evalNormalOutput(explabels, expprops):

        assert 'mask {}'.format(op.abspath(query)) in stdout

        if len(explabels) == 0:
            assert 'No results' in stdout
            return

        lines = stdout.split('\n')

        for explabel, expprop in zip(explabels, expprops):
            hits = [l for l in lines if explabel.name + ' ' in l]

            if expprop == 0:
                assert len(hits) == 0
                continue

            assert len(hits) == 1
            line = hits[0]

            assert '{:0.4f}'.format(expprop)        in line
            assert ' {} '   .format(explabel.index) in line
            if prob:
                assert ' {} '.format(explabel.index + 1) in line

    def evalShortOutput(explabels, expprops):

        explabels = [l.name for l in explabels]

        exp = ['mask', op.abspath(query)]

        for expprop, explabel in reversed(sorted(zip(expprops, explabels))):
            if expprop > 0:
                exp.append('{} {:0.4f}'.format(explabel, expprop))

        _stdout = re.sub(r'\s+', ' ', stdout).strip()
        assert _stdout == ' '.join(exp)

    if isinstance(aimg, fslatlases.LabelAtlas):
        try:
            explabels, expprops = aimg.maskLabel(maskimg)
            if prob: explabels = [aimg.desc.labels[i - 1] for i in explabels]
            else:    explabels = [aimg.desc.labels[i]     for i in explabels]
        except fslatlases.MaskError:
            explabels, expprops = [], []
    elif isinstance(aimg, fslatlases.ProbabilisticAtlas):
        try:
            expprops  = aimg.maskValues(maskimg)
            explabels = aimg.desc.labels
        except fslatlases.MaskError:
            explabels = []
            expprops  = []

    if q_in == 'out':
        assert stdout.strip() == 'Mask is not in the same space as atlas'
        return

    if o_type == 'normal': evalNormalOutput(explabels, expprops)
    else:                  evalShortOutput( explabels, expprops)



def _build_command_line(atlas, query, use_label, q_type, res, o_type):

    cmd = ['query', atlas, '-r', str(res)]

    if use_label:         cmd.append('-l')
    if o_type == 'short': cmd.append('-s')

    if   q_type.startswith('mask'):
        cmd += ['-m', query]
    elif q_type == 'voxel':
        cmd += ['-v'] + '{} {} {}'.format(*query).split()
    elif q_type == 'coordinate':
        cmd += ['-c'] + '{} {} {}'.format(*query).split()

    return cmd


def test_bad_mask(seed):

    fslatlases.rescanAtlases()
    capture  = CaptureStdout()

    with tempdir() as td:

        for atlasID, use_label in it.product(atlases, use_labels):

            atlas  = fslatlases.loadAtlas(
                atlasID,
                loadSummary=use_label,
                loadData=False,
                calcRange=False)
            ashape = list(atlas.shape[:3])

            wrongdims  = fslimage.Image(
                np.array(np.random.random(list(ashape) + [2]),
                            dtype=np.float32))
            wrongspace = fslimage.Image(
                np.random.random((20, 20, 20)),
                xform=affine.concat(atlas.voxToWorldMat,
                                    np.diag([2, 2, 2, 1])))

            print(wrongdims.shape)
            print(wrongspace.shape)

            wrongdims .save('wrongdims.nii.gz')
            wrongspace.save('wrongspace.nii.gz')

            cmd      = ['query', atlasID, '-m', 'wrongdims']
            expected = 'Mask has wrong number of dimensions'
            capture.reset()
            with capture:
                assert fslatlasq.main(cmd) != 0
            assert capture.stdout.strip() == expected

            cmd      = ['query', atlasID, '-m', 'wrongspace']
            expected = 'Mask is not in the same space as atlas'
            capture.reset()
            with capture:
                assert fslatlasq.main(cmd) != 0
            assert capture.stdout.strip() == expected
