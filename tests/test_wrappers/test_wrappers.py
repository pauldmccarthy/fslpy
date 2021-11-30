#!/usr/bin/env python
#
# test_wrappers.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path   as op
import itertools as it
import textwrap  as tw
import              os
import              shlex

import numpy as np

import fsl.wrappers                       as fw
import fsl.utils.assertions               as asrt
import fsl.utils.run                      as run
from fsl.utils.tempdir import tempdir

from .. import mockFSLDIR, make_random_image


def checkResult(cmd, base, args, stripdir=None):
    """Check that the generate dcommand matches the expected command.

    Pre python 3.7, we couldn't control the order in which command
    line args were generated, so we needed to test all possible orderings.

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
        assert checkResult(result.stdout[0], *expected, stripdir=[2])


def test_robustfov():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('robustfov',)) as fsldir:
        rfov     = op.join(fsldir, 'bin', 'robustfov')
        result   = fw.robustfov('input', 'output', b=180)
        expected = (rfov + ' -i input', ('-r output', '-b 180'))
        assert checkResult(result.stdout[0], *expected)


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

        assert checkResult(result.stdout[0], *expected)


def test_topup():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('topup',)) as fsldir:
        topup    = op.join(fsldir, 'bin', 'topup')
        result   = fw.topup('imain', 'datain', minmet=1)
        expected = topup + ' --imain=imain --datain=datain --minmet=1'
        assert result.stdout[0] == expected


def test_flirt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('flirt',)) as fsldir:
        flirt    = op.join(fsldir, 'bin', 'flirt')
        result   = fw.flirt('src', 'ref', usesqform=True, anglerep='euler')
        expected = (flirt + ' -in src -ref ref',
                    ('-usesqform', '-anglerep euler'))
        assert checkResult(result.stdout[0], *expected)


def test_epi_reg():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('epi_reg',)) as fsldir:
        epi_reg  = op.join(fsldir, 'bin', 'epi_reg')
        result   = fw.epi_reg('epi', 't1', 't1brain', 'out')
        expected = epi_reg + ' --epi=epi --t1=t1 --t1brain=t1brain --out=out'
        assert result.stdout[0] == expected


def test_applyxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('flirt',)) as fsldir:
        flirt    = op.join(fsldir, 'bin', 'flirt')
        result   = fw.applyxfm('src', 'ref', 'mat', 'out', interp='trilinear')
        expected = (flirt + ' -in src -ref ref',
                    ('-applyxfm',
                     '-out out',
                     '-init mat',
                     '-interp trilinear'))
        assert checkResult(result.stdout[0], *expected)


def test_applyxfm4D():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('applyxfm4D',)) as fsldir:
        applyxfm = op.join(fsldir, 'bin', 'applyxfm4D')
        result   = fw.applyxfm4D(
            'src', 'ref', 'out', 'mat', fourdigit=True, userprefix='boo')
        expected = (applyxfm + ' src ref out mat',
                    ('-fourdigit',
                     '-userprefix boo'))
        assert checkResult(result.stdout[0], *expected)


def test_invxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convert_xfm',)) as fsldir:
        cnvxfm   = op.join(fsldir, 'bin', 'convert_xfm')
        result   = fw.invxfm('mat', 'output')
        expected = cnvxfm + ' -omat output -inverse mat'
        assert result.stdout[0] == expected


def test_concatxfm():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convert_xfm',)) as fsldir:
        cnvxfm   = op.join(fsldir, 'bin', 'convert_xfm')
        result   = fw.concatxfm('mat1', 'mat2', 'output')
        expected = cnvxfm + ' -omat output -concat mat2 mat1'
        assert result.stdout[0] == expected


def test_mcflirt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('mcflirt',)) as fsldir:
        mcflirt  = op.join(fsldir, 'bin', 'mcflirt')
        result   = fw.mcflirt('input', out='output', cost='normcorr', dof=12)
        expected = (mcflirt + ' -in input',
                    ('-out output',
                     '-cost normcorr',
                     '-dof 12'))
        assert checkResult(result.stdout[0], *expected)


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
        assert checkResult(result.stdout[0], *expected)


def test_applywarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('applywarp',)) as fsldir:
        applywarp = op.join(fsldir, 'bin', 'applywarp')
        result    = fw.applywarp('src', 'ref', 'out', warp='warp', abs=True, super=True)
        expected  = (applywarp + ' --in=src --ref=ref --out=out',
                     ('--warp=warp', '--abs', '--super'))
        assert checkResult(result.stdout[0], *expected)


def test_invwarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('invwarp',)) as fsldir:
        invwarp  = op.join(fsldir, 'bin', 'invwarp')
        result   = fw.invwarp('warp', 'ref', 'out',
                              rel=True, noconstraint=True)
        expected = (invwarp + ' --warp=warp --ref=ref --out=out',
                     ('--rel', '--noconstraint'))
        assert checkResult(result.stdout[0], *expected)


def test_convertwarp():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('convertwarp',)) as fsldir:
        cnvwarp  = op.join(fsldir, 'bin', 'convertwarp')
        result   = fw.convertwarp('out', 'ref', absout=True, jacobian='jacobian')
        expected = (cnvwarp + ' --ref=ref --out=out',
                     ('--absout', '--jacobian=jacobian'))
        assert checkResult(result.stdout[0], *expected)


def test_fugue():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fugue',)) as fsldir:
        fugue    = op.join(fsldir, 'bin', 'fugue')
        result   = fw.fugue(input='input', warp='warp',
                            median=True, dwell=10)
        expected = (fugue, ('--in=input',
                            '--warp=warp',
                            '--median',
                            '--dwell=10'))
        assert checkResult(result.stdout[0], *expected)



def test_sigloss():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('sigloss',)) as fsldir:
        sigloss  = op.join(fsldir, 'bin', 'sigloss')
        result   = fw.sigloss('input', 'sigloss', mask='mask', te=0.5)
        expected = (sigloss + ' --in input --sigloss sigloss',
                    ('--mask mask', '--te 0.5'))
        assert checkResult(result.stdout[0], *expected)


def test_prelude():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('prelude',)) as fsldir:
        prelude  = op.join(fsldir, 'bin', 'prelude')
        result   = fw.prelude(complex='complex',
                              out='out',
                              labelslices=True,
                              start=5)
        expected = (prelude, ('--complex=complex',
                              '--out=out',
                              '--labelslices',
                              '--start=5'))
        assert checkResult(result.stdout[0], *expected)


def test_melodic():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('melodic',)) as fsldir:
        melodic  = op.join(fsldir, 'bin', 'melodic')
        result   = fw.melodic('input', dim=50, mask='mask', Oall=True)
        expected = (melodic + ' --in=input',
                    ('--dim=50', '--mask=mask', '--Oall'))
        assert checkResult(result.stdout[0], *expected)


def test_fsl_regfilt():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fsl_regfilt',)) as fsldir:
        regfilt  = op.join(fsldir, 'bin', 'fsl_regfilt')
        result   = fw.fsl_regfilt('input', 'output', 'design',
                                  filter=(1, 2, 3, 4), vn=True)
        expected = (regfilt + ' --in=input --out=output --design=design',
                    ('--filter=1,2,3,4', '--vn'))
        assert checkResult(result.stdout[0], *expected)


def test_fslorient():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslorient',)) as fsldir:
        fslo    = op.join(fsldir, 'bin', 'fslorient')
        result   = fw.fslorient('input', setsform=(-2, 0, 0, 90, 0, 2, 0, -126, 0, 0, 2, -72, 0, 0, 0, 1))
        expected = fslo + ' -setsform -2 0 0 90 0 2 0 -126 0 0 2 -72 0 0 0 1' + ' input'
        assert result.stdout[0] == expected

        result   = fw.fslorient('input', getorient=True)
        expected = fslo + ' -getorient' + ' input'
        assert result.stdout[0] == expected

        result   = fw.fslorient('input', setsformcode=1)
        expected = fslo + ' -setsformcode 1' + ' input'
        assert result.stdout[0] == expected


def test_fslreorient2std():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslreorient2std',)) as fsldir:
        r2std    = op.join(fsldir, 'bin', 'fslreorient2std')
        result   = fw.fslreorient2std('input', 'output')
        expected = r2std + ' input output'
        assert result.stdout[0] == expected


def test_fslroi():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslroi',)) as fsldir:
        fslroi   = op.join(fsldir, 'bin', 'fslroi')

        result   = fw.fslroi('input', 'output', 1, 10)
        expected = fslroi + ' input output 1 10'
        assert result.stdout[0] == expected

        result   = fw.fslroi('input', 'output', 1, 10, 2, 20, 3, 30)
        expected = fslroi + ' input output 1 10 2 20 3 30'
        assert result.stdout[0] == expected

        result   = fw.fslroi('input', 'output', 1, 10, 2, 20, 3, 30, 4, 40)
        expected = fslroi + ' input output 1 10 2 20 3 30 4 40'
        assert result.stdout[0] == expected


def test_slicer():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('slicer',)) as fsldir:
        slicer   = op.join(fsldir, 'bin', 'slicer')
        result   = fw.slicer('input1', 'input2', i=(20, 100), x=(20, 'x.png'))
        expected = slicer + ' input1 input2 -i 20 100 -x 20 x.png'
        assert result.stdout[0] == expected


def test_cluster():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('cluster',)) as fsldir:
        cluster  = op.join(fsldir, 'bin', 'cluster')
        result   = fw.cluster('input', 'thresh',
                              fractional=True, osize='osize')
        expected = (cluster + ' --in=input --thresh=thresh',
                    ('--fractional', '--osize=osize'))
        assert checkResult(result.stdout[0], *expected)


def test_fslmaths():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fslmaths',)) as fsldir:
        cmd    = op.join(fsldir, 'bin', 'fslmaths')
        result = fw.fslmaths('input') \
            .abs().bin().binv().recip().Tmean().Tstd().Tmin().Tmax() \
            .fillh().ero().dilM().dilF().add('addim').sub('subim') \
            .mul('mulim').div('divim').mas('masim').rem('remim')   \
            .thr('thrim').uthr('uthrim').inm('inmim').bptf(1, 10) \
            .smooth(sigma=6).kernel('3D').fmeanu().run('output')

        expected = [cmd, 'input',
                    '-abs', '-bin', '-binv', '-recip', '-Tmean', '-Tstd',
                    '-Tmin', '-Tmax', '-fillh', '-ero', '-dilM', '-dilF',
                    '-add addim', '-sub subim', '-mul mulim', '-div divim',
                    '-mas masim', '-rem remim', '-thr thrim', '-uthr uthrim',
                    '-inm inmim', '-bptf 1 10', '-s 6', '-kernel 3D', '-fmeanu',
                    'output']
        expected = ' '.join(expected)

        assert result.stdout[0] == expected

    # test LOAD output
    with tempdir() as td, mockFSLDIR(bin=('fslmaths',)) as fsldir:
        expect = make_random_image(op.join(td, 'output.nii.gz'))

        with open(op.join(fsldir, 'bin', 'fslmaths'), 'wt') as f:
            f.write(tw.dedent("""
            #!/usr/bin/env python
            import sys
            import shutil
            shutil.copy('{}', sys.argv[2])
            """.format(op.join(td, 'output.nii.gz'))).strip())
            os.chmod(op.join(fsldir, 'bin', 'fslmaths'), 0o755)

        got = fw.fslmaths('input').run()
        assert np.all(expect.dataobj[:] == got.dataobj[:])
        got = fw.fslmaths('input').run(fw.LOAD)
        assert np.all(expect.dataobj[:] == got.dataobj[:])

def test_fast():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fast',)) as fsldir:

        cmd = op.join(fsldir, 'bin', 'fast')

        result   = fw.fast('input', 'myseg', n_classes=3)
        expected = [cmd, '--out=myseg', '--class=3', 'input']

        assert result.stdout[0] == ' '.join(expected)

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3)
        expected = [cmd, '--out=myseg', '--class=3', 'in1', 'in2', 'in3']
        assert result.stdout[0] == ' '.join(expected)

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3, verbose=True)
        expected = [cmd, '--out=myseg', '--class=3', '--verbose', 'in1', 'in2', 'in3']
        assert result.stdout[0] == ' '.join(expected)


def test_fsl_anat():
    with asrt.disabled(), \
         run.dryrun(), \
         mockFSLDIR(bin=('fsl_anat',)) as fsldir:

        cmd = op.join(fsldir, 'bin', 'fsl_anat')

        result   = fw.fsl_anat('t1', out='fsl_anat', bias_smoothing=25)
        expected = [cmd, '-i', 't1', '-o', 'fsl_anat', '-t', 'T1',
                    '-s', '25']

        assert result.stdout[0] == ' '.join(expected)


def test_gps():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('gps',)) as fsldir:
        gps = op.join(fsldir, 'bin', 'gps')
        result = fw.gps('bvecs', 128, optws=True, ranseed=123)
        expected = (gps + ' --ndir=128 --out=bvecs',
                    ('--optws', '--ranseed=123'))
        assert checkResult(result.stdout[0], *expected)


def test_tbss():
    exes = {
        'preproc'  : 'tbss_1_preproc',
        'reg'      : 'tbss_2_reg',
        'postreg'  : 'tbss_3_postreg',
        'prestats' : 'tbss_4_prestats',
        'non_FA'   : 'tbss_non_FA',
        'fill'     : 'tbss_fill'
    }

    with asrt.disabled(), \
         run.dryrun(), \
         mockFSLDIR(bin=exes.values()) as fsldir:
        for k in exes:
            exes[k] = op.join(fsldir, 'bin', exes[k])

        assert fw.tbss.preproc('1', '2')[0] == ' '.join([exes['preproc'], '1', '2'])
        assert fw.tbss.reg(T=True)[0]       == ' '.join([exes['reg'], '-T'])
        assert fw.tbss.reg(n=True)[0]       == ' '.join([exes['reg'], '-n'])
        assert fw.tbss.reg(t='target')[0]   == ' '.join([exes['reg'], '-t', 'target'])
        assert fw.tbss.postreg(S=True)[0]   == ' '.join([exes['postreg'], '-S'])
        assert fw.tbss.postreg(T=True)[0]   == ' '.join([exes['postreg'], '-T'])
        assert fw.tbss.prestats(0.3)[0]     == ' '.join([exes['prestats'], '0.3'])
        assert fw.tbss.non_FA('alt')[0]     == ' '.join([exes['non_FA'], 'alt'])
        assert fw.tbss.fill('stat', 0.4, 'mean_fa', 'output', n=True).stdout[0] == \
            ' '.join([exes['fill'], 'stat', '0.4', 'mean_fa', 'output', '-n'])

def test_fsl_prepare_fieldmap():
    with asrt.disabled(), run.dryrun(), mockFSLDIR(bin=('fsl_prepare_fieldmap',)) as fsldir:
        fpf = op.join(fsldir, 'bin', 'fsl_prepare_fieldmap')
        result   = fw.fsl_prepare_fieldmap(phase_image='ph',
                                           magnitude_image='mag',
                                           out_image='out',
                                           deltaTE=2.46,
                                           nocheck=True)
        expected = (fpf, ('SIEMENS', 'ph', 'mag', 'out', '2.46', '--nocheck'))
        assert checkResult(result.stdout[0], *expected)


def test_fsl_sub():
    with run.dryrun(), mockFSLDIR(bin=('fsl_sub',)) as fsldir:
        expected = [op.join(fsldir, 'bin', 'fsl_sub'),
                    '--jobhold', '123',
                    '--queue', 'long.q',
                    'some_command', '--some_arg']

        result = fw.fsl_sub(
            'some_command', '--some_arg', jobhold='123', queue='long.q')
        assert shlex.split(result[0]) == expected
