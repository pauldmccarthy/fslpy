#!/usr/bin/env python
#
# test_imagewrapper.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>



import              collections
import              random
import itertools as it
import numpy     as np


import fsl.data.image        as image
import fsl.data.imagewrapper as imagewrap


def setup_module():
    pass

def teardown_module():
    pass


def random_coverage(shape):
    
    ndims = len(shape) - 1
    nvols = shape[-1]

    print '{}D (shape: {}, {} vectors/slices/volumes)'.format(ndims, shape, nvols)

    # Generate a random coverage. 
    # We use the same coverage for
    # each vector/slice/volume, so
    # are not fully testing the function.
    coverage = np.zeros((2, ndims, nvols), dtype=np.uint32)

    for dim in range(ndims):
        dsize = shape[dim]

        # Random low/high indices for each dimension.
        low  = np.random.randint(0, dsize)

        # We have to make sure that the coverage is not
        # complete, as some of the tests will fail if
        # the coverage is complete. 
        if low == 0: high = np.random.randint(low + 1, dsize)
        else:        high = np.random.randint(low + 1, dsize + 1)

        coverage[0, dim, :] = low
        coverage[1, dim, :] = high
 
    return coverage


def random_slices(coverage, shape, mode):

    ndims = len(shape) - 1
    nvols = shape[-1]
    
    slices = np.zeros((2, len(shape)))

    for dim, size in enumerate(shape):

        # Volumes 
        if dim == ndims:
            lowCover  = np.random.randint(0,            nvols)
            highCover = np.random.randint(lowCover + 1, nvols + 1) 

            slices[:, dim] = lowCover, highCover
            continue

        # Assuming that coverage is same for each volume
        lowCover  = coverage[0, dim, 0]
        highCover = coverage[1, dim, 0]
        
        # Generate some slices that will
        # be contained within the coverage
        if mode == 'in':
            lowSlice  = np.random.randint(lowCover,     highCover)
            highSlice = np.random.randint(lowSlice + 1, highCover + 1)

        # Generate some indices which will
        # randomly overlap with the coverage
        # (if it is possible to do so)
        elif mode == 'overlap':

            if highCover == size: lowSlice = np.random.randint(0, lowCover)
            else:                 lowSlice = np.random.randint(0, highCover)

            if lowSlice < lowCover: highSlice = np.random.randint(lowCover  + 1, size + 1)
            else:                   highSlice = np.random.randint(highCover + 1, size + 1)

        elif mode == 'out':

            # The coverage is full, so we can't
            # generate an outside range 
            if lowCover == 0 and highCover == size:
                lowSlice  = np.random.randint(lowCover,     highCover)
                highSlice = np.random.randint(lowSlice + 1, highCover + 1)

            # If low coverage is 0, the slice
            # must be above the coverage
            elif lowCover == 0:
                lowSlice  = np.random.randint(highCover,    size)
                highSlice = np.random.randint(lowSlice + 1, size + 1)

            # If high coverage is size, the
            # slice must be below the coverage
            elif highCover == size:
                lowSlice  = np.random.randint(0,            lowCover)
                highSlice = np.random.randint(lowSlice + 1, lowCover + 1)
                
            # Otherwise the slice could be
            # below or above the coverage
            else:
                lowSlice = random.choice((np.random.randint(0,         lowCover),
                                          np.random.randint(highCover, size)))

                if    lowSlice < lowCover: highSlice = np.random.randint(lowSlice + 1, lowCover + 1)
                else:                      highSlice = np.random.randint(lowSlice + 1, size     + 1)


        slices[0, dim] = lowSlice
        slices[1, dim] = highSlice

    slices = [tuple(map(int, pair)) for pair in slices.T]
    return slices


def test_sliceObjToSliceTuple():

    func  = imagewrap.sliceObjToSliceTuple
    shape = (10, 10, 10)


    assert func( 2,                                       shape) == ((2, 3),  (0, 10), (0, 10))
    assert func( slice(None),                             shape) == ((0, 10), (0, 10), (0, 10))
    assert func((slice(None), slice(None),  slice(None)), shape) == ((0, 10), (0, 10), (0, 10))
    assert func((9,           slice(None),  slice(None)), shape) == ((9, 10), (0, 10), (0, 10))
    assert func((slice(None), 5,            slice(None)), shape) == ((0, 10), (5, 6),  (0, 10))
    assert func((slice(None), slice(None),  3),           shape) == ((0, 10), (0, 10), (3, 4))
    assert func((slice(4, 6), slice(None),  slice(None)), shape) == ((4, 6),  (0, 10), (0, 10))
    assert func((8,           slice(1, 10), slice(None)), shape) == ((8, 9),  (1, 10), (0, 10))



def test_sliceTupleToSliceObj():

    func  = imagewrap.sliceTupleToSliceObj
    shape = (10, 10, 10)

    for x1, y1, z1 in it.product(*[range(d - 1) for d in shape]):

        for x2, y2, z2 in it.product(*[range(s + 1, d) for s, d in zip((x1, y1, z1), shape)]):

            slices   = [[x1, x2], [y1, y2], [z1, z2]]
            sliceobj = (slice(x1, x2, 1), slice(y1, y2, 1), slice(z1, z2, 1))

            assert func(slices) == sliceobj


def test_adjustCoverage():

    # TODO Randomise

    # Each test is a tuple of (coverage, expansion, expectedResult) 
    tests = [([[3, 5], [2, 6]], [[6, 7], [8,  10]],         [[3, 7], [2, 10]]),
             ([[0, 0], [0, 0]], [[1, 2], [3,  5]],          [[0, 2], [0, 5]]),
             ([[2, 3], [0, 6]], [[1, 5], [4,  10]],         [[1, 5], [0, 10]]),
             ([[0, 1], [0, 1]], [[0, 7], [19, 25], [0, 1]], [[0, 7], [0, 25]]),
    ]

    for coverage, expansion, result in tests:

        result   = np.array(result)  .T
        coverage = np.array(coverage).T

        assert np.all(imagewrap.adjustCoverage(coverage, expansion) == result)


def test_sliceCovered():

    # A bunch of random coverages
    for i in range(500):

        # 2D, 3D or 4D?
        # ndims is the number of dimensions
        # in one vector/slice/volume
        ndims = random.choice((2, 3, 4)) - 1

        # Shape of one vector[2D]/slice[3D]/volume[4D]
        shape = np.random.randint(5, 100, size=ndims + 1)

        # Number of vectors/slices/volumes
        nvols = shape[-1]

        coverage = random_coverage(shape)

        # Generate some slices that should
        # be contained within the coverage
        for j in range(500):
            slices = random_slices(coverage, shape, 'in')
            assert imagewrap.sliceCovered(slices, coverage, shape)

        # Generate some slices that should
        # overlap with the coverage 
        for j in range(500):
            slices = random_slices(coverage, shape, 'overlap')
            assert not imagewrap.sliceCovered(slices, coverage, shape)

        # Generate some slices that should
        # be outside of the coverage 
        for j in range(500):
            slices = random_slices(coverage, shape, 'out')
            assert not imagewrap.sliceCovered(slices, coverage, shape) 



# The sum of the coverage ranges + the
# expansion ranges should be equal to
# the coverage, expanded to include the
# original slices (or the expansions
# - should be equivalent). Note that
# if imagewrapper.adjustCoverage is
# broken, this validation will also be
# broken.
def _test_expansion(coverage, slices, volumes, expansions):
    ndims = coverage.shape[1]

    print
    print 'Slice:    "{}"'.format(" ".join(["{:2d} {:2d}".format(l, h) for l, h in slices]))

    # Bin the expansions by volume
    expsByVol = collections.defaultdict(list)
    for vol, exp in zip(volumes, expansions):
        print '  {:3d}:    "{}"'.format(vol, " ".join(["{:2d} {:2d}".format(l, h) for l, h in exp]))
        expsByVol[vol].append(exp)

    for vol, exps in expsByVol.items():

        # Figure out what the adjusted
        # coverage should look like (assumes
        # that adjustCoverage is working).
        oldCoverage  = coverage[..., vol]
        newCoverage  = imagewrap.adjustCoverage(oldCoverage, slices)

        nc = newCoverage

        dimranges = []
        for d in range(ndims):
            dimranges.append(np.arange(nc[0, d], nc[1, d]))

            points = it.product(*dimranges)

        for point in points:

            # Is this point in the old coverage?
            covered = True
            for dim in range(ndims):
                covLow, covHigh = oldCoverage[:, dim]

                if point[dim] < covLow or point[dim] > covHigh:
                    covered = False
                    break

            if covered:
                break

            # Is this point in any of the expansions
            covered = [False] * len(exps)
            for i, exp in enumerate(exps):
                
                covered[i] = True
                
                for dim in range(ndims):

                    expLow, expHigh = exp[dim]
                    if point[dim] < expLow or point[dim] > expHigh:
                        covered[i] = False
                        break
                    
            if not any(covered):
                raise AssertionError(point)

                
def test_calcSliceExpansion():

    for i in range(500):

        ndims    = 3 # random.choice((2, 3, 4)) - 1
        shape    = np.random.randint(5, 100, size=ndims + 1)
        coverage = random_coverage(shape)

        cov = [(lo, hi) for lo, hi in coverage[:, :, 0].T]

        print 'Shape:    {}'.format(shape)
        print 'Coverage: {}'.format(cov)

        print
        print '-- In --'
        for j in range(250):
            slices     = random_slices(coverage, shape, 'in')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)
            
        print
        print '-- Overlap --' 
        for j in range(250):
            slices     = random_slices(coverage, shape, 'overlap')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)

        print
        print '-- Out --' 
        for j in range(250):
            slices     = random_slices(coverage, shape, 'out')
            vols, exps = imagewrap.calcExpansion(slices, coverage)
            _test_expansion(coverage, slices, vols, exps)
