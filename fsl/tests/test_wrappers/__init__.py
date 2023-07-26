#!/usr/bin/env python


import              contextlib
import os.path   as op
import itertools as it

import fsl.utils.assertions as asrt
import fsl.utils.run        as run

from .. import mockFSLDIR


def checkResult(cmd, base, args, stripdir=None):
    """Check that the generate dcommand matches the expected command.

    Pre python 3.7, we couldn't control the order in which command
    line args were generated, so we needed to test all possible orderings.

    But for Python >= 3.7, the order in which kwargs are passed will
    be the same as the order in which they are rendered, so this function
    is not required.

    :arg cmd:      Generated command
    :arg base:     Beginning of expected command
    :arg args:     Sequence of expected arguments
    :arg stripdir: Sequence of indices indicating arguments
                   for whihc any leading directory should be ignored.
    """

    if stripdir is not None:
        cmd = list(cmd.split())
        for si in stripdir:
            cmd[si] = op.basename(cmd[si])
        cmd = ' '.join(cmd)

    permutations = it.permutations(args, len(args))
    possible     = [' '.join([base] + list(p))  for p in permutations]

    return any([cmd == p for p in possible])


@contextlib.contextmanager
def testenv(*fslexes):
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=fslexes) as fsldir:
        fslexes = [op.join(fsldir, 'bin', e) for e in fslexes]
        if len(fslexes) == 1: yield fslexes[0]
        else:                 yield fslexes
