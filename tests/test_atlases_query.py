#!/usr/bin/env python
#
# test_atlases_query.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import                    os
import itertools       as it
import numpy           as np
import                    pytest


import fsl.data.atlases    as fslatlases
import fsl.data.image      as fslimage
import fsl.utils.transform as transform
import fsl.utils.cache     as cache

from . import (testdir, make_random_mask)


pytestmark = pytest.mark.fsltest


def setup_module():
    if os.environ.get('FSLDIR', None) is None:
        raise Exception('FSLDIR is not set - atlas tests cannot be run')
    fslatlases.rescanAtlases()


# why this is not built into
# in itertools i don't even
def _repeat(iterator, n):
    for elem in iterator:
        for i in range(n):
            yield elem


_atlases = cache.Cache()
def _get_atlas(atlasID, res, summary=False):
    atlas = _atlases.get((atlasID, res, summary), default=None)
    if atlas is None:
        if summary or atlasID in ('talairach', 'striatum-structural',
                                  'jhu-labels', 'smatt'):
            kwargs = {}
        else:
            kwargs = {'loadData'  : False,
                      'calcRange' : False,
                      'indexed'   : True}

        atlas = fslatlases.loadAtlas(atlasID,
                                     loadSummary=summary,
                                     resolution=res,
                                     **kwargs)
        _atlases.put((atlasID, res, summary), atlas)

    return atlas

def _random_atlas(atype, res, summary=False):

    if atype == 'prob':
        atype = 'probabilistic'

    atlases = fslatlases.listAtlases()
    atlases = [a for a in atlases if a.atlasType == atype]
    desc    = atlases[np.random.randint(0, len(atlases))]
    return _get_atlas(desc.atlasID, res, summary)


# Generate a mask which tells us which
# voxels in the atlas are all zeros
_zero_masks = cache.Cache(maxsize=5)
def _get_zero_mask(aimg):

    atlasID = aimg.desc.atlasID
    res     = aimg.pixdim[0]
    summary = isinstance(aimg, fslatlases.LabelAtlas) \
              and aimg.desc.atlasType == 'probabilistic'

    zmask = _zero_masks.get((atlasID, summary, res), None)

    if zmask is None:
        if isinstance(aimg, fslatlases.LabelAtlas):
            zmask = aimg[:] == 0
        elif isinstance(aimg, fslatlases.ProbabilisticAtlas):

            # Keep memory usage down
            zmask = np.ones(aimg.shape[:3], dtype=np.bool)
            for vol in range(aimg.shape[-1]):
                zmask = np.logical_and(zmask, aimg[..., vol] == 0)

        _zero_masks[atlasID, summary, res] = zmask

    return zmask


def test_label_coord_query(  seed): _test_query('coord', 'label')
def test_label_voxel_query(  seed): _test_query('voxel', 'label')
@pytest.mark.longtest
def test_label_mask_query(   seed): _test_query('mask',  'label')
def test_summary_coord_query(seed): _test_query('coord', 'prob', summary=True)
def test_summary_voxel_query(seed): _test_query('voxel', 'prob', summary=True)
@pytest.mark.longtest
def test_summary_mask_query( seed): _test_query('mask',  'prob', summary=True)
def test_prob_coord_query(   seed): _test_query('coord', 'prob')
def test_prob_voxel_query(   seed): _test_query('voxel', 'prob')
@pytest.mark.longtest
def test_prob_mask_query(    seed): _test_query('mask',  'prob')


# qtype: (voxel|coord|mask)
# atype: (label|prob)
def _test_query(qtype, atype, summary=False):

    qins  = ['in', 'zero', 'out']
    reses = [1, 2]

    if qtype == 'mask': maskreses = [1, 2]
    else:               maskreses = [1]

    tests = _repeat(it.product(qins, reses, maskreses), 5)

    for qin, res, maskres in tests:

        atlas = _random_atlas(atype, res=res, summary=summary)

        with testdir():

            if qtype in ('voxel', 'coord'):
                genfunc  = _gen_coord_voxel_query
                evalfunc = _eval_coord_voxel_query
            else:
                genfunc  = _gen_mask_query
                evalfunc = _eval_mask_query

            print('Test: {} {}mm type={} in={}'.format(
                atlas.desc.atlasID, res, qtype, qin))

            query = genfunc(atlas, qtype, qin, maskres=maskres)
            evalfunc(atlas, query, qtype, qin)


# Generate a random voxel/world space
# coordinate to query the given atlas.
def _gen_coord_voxel_query(atlas, qtype, qin, **kwargs):

    voxel = qtype == 'voxel'

    if voxel: dtype = int
    else:     dtype = float

    if qin == 'out':

        if voxel:
            dlo = (0, 0, 0)
            dhi = atlas.shape
        else:
            dlo, dhi = transform.axisBounds(atlas.shape, atlas.voxToWorldMat)

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
        zmask = _get_zero_mask(atlas)

        # get indices to voxels which are
        # either all zero, or which are
        # not all all zero, depending on
        # the value of q_in
        if qin == 'in': zidxs = np.where(zmask == 0)
        else:           zidxs = np.where(zmask)

        # Randomly choose a voxel
        cidx   = np.random.randint(0, len(zidxs[0]))
        coords = [zidxs[0][cidx], zidxs[1][cidx], zidxs[2][cidx]]
        coords = np.array(coords, dtype=dtype)

        if not voxel:
            coords = transform.transform(coords, atlas.voxToWorldMat)

    return tuple([dtype(c) for c in coords])


def _eval_coord_voxel_query(atlas, query, qtype, qin):

    voxel = qtype == 'voxel'

    if voxel: vx, vy, vz = query
    else:     vx, vy, vz = transform.transform(query, atlas.worldToVoxMat)

    vx, vy, vz = [int(round(v)) for v in [vx, vy, vz]]

    def evalLabel():
        if qin in ('in', 'zero'): expval = atlas[vx, vy, vz]
        else:                     expval = None

        assert atlas.label(     query, voxel=voxel) == expval
        assert atlas.coordLabel(query, voxel=voxel) == expval

    def evalProb():
        if qin in ('in', 'zero'):
            expval = atlas[vx, vy, vz, :]
            expval = [expval[l.index] for l in atlas.desc.labels]
        elif qin == 'out':
            expval = []

        assert atlas.proportions(     query, voxel=voxel) == expval
        assert atlas.coordProportions(query, voxel=voxel) == expval

    if   isinstance(atlas, fslatlases.LabelAtlas):         evalLabel()
    elif isinstance(atlas, fslatlases.ProbabilisticAtlas): evalProb()


def _gen_mask_query(atlas, qtype, qin, maskres):

    maskfile = 'mask.nii.gz'
    res      = atlas.pixdim[0]

    if qin == 'out':
        make_random_mask(maskfile, (20, 20, 20), np.eye(4))
        return maskfile

    zmask = _get_zero_mask(atlas)

    if qin == 'in':
        zmask = zmask == 0

    mask = make_random_mask(
        maskfile, atlas.shape[:3], atlas.voxToWorldMat, zmask)

    # Make sure that when the mask gets
    # resampled into the atlas resolution,
    # it is still either in or out of the
    # atlas space
    if maskres != res:
        a       = _get_atlas(atlas.desc.atlasID, maskres, True)
        a_zmask = _get_zero_mask(a)

        if qin == 'in':
            a_zmask = a_zmask == 0

        # use linear interp and threshold
        # aggresively to make sure there
        # is no overlap between the different
        # resolutions
        mask, xform = mask.resample(a.shape[:3], dtype=np.float32, order=1)

        mask[mask   < 1.0] = 0
        mask[a_zmask == 0] = 0

        mask = np.array(mask, dtype=np.uint8)
        mask = fslimage.Image(mask, xform=xform)

        mask.save(maskfile)

    return maskfile


def _eval_mask_query(atlas, query, qtype, qin):

    mask    = fslimage.Image(query)
    prob    = atlas.desc.atlasType == 'probabilistic'
    maskres = mask .pixdim[0]
    res     = atlas.pixdim[0]

    if maskres == res:
        rmask = mask[:]
    else:
        rmask = mask.resample(atlas.shape[:3], dtype=np.float32, order=0)[0]

    rmask = np.array(rmask, dtype=np.bool)

    def evalLabel():

        if qin == 'out':
            with pytest.raises(fslatlases.MaskError): atlas.maskLabel(mask)
            with pytest.raises(fslatlases.MaskError): atlas.label(    mask)
            return

        if qin == 'in':

            voxels    = np.array(np.where(rmask)).T
            maxval    = int(atlas[:].max())
            valcounts = np.zeros((maxval + 1, ))
            nvoxels   = voxels.shape[0]

            for x, y, z in voxels:
                x, y, z = [int(v) for v in [x, y, z]]
                valcounts[int(atlas[x, y, z])] += 1.0

            # make sure the values are sorted
            # according to their atlas ordering
            expvals   = np.where(valcounts > 0)[0]
            explabels = []

            # There may be more values in an image
            # than are listed in the atlas spec :(
            for v in expvals:
                try:             explabels.append(atlas.find(value=int(v)))
                except KeyError: pass
            explabels = list(sorted(explabels))
            expvals   = [l.value for l in explabels]
            expprops  = [100 * valcounts[v] / nvoxels for v in expvals]

        else:
            if prob:
                expvals  = []
                expprops = []
            else:
                allvals = [l.value for l in atlas.desc.labels]
                if 0 in allvals:
                    expvals  = [0]
                    expprops = [100]
                else:
                    expvals  = []
                    expprops = []

        vals,  props  = atlas.    label(mask)
        vals2, props2 = atlas.maskLabel(mask)

        assert np.all(np.isclose(vals,  vals2))
        assert np.all(np.isclose(props, props2))
        assert np.all(np.isclose(vals,  expvals))
        assert np.all(np.isclose(props, expprops))

    def evalProb():

        if qin == 'out':
            with pytest.raises(fslatlases.MaskError):
                atlas.maskProportions(mask)
            with pytest.raises(fslatlases.MaskError):
                atlas.proportions(    mask)
            return

        props  = atlas.    proportions(mask)
        props2 = atlas.maskProportions(mask)

        assert np.all(np.isclose(props, props2))

    if   isinstance(atlas, fslatlases.LabelAtlas):         evalLabel()
    elif isinstance(atlas, fslatlases.ProbabilisticAtlas): evalProb()
