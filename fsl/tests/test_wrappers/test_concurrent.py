#!/usr/bin/env python


import glob
import os
import os.path as op
import multiprocessing as mp
import shutil

from fsl.data.image import removeExt
from fsl.utils.tempdir import tempdir
from fsl.wrappers import bet


datadir = op.join(op.dirname(__file__), '..', 'testdata')


def test_wrappers_concurrent():
    exfunc = op.join(datadir, 'example_func.nii.gz')
    with tempdir():
        for i in range(1, 11):
            shutil.copy(exfunc, f'{i:02d}.nii.gz')
        infiles   = list(glob.glob('??.nii.gz'))
        basenames = [removeExt(f) for f in infiles]
        outfiles  = [f'{bn}_brain.nii.gz' for bn in basenames]

        os.environ['FSLOUTPUTTYPE'] = 'NIFTI_GZ'

        with mp.Pool(len(infiles)) as pool:
            args = zip(infiles, outfiles)
            pool.starmap(bet, args)

        assert all(op.exists(f) for f in outfiles)
