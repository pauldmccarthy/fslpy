#!/usr/bin/env python
#
# test_fslsub.py - Tests functions in the fsl.utils.fslsub module.
#
# Author: Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>
#

from fsl.utils import fslsub


def test_flatten_jobids():
    job_ids = ('12', '27', '35', '41', 721)
    res = '12,27,35,41,721'

    assert fslsub._flatten_job_ids(job_ids) == res
    assert fslsub._flatten_job_ids(job_ids[::-1]) == res
    assert fslsub._flatten_job_ids('12') == '12'
    assert fslsub._flatten_job_ids([job_ids[:2], job_ids[2:]]) == res
    assert fslsub._flatten_job_ids([set(job_ids[:2]), job_ids[2:]]) == res
    assert fslsub._flatten_job_ids(((job_ids, ), job_ids + job_ids)) == res
