#!/usr/bin/env python
#
# test_wrappers.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path   as op
import itertools as it

import fsl.wrappers                       as fw
import fsl.utils.assertions               as asrt
import fsl.utils.run                      as run

from . import mockFSLDIR


def checkResult(cmd, base, args, stripdir=None):
    """We can't control the order in which command line args are generated,
    so we need to test all possible orderings.

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


def test_bet():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('bet',)) as fsldir:
        bet      = op.join(fsldir, 'bin', 'bet')
        result   = fw.bet('input', 'output', mask=True, c=(10, 20, 30))
        expected = (bet + ' input output', ('-m', '-c 10 20 30'))
        assert checkResult(result.output[0], *expected, stripdir=[2])


def test_robustfov():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('robustfov',)) as fsldir:
        rfov     = op.join(fsldir, 'bin', 'robustfov')
        result   = fw.robustfov('input', 'output', b=180)
        expected = (rfov + ' -i input', ('-r output', '-b 180'))
        assert checkResult(result.output[0], *expected)


def test_eddy_cuda():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('eddy_cuda',)) as fsldir:
        eddy     = op.join(fsldir, 'bin', 'eddy_cuda')
        result   = fw.eddy_cuda('imain', 'mask', 'index', 'acqp',
                                'bvecs', 'bvals', 'out', dont_mask_output=True)
        expected = (eddy, ('--imain=imain',
                           '--mask=mask',
                           '--index=index',
                           '--acqp=acqp',
                           '--bvecs=bvecs',
                           '--bvals=bvals',
                           '--out=out',
                           '--dont_mask_output'))

        assert checkResult(result.output[0], *expected)


def test_topup():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('topup',)) as fsldir:
        topup    = op.join(fsldir, 'bin', 'topup')
        result   = fw.topup('imain', 'datain', minmet=1)
        expected = topup + ' --imain=imain --datain=datain --minmet=1'
        assert result.output[0] == expected


def test_flirt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('flirt',)) as fsldir:
        flirt    = op.join(fsldir, 'bin', 'flirt')
        result   = fw.flirt('src', 'ref', usesqform=True, anglerep='euler')
        expected = (flirt + ' -in src -ref ref',
                    ('-usesqform', '-anglerep euler'))
        assert checkResult(result.output[0], *expected)


def test_applyxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('flirt',)) as fsldir:
        flirt    = op.join(fsldir, 'bin', 'flirt')
        result   = fw.applyxfm('src', 'ref', 'mat', 'out', interp='trilinear')
        expected = (flirt + ' -in src -ref ref',
                    ('-applyxfm',
                     '-out out',
                     '-init mat',
                     '-interp trilinear'))
        assert checkResult(result.output[0], *expected)


def test_invxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convert_xfm',)) as fsldir:
        cnvxfm   = op.join(fsldir, 'bin', 'convert_xfm')
        result   = fw.invxfm('mat', 'output')
        expected = cnvxfm + ' -omat output -inverse mat'
        assert result.output[0] == expected


def test_concatxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convert_xfm',)) as fsldir:
        cnvxfm   = op.join(fsldir, 'bin', 'convert_xfm')
        result   = fw.concatxfm('mat1', 'mat2', 'output')
        expected = cnvxfm + ' -omat output -concat mat2 mat1'
        assert result.output[0] == expected


def test_mcflirt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('mcflirt',)) as fsldir:
        mcflirt  = op.join(fsldir, 'bin', 'mcflirt')
        result   = fw.mcflirt('input', out='output', cost='normcorr', dof=12)
        expected = (mcflirt + ' -in input',
                    ('-out output',
                     '-cost normcorr',
                     '-dof 12'))
        assert checkResult(result.output[0], *expected)


def test_fnirt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fnirt',)) as fsldir:
        fnirt    = op.join(fsldir, 'bin', 'fnirt')
        result   = fw.fnirt('src', ref='ref', iout='iout', fout='fout',
                            subsamp=(8, 6, 4, 2))
        expected = (fnirt + ' --in=src',
                    ('--ref=ref',
                     '--iout=iout',
                     '--fout=fout',
                     '--subsamp=8,6,4,2'))
        assert checkResult(result.output[0], *expected)


def test_applywarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('applywarp',)) as fsldir:
        applywarp = op.join(fsldir, 'bin', 'applywarp')
        result    = fw.applywarp('src', 'ref', 'out', warp='warp', abs=True, super=True)
        expected  = (applywarp + ' --in=src --ref=ref --out=out',
                     ('--warp=warp', '--abs', '--super'))
        assert checkResult(result.output[0], *expected)


def test_invwarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('invwarp',)) as fsldir:
        invwarp  = op.join(fsldir, 'bin', 'invwarp')
        result   = fw.invwarp('warp', 'ref', 'out',
                              rel=True, noconstraint=True)
        expected = (invwarp + ' --warp=warp --ref=ref --out=out',
                     ('--rel', '--noconstraint'))
        assert checkResult(result.output[0], *expected)


def test_convertwarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convertwarp',)) as fsldir:
        cnvwarp  = op.join(fsldir, 'bin', 'convertwarp')
        result   = fw.convertwarp('out', 'ref', absout=True, jacobian='jacobian')
        expected = (cnvwarp + ' --ref=ref --out=out',
                     ('--absout', '--jacobian=jacobian'))
        assert checkResult(result.output[0], *expected)


def test_fugue():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fugue',)) as fsldir:
        fugue    = op.join(fsldir, 'bin', 'fugue')
        result   = fw.fugue(input='input', warp='warp',
                            median=True, dwell=10)
        expected = (fugue, ('--in=input',
                            '--warp=warp',
                            '--median',
                            '--dwell=10'))
        assert checkResult(result.output[0], *expected)



def test_sigloss():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('sigloss',)) as fsldir:
        sigloss  = op.join(fsldir, 'bin', 'sigloss')
        result   = fw.sigloss('input', 'sigloss', mask='mask', te=0.5)
        expected = (sigloss + ' --in input --sigloss sigloss',
                    ('--mask mask', '--te 0.5'))
        assert checkResult(result.output[0], *expected)


def test_melodic():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('melodic',)) as fsldir:
        melodic  = op.join(fsldir, 'bin', 'melodic')
        result   = fw.melodic('input', dim=50, mask='mask', Oall=True)
        expected = (melodic + ' --in=input',
                    ('--dim=50', '--mask=mask', '--Oall'))
        assert checkResult(result.output[0], *expected)


def test_fsl_regfilt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fsl_regfilt',)) as fsldir:
        regfilt  = op.join(fsldir, 'bin', 'fsl_regfilt')
        result   = fw.fsl_regfilt('input', 'output', 'design',
                                  filter=(1, 2, 3, 4), vn=True)
        expected = (regfilt + ' --in=input --out=output --design=design',
                    ('--filter=1,2,3,4', '--vn'))
        assert checkResult(result.output[0], *expected)



def test_fslreorient2std():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslreorient2std',)) as fsldir:
        r2std    = op.join(fsldir, 'bin', 'fslreorient2std')
        result   = fw.fslreorient2std('input', 'output')
        expected = r2std + ' input output'
        assert result.output[0] == expected


def test_fslroi():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslroi',)) as fsldir:
        fslroi   = op.join(fsldir, 'bin', 'fslroi')

        result   = fw.fslroi('input', 'output', 1, 10)
        expected = fslroi + ' input output 1 10'
        assert result.output[0] == expected

        result   = fw.fslroi('input', 'output', 1, 10, 2, 20, 3, 30)
        expected = fslroi + ' input output 1 10 2 20 3 30'
        assert result.output[0] == expected

        result   = fw.fslroi('input', 'output', 1, 10, 2, 20, 3, 30, 4, 40)
        expected = fslroi + ' input output 1 10 2 20 3 30 4 40'
        assert result.output[0] == expected


def test_slicer():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('slicer',)) as fsldir:
        slicer   = op.join(fsldir, 'bin', 'slicer')
        result   = fw.slicer('input1', 'input2', i=(20, 100), x=(20, 'x.png'))
        expected = slicer + ' input1 input2 -i 20 100 -x 20 x.png'
        assert result.output[0] == expected


def test_cluster():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('cluster',)) as fsldir:
        cluster  = op.join(fsldir, 'bin', 'cluster')
        result   = fw.cluster('input', 'thresh',
                              fractional=True, osize='osize')
        expected = (cluster + ' --in=input --thresh=thresh',
                    ('--fractional', '--osize=osize'))
        assert checkResult(result.output[0], *expected)


def test_fslmaths():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslmaths',)) as fsldir:
        cmd    = op.join(fsldir, 'bin', 'fslmaths')
        result = fw.fslmaths('input') \
            .abs().bin().binv().recip().Tmean().Tstd().Tmin().Tmax() \
            .fillh().ero().dilM().dilF().add('addim').sub('subim') \
            .mul('mulim').div('divim').mas('masim').rem('remim')   \
            .thr('thrim').uthr('uthrim').inm('inmim').bptf(1, 10).run('output')

        expected = [cmd, 'input',
                    '-abs', '-bin', '-binv', '-recip', '-Tmean', '-Tstd',
                    '-Tmin', '-Tmax', '-fillh', '-ero', '-dilM', '-dilF',
                    '-add addim', '-sub subim', '-mul mulim', '-div divim',
                    '-mas masim', '-rem remim', '-thr thrim', '-uthr uthrim',
                    '-inm inmim', '-bptf 1 10', 'output']
        expected = ' '.join(expected)

        assert result.output[0] == expected

        # TODO test LOAD output

def test_fast():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fast',)) as fsldir:

        cmd = op.join(fsldir, 'bin', 'fast')

        result   = fw.fast('input', 'myseg', n_classes=3)
        expected = [cmd, '-v', '--out=myseg', '--class=3', 'input']

        assert result.output[0] == ' '.join(expected)

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3)
        expected = [cmd, '-v', '--out=myseg', '--class=3', 'in1', 'in2', 'in3']

        assert result.output[0] == ' '.join(expected)



def test_fsl_anat():
    with asrt.disabled(), \
         run.dryrun(), \
         mockFSLDIR(bin=('fsl_anat',)) as fsldir:

        cmd = op.join(fsldir, 'bin', 'fsl_anat')

        result   = fw.fsl_anat('t1', out='fsl_anat', bias_smoothing=25)
        expected = [cmd, '-i', 't1', '-o', 'fsl_anat', '-t', 'T1',
                    '-s', '25']

        assert result.output[0] == ' '.join(expected)
