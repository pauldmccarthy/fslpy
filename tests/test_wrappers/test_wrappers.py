#!/usr/bin/env python
#
# test_wrappers.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            pathlib
import            shlex

import fsl.wrappers as fw

from . import checkResult, testenv


def test_bet():
    with testenv('bet') as bet:
        result   = fw.bet('input', 'output', mask=True, c=(10, 20, 30))
        expected = (bet + ' input output', ('-m', '-c 10 20 30'))
        assert checkResult(result.stdout[0], *expected, stripdir=[2])


def test_robustfov():
    with testenv('robustfov') as rfov:
        result   = fw.robustfov('input', 'output', b=180)
        expected = f'{rfov} -i input -b 180 -r output'
        assert result.stdout[0] == expected


def test_eddy():
    with testenv('eddy') as eddy:
        result   = fw.eddy('imain', 'mask', 'index', 'acqp',
                           'bvecs', 'bvals', 'out', dont_mask_output=True)
        expected = f'{eddy} ' \
                    '--imain=imain '\
                    '--mask=mask '\
                    '--index=index '\
                    '--acqp=acqp '\
                    '--bvecs=bvecs '\
                    '--bvals=bvals '\
                    '--out=out '\
                    '--dont_mask_output'
        assert result.stdout[0] == expected


def test_topup():
    with testenv('topup') as topup:
        result   = fw.topup('imain', 'datain', minmet=1)
        expected = topup + ' --imain=imain --datain=datain --minmet=1'
        assert result.stdout[0] == expected



def test_applytopup():
    with testenv('applytopup') as applytopup:
        result   = fw.applytopup('imain', 'datain', '1,2,3', 'topup', 'out',
                                  m='jac')
        expected = f'{applytopup} --imain=imain --datain=datain ' \
                    '--inindex=1,2,3 --topup=topup --out=out -m jac'
        assert result.stdout[0] == expected

        result   = fw.applytopup('imain', 'datain', [1, 2, 3], 'topup', 'out',
                            method='jac')
        expected = f'{applytopup} --imain=imain --datain=datain ' \
                    '--inindex=1,2,3 --topup=topup --out=out --method=jac'
        assert result.stdout[0] == expected


def test_flirt():
    with testenv('flirt') as flirt:
        result   = fw.flirt('src', 'ref', usesqform=True, anglerep='euler')
        expected = f'{flirt} -in src -ref ref -usesqform -anglerep euler'
        assert result.stdout[0] == expected


def test_fixscaleskew():
    with testenv('convert_xfm') as convert_xfm:
        result      = fw.fixscaleskew('mat1', 'mat2', 'out')
        expected    = f'{convert_xfm} -fixscaleskew mat2 mat1 -omat out'
        assert result.stdout[0] == expected


def test_epi_reg():
    with testenv('epi_reg') as epi_reg:
        result   = fw.epi_reg('epi', 't1', 't1brain', 'out')
        expected = epi_reg + ' --epi=epi --t1=t1 --t1brain=t1brain --out=out'
        assert result.stdout[0] == expected


def test_applyxfm():
    with testenv('flirt') as flirt:
        result   = fw.applyxfm('src', 'ref', 'mat', 'out', interp='trilinear')
        expected = f'{flirt} -in src -ref ref -out out -applyxfm -init mat -interp trilinear'
        assert result.stdout[0] == expected


def test_applyxfm4D():
    with testenv('applyxfm4D') as applyxfm:
        result   = fw.applyxfm4D(
            'src', 'ref', 'out', 'mat', fourdigit=True, userprefix='boo')
        expected = f'{applyxfm} src ref out mat -fourdigit -userprefix boo'
        assert result.stdout[0] == expected


def test_invxfm():
    with testenv('convert_xfm') as cnvxfm:
        result   = fw.invxfm('mat', 'output')
        expected = cnvxfm + ' -omat output -inverse mat'
        assert result.stdout[0] == expected


def test_concatxfm():
    with testenv('convert_xfm') as cnvxfm:
        result   = fw.concatxfm('mat1', 'mat2', 'output')
        expected = cnvxfm + ' -omat output -concat mat2 mat1'
        assert result.stdout[0] == expected


def test_mcflirt():
    with testenv('mcflirt') as mcflirt:
        result   = fw.mcflirt('input', out='output', cost='normcorr', dof=12)
        expected = f'{mcflirt} -in input -out output -cost normcorr -dof 12'
        assert result.stdout[0] == expected


def test_fnirt():
    with testenv('fnirt') as fnirt:
        result   = fw.fnirt('src', ref='ref', iout='iout', fout='fout',
                            subsamp=(8, 6, 4, 2))
        expected = f'{fnirt} --in=src --ref=ref --iout=iout --fout=fout --subsamp=8,6,4,2'
        assert result.stdout[0] == expected


def test_applywarp():
    with testenv('applywarp') as applywarp:
        result    = fw.applywarp('src', 'ref', 'out', warp='warp', abs=True, super=True)
        expected  = f'{applywarp} --in=src --ref=ref --out=out --warp=warp --abs --super'
        assert result.stdout[0] == expected


def test_invwarp():
    with testenv('invwarp') as invwarp:
        result   = fw.invwarp('warp', 'ref', 'out', rel=True, noconstraint=True)
        expected = f'{invwarp} --warp=warp --ref=ref --out=out --rel --noconstraint'
        assert result.stdout[0] == expected


def test_convertwarp():
    with testenv('convertwarp') as cnvwarp:
        result   = fw.convertwarp('out', 'ref', absout=True, jacobian='jacobian')
        expected = f'{cnvwarp} --ref=ref --out=out --absout --jacobian=jacobian'
        assert result.stdout[0] == expected


def test_fugue():
    with testenv('fugue') as fugue:
        result   = fw.fugue(input='input', warp='warp', median=True, dwell=10)
        expected = f'{fugue} --in=input --warp=warp --median --dwell=10'
        assert result.stdout[0] == expected



def test_sigloss():
    with testenv('sigloss') as sigloss:
        result   = fw.sigloss('input', 'sigloss', mask='mask', te=0.5)
        expected = f'{sigloss} --in input --sigloss sigloss --mask mask --te 0.5'
        assert result.stdout[0] == expected


def test_prelude():
    with testenv('prelude') as prelude:
        result   = fw.prelude(complex='complex',
                              out='out',
                              labelslices=True,
                              start=5)
        expected = f'{prelude} --complex=complex --out=out --labelslices --start=5'
        assert result.stdout[0] == expected


def test_melodic():
    with testenv('melodic') as melodic:
        result   = fw.melodic('input', dim=50, mask='mask', Oall=True)
        expected = f'{melodic} --in=input --dim=50 --mask=mask --Oall'
        assert result.stdout[0] == expected


def test_fsl_regfilt():
    with testenv('fsl_regfilt') as regfilt:
        result   = fw.fsl_regfilt('input', 'output', 'design',
                                  filter=(1, 2, 3, 4), vn=True, a=True)
        expected = f'{regfilt} --in=input --out=output --design=design ' \
                    '--filter=1,2,3,4 --vn -a'
        assert result.stdout[0] == expected


def test_fsl_glm():
    with testenv('fsl_glm') as fsl_glm:
        exp = f'{fsl_glm} --in=in --out=out --design=des -m mask --demean --dof=7'
        res = fw.fsl_glm('in', 'out', 'des', m='mask', demean=True, dof=7)
        assert res.stdout[0] == exp


def test_fslorient():
    with testenv('fslorient') as fslo:
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
    with testenv('fslreorient2std') as r2std:
        result   = fw.fslreorient2std('input', 'output')
        expected = r2std + ' input output'
        assert result.stdout[0] == expected


def test_fslroi():
    with testenv('fslroi') as fslroi:
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
    with testenv('slicer') as slicer:
        result   = fw.slicer('input1', 'input2', i=(20, 100), x=(20, 'x.png'))
        expected = slicer + ' input1 input2 -i 20 100 -x 20 x.png'
        assert result.stdout[0] == expected


def test_cluster():
    with testenv('cluster') as cluster:
        result   = fw.cluster('input', 'thresh',
                              fractional=True, osize='osize')
        expected = f'{cluster} --in=input --thresh=thresh --fractional --osize=osize'
        assert result.stdout[0] == expected


def test_fast():
    with testenv('fast') as fast:
        result   = fw.fast('input', 'myseg', n_classes=3)
        expected = f'{fast} --out=myseg --class=3 input'
        assert result.stdout[0] == expected

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3)
        expected = f'{fast} --out=myseg --class=3 in1 in2 in3'
        assert result.stdout[0] == expected

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3, verbose=True)
        expected = f'{fast} --out=myseg --class=3 --verbose in1 in2 in3'
        assert result.stdout[0] == expected

        result   = fw.fast(('in1', 'in2', 'in3'), 'myseg', n_classes=3,
                           a='reg.mat', A=('csf', 'gm', 'wm'), Prior=True)
        expected = f'{fast} --out=myseg --class=3 -a reg.mat '\
                    '-A csf gm wm --Prior in1 in2 in3'

        assert result.stdout[0] == expected


def test_fsl_anat():
    with testenv('fsl_anat') as fsl_anat:
        result   = fw.fsl_anat('t1', out='fsl_anat', bias_smoothing=25)
        expected = f'{fsl_anat} -i t1 -o fsl_anat -t T1 -s 25'
        assert result.stdout[0] == expected


def test_gps():
    with testenv('gps') as gps:
        result   = fw.gps('bvecs', 128, optws=True, ranseed=123)
        expected = f'{gps} --ndir=128 --out=bvecs --optws --ranseed=123'
        assert result.stdout[0] == expected


def test_tbss():
    exes = ['tbss_1_preproc',
            'tbss_2_reg',
            'tbss_3_postreg',
            'tbss_4_prestats',
            'tbss_non_FA',
            'tbss_fill']

    with testenv(*exes) as (preproc, reg, postreg, prestats, non_FA, fill):
        assert fw.tbss.preproc('1', '2')[0] == f'{preproc} 1 2'
        assert fw.tbss.reg(T=True)[0]       == f'{reg} -T'
        assert fw.tbss.reg(n=True)[0]       == f'{reg} -n'
        assert fw.tbss.reg(t='target')[0]   == f'{reg} -t target'
        assert fw.tbss.postreg(S=True)[0]   == f'{postreg} -S'
        assert fw.tbss.postreg(T=True)[0]   == f'{postreg} -T'
        assert fw.tbss.prestats(0.3)[0]     == f'{prestats} 0.3'
        assert fw.tbss.non_FA('alt')[0]     == f'{non_FA} alt'
        assert fw.tbss.fill('stat', 0.4, 'mean_fa', 'output', n=True).stdout[0] == \
            f'{fill} stat 0.4 mean_fa output -n'


def test_fsl_prepare_fieldmap():
    with testenv('fsl_prepare_fieldmap') as fpf:
        result   = fw.fsl_prepare_fieldmap(phase_image='ph',
                                           magnitude_image='mag',
                                           out_image='out',
                                           deltaTE=2.46,
                                           nocheck=True)
        expected = f'{fpf} SIEMENS ph mag out 2.46 --nocheck'
        assert result.stdout[0] == expected


def test_fsl_sub():
    with testenv('fsl_sub') as fsl_sub:
        expected = [fsl_sub,
                    '--jobhold', '123',
                    '--queue', 'long.q',
                    'some_command', '--some_arg']
        result = fw.fsl_sub(
            'some_command', '--some_arg', jobhold='123', queue='long.q')
        assert shlex.split(result[0]) == expected


def test_standard_space_roi():
    with testenv('standard_space_roi') as ssr:
        expected = [ssr,
                    'input',
                    'output',
                    '-maskFOV',
                    '-maskNONE',
                    '-maskMASK', 'mask',
                    '-d',
                    '-b',
                    '-ssref', 'ssref',
                    '-altinput', 'altinput',
                    '-2D',
                    '-usesqform',
                    '-ref flirt_ref']

        result = fw.standard_space_roi(
            'input', 'output',
            maskFOV=True,
            maskNONE=True,
            maskMASK='mask',
            d=True,
            b=True,
            ssref='ssref',
            altinput='altinput',
            twod=True,
            usesqform=True,
            ref='flirt_ref')
        assert result.stdout[0] == ' '.join(expected)


def test_fslswapdim():
    with testenv('fslswapdim') as swapdim:
        assert fw.fslswapdim('input', 'a', 'b', 'c').stdout[0] == \
               f'{swapdim} input a b c'
        assert fw.fslswapdim('input', 'a', 'b', 'c', 'output').stdout[0] == \
               f'{swapdim} input a b c output'


def test_first():
    exes = ['first', 'first_flirt', 'run_first',
            'run_first_all', 'first_utils', 'concat_bvars']
    with testenv(*exes) as (first, first_flirt, run_first,
                            run_first_all, first_utils, concat_bvars):

        expected = f'{first} --in=input --outputName=output ' \
                    '--inputModel=inmodel --flirtMatrix=flirtmat '\
                    '--shcond -n 5 --bmapname=bmaps'
        result = fw.first('input', 'output', 'inmodel', 'flirtmat',
                          shcond=True, n=5, bmapname='bmaps')
        assert result.stdout[0] == expected

        expected = f'{first_flirt} input outbase -b -cost costfn'
        result   = fw.first_flirt('input', 'outbase', b=True, cost='costfn')
        assert result.stdout[0] == expected

        expected = f'{run_first} -i input -t mat -n 20 ' \
                    '-o output -m L_Thal -multipleImages -intref R_Thal'
        result   = fw.run_first('input', 'mat', 20, 'output', 'L_Thal',
                                multipleImages=True, intref='R_Thal')
        assert result.stdout[0] == expected

        expected = f'{run_first} -i input -t mat -n 20 ' \
                    '-o output -m L_Thal -multipleImages -intref R_Thal'
        result   = fw.run_first('input', 'mat', 20, 'output', 'L_Thal',
                                multipleImages=True, intref='R_Thal')
        assert result.stdout[0] == expected

        expected = f'{run_first_all} -i input -o outbase -3 -s L_Hipp,R_Hipp '\
                    '-d'
        result   = fw.run_first_all('input', 'outbase', three=True,
                                    s='L_Hipp,R_Hipp', d=True)
        assert result.stdout[0] == expected

        expected = f'{first_utils} --in input --out out --useScale '\
                    '--numModes=20'
        result   = fw.first_utils('input', 'out', useScale=True,
                                  numModes=20)
        assert result.stdout[0] == expected

        expected = f'{concat_bvars} output in1 in2 in3'
        result   = fw.concat_bvars('output', 'in1', 'in2', 'in3')
        assert result[0] == expected


def test_fslmerge():
    with testenv('fslmerge') as fslmerge:

        expected = f'{fslmerge} -x out in1 in2 in3'
        result   = fw.fslmerge('x', 'out', 'in1', 'in2', 'in3')
        assert result.stdout[0] == expected

        expected = f'{fslmerge} -n 123 out in1 in2 in3'
        result   = fw.fslmerge('n', 'out', 123, 'in1', 'in2', 'in3')
        assert result.stdout[0] == expected

        expected = f'{fslmerge} -tr out in1 in2 in3 123'
        result   = fw.fslmerge('tr', 'out', 'in1', 'in2', 'in3', 123)
        assert result.stdout[0] == expected


def test_fslselectvols():
    with testenv('fslselectvols') as fsv:

        # vols can either be a sequence,
        # comma-separated string, or
        # string/path to a file
        expected = f'{fsv} -i in -o out --vols=vols.txt'
        result   = fw.fslselectvols('in', 'out', 'vols.txt')
        assert result.stdout[0] == expected

        absvols  = op.abspath('vols.txt')
        expected = f'{fsv} -i in -o out --vols={absvols}'
        result   = fw.fslselectvols('in', 'out', pathlib.Path('vols.txt'))
        assert result.stdout[0] == expected

        expected = f'{fsv} -i in -o out --vols=1,2,3'
        result   = fw.fslselectvols('in', 'out', '1,2,3')
        assert result.stdout[0] == expected

        expected = f'{fsv} -i in -o out --vols=1,2,3'
        result   = fw.fslselectvols('in', 'out', ['1', '2', '3'])
        assert result.stdout[0] == expected

        expected = f'{fsv} -i in -o out --vols=1,2,3'
        result   = fw.fslselectvols('in', 'out', [1, 2, 3])
        assert result.stdout[0] == expected


def test_fslsplit():
    with testenv('fslsplit') as fslsplit:
        assert fw.fslsplit('src')                .stdout[0] == f'{fslsplit} src'
        assert fw.fslsplit('src', 'out')         .stdout[0] == f'{fslsplit} src out'
        assert fw.fslsplit('src',        dim='x').stdout[0] == f'{fslsplit} src -x'
        assert fw.fslsplit('src', 'out', dim='t').stdout[0] == f'{fslsplit} src out -t'


def test_fslcpgeom():
    with testenv('fslcpgeom') as fslcpgeom:
        assert fw.fslcpgeom('src', 'dest')        .stdout[0] == f'{fslcpgeom} src dest'
        assert fw.fslcpgeom('src', 'dest', d=True).stdout[0] == f'{fslcpgeom} src dest -d'


def test_bianca():
    exes = ['bianca',
            'bianca_cluster_stats',
            'bianca_overlap_measures',
            'bianca_perivent_deep',
            'make_bianca_mask']
    with testenv(*exes) as (bianca,
                            bianca_cluster_stats,
                            bianca_overlap_measures,
                            bianca_perivent_deep,
                            make_bianca_mask):

        expected = f'{bianca} --singlefile sfile --querysubjectnum 3 --brainmaskfeaturenum 4'
        result   = fw.bianca('sfile', 3, 4)
        assert result[0] == expected

        expected = f'{bianca} --singlefile sfile --querysubjectnum 3 --patch3d -v'
        result   = fw.bianca('sfile', 3, patch3d=True, v=True)
        assert result[0] == expected

        expected = f'{bianca_cluster_stats} out 9 5 mask'
        result   = fw.bianca_cluster_stats('out', 9, 5, 'mask')
        assert result.stdout[0] == expected

        expected = f'{bianca_overlap_measures} lesions 9 mask 1'
        result   = fw.bianca_overlap_measures('lesions', 9, 'mask', True)
        assert result.stdout[0] == expected

        expected = f'{bianca_perivent_deep} wmh vent 10 2 out'
        result   = fw.bianca_perivent_deep('wmh', 'vent', 10, 'out', 2)
        assert result.stdout[0] == expected

        expected = f'{make_bianca_mask} struc csf warp 1'
        result   = fw.make_bianca_mask('struc', 'csf', 'warp', True)
        assert result.stdout[0] == expected


def test_feat():
    with testenv('feat') as feat:
        assert fw.feat('design.fsf')[0] == f'{feat} design.fsf'


def test_featquery():
    with testenv('featquery') as featquery:
        expect = f'{featquery} 3 feat1 feat2 feat3 2 stat1 stat2 ' \
                  'output -p -t 0.4 -w mask -vox 20 30 40'
        result = fw.featquery(('feat1', 'feat2', 'feat3'),
                              ('stat1', 'stat2'),
                              'output', 'mask',
                              vox=(20, 30, 40), t=0.4,
                              p=True, w=True)
        assert result.stdout[0] == expect

        expect = f'{featquery} 2 feat1 feat2 3 stat1 stat2 stat3 ' \
                  'output -a atlas -i 1.5 -s mask -mm 20 30 40'
        result = fw.featquery(('feat1', 'feat2'),
                              ('stat1', 'stat2', 'stat3'),
                              'output', 'mask',
                              w=False,
                              s=True,
                              a='atlas',
                              mm=(20, 30, 40),
                              i=1.5)
        assert result.stdout[0] == expect


def test_dtifit():
    with testenv('dtifit') as dtifit:
        res    = fw.dtifit('data', 'out', 'mask', 'bvecs', 'bvals', kurt=True, z=2, xmax=6)
        exp    = f'{dtifit} --data=data --out=out --mask=mask --bvecs=bvecs '\
                  '--bvals=bvals --kurt -z 2 --xmax=6'
        assert res.stdout[0] == exp


def test_xfibres():
    with testenv('xfibres') as xfibres:
        res = fw.xfibres('data', 'mask', 'bvecs', 'bvals',
                         f0=True, nf=20, V=True)
        exp = f'{xfibres} --data=data --mask=mask --bvecs=bvecs ' \
               '--bvals=bvals --f0 --nf=20 -V'
        assert res.stdout[0] == exp


def test_xfibres_gpu():
    with testenv('xfibres_gpu') as xfibres_gpu:
        res = fw.xfibres_gpu('data', 'mask', 'bvecs', 'bvals', 'subjdir',
                             1, 10, 100, f0=True, nf=20)
        exp = f'{xfibres_gpu} --data=data --mask=mask --bvecs=bvecs ' \
               '--bvals=bvals --f0 --nf=20 subjdir 1 10 100'
        assert res.stdout[0] == exp


def test_split_parts_gpu():
    with testenv('split_parts_gpu') as split_parts_gpu:
        res = fw.split_parts_gpu('data', 'mask', 'bvals', 'bvecs', 10, 'out')
        exp = f'{split_parts_gpu} data mask bvals bvecs None 0 10 out'
        assert res.stdout[0] == exp
        res = fw.split_parts_gpu('data', 'mask', 'bvals', 'bvecs', 10, 'out', 'grad')
        exp = f'{split_parts_gpu} data mask bvals bvecs grad 1 10 out'
        assert res.stdout[0] == exp


def test_bedpostx_postproc_gpu():
    with testenv('bedpostx_postproc_gpu.sh') as bpg:
        res = fw.bedpostx_postproc_gpu('data', 'mask', 'bvecs', 'bvals',
                                       100, 10, 'subdir', 'bindir', nf=20)
        exp = f'{bpg} --data=data --mask=mask --bvecs=bvecs --bvals=bvals ' \
               '--nf=20 100 10 subdir bindir'
        assert res.stdout[0] == exp


def test_probtrackx():
    with testenv('probtrackx') as ptx:
        res = fw.probtrackx('samples', 'mask', 'seed', rseed=20,
                            usef=True, S=50, nsamples=50)
        exp = f'{ptx} --samples=samples --mask=mask --seed=seed --rseed=20 ' \
               '--usef -S 50 --nsamples=50'
        assert res.stdout[0] == exp


def test_probtrackx2():
    with testenv('probtrackx2') as ptx2:
        res = fw.probtrackx2('samples', 'mask', 'seed', rseed=20,
                             usef=True, S=50, nsamples=50)
        exp = f'{ptx2} --samples=samples --mask=mask --seed=seed --rseed=20 ' \
               '--usef -S 50 --nsamples=50'
        assert res.stdout[0] == exp


def test_probtrackx2_gpu():
    with testenv('probtrackx2_gpu') as ptx2gpu:
        res = fw.probtrackx2_gpu('samples', 'mask', 'seed', rseed=20,
                                 usef=True, S=50, nsamples=50)
        exp = f'{ptx2gpu} --samples=samples --mask=mask --seed=seed ' \
               '--rseed=20 --usef -S 50 --nsamples=50'
        assert res.stdout[0] == exp


def test_oxford_asl():
    with testenv('oxford_asl') as oxford_asl:
        res = fw.oxford_asl('in', 'out',
                            S='T1',
                            sbrain='T1_brain',
                            regfrom_method='pwi',
                            region_analysis=True,
                            region_analysis_atlas=['a1', 'a2', 'a3'],
                            region_analysis_atlas_labels=['l1', 'l2', 'l3'])
        exp = f'{oxford_asl} -i in -o out -S T1 --sbrain=T1_brain ' \
               '--regfrom-method=pwi --region-analysis '  \
               '--region-analysis-atlas=a1 ' \
               '--region-analysis-atlas=a2 ' \
               '--region-analysis-atlas=a3 ' \
               '--region-analysis-atlas-labels=l1 ' \
               '--region-analysis-atlas-labels=l2 ' \
               '--region-analysis-atlas-labels=l3'
        assert res.stdout[0] == exp


def test_asl_file():
    with testenv('asl_file') as asl_file:
        res = fw.asl_file('in', 20, 'out', diff=True, iaf='ct')
        exp = f'{asl_file} --data=in --ntis=20 --out=out --diff --iaf=ct'
        assert res.stdout[0] == exp


def test_randomise():
    with testenv('randomise') as randomise:
        res = fw.randomise('input', 'outbase', T=True, T2=True, fonly=True,
                           d='design.mat', one=True)
        exp = f'{randomise} -i input -o outbase -T --T2 --fonly -d design.mat -1'
        assert res[0] == exp
