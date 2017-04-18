#!/usr/bin/env python
#
# test_fixlabels.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

import os.path as op
import            textwrap

import pytest

import tests
import fsl.data.fixlabels as fixlabels

goodfiles = []

goodfiles.append(("""
filtered_func_data.ica
1, Signal, False
2, Unclassified Noise, True
3, Unknown, False
4, Signal, False
5, Unclassified Noise, True
6, Unclassified Noise, True
7, Unclassified Noise, True
8, Signal, False
[2, 5, 6, 7]
""",
'filtered_func_data.ica',
[['Signal'],
 ['Unclassified Noise'],
 ['Unknown'],
 ['Signal'],
 ['Unclassified Noise'],
 ['Unclassified Noise'],
 ['Unclassified Noise'],
 ['Signal']]))


goodfiles.append(("""
REST.ica/filtered_func_data.ica
1, Signal, Unclassified noise, Cardiac, White matter, False
2, Non-brain, Movement, MRI, True
3, Unclassified noise, True
4, Non-brain, True
5, Unclassified noise, True
6, Non-brain, True
7, Respiratory, True
8, White matter, True
9, Movement, True
10, White matter, True
11, White matter, True
12, Movement, True
13, Unclassified noise, True
14, Unclassified noise, True
15, Signal, False
16, Signal, False
17, Signal, False
18, Signal, False
19, Signal, False
20, Signal, False
21, Unclassified noise, True
22, Unclassified noise, True
23, Unclassified noise, True
24, Unclassified noise, True
25, Unknown, False
[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 21, 22, 23, 24]
""",
'REST.ica/filtered_func_data.ica',
[['Signal', 'Unclassified noise', 'Cardiac', 'White matter'],
 ['Non-brain', 'Movement', 'MRI'],
 ['Unclassified noise'],
 ['Non-brain'],
 ['Unclassified noise'],
 ['Non-brain'],
 ['Respiratory'],
 ['White matter'],
 ['Movement'],
 ['White matter'],
 ['White matter'],
 ['Movement'],
 ['Unclassified noise'],
 ['Unclassified noise'],
 ['Signal'],
 ['Signal'],
 ['Signal'],
 ['Signal'],
 ['Signal'],
 ['Signal'],
 ['Unclassified noise'],
 ['Unclassified noise'],
 ['Unclassified noise'],
 ['Unclassified noise'],
 ['Unknown']]))

goodfiles.append(("""
[2, 5, 6, 7]
""",
None,
[['Signal'],
 ['Unclassified noise'],
 ['Signal'],
 ['Signal'],
 ['Unclassified noise'],
 ['Unclassified noise'],
 ['Unclassified noise']]))

goodfiles.append(("""
2, 5, 6, 7
""",
None,
[['Unknown'],
 ['Movement'],
 ['Unknown'],
 ['Unknown'],
 ['Movement'],
 ['Movement'],
 ['Movement']]))


goodfiles.append(("""
path/to/analysis.ica
1, Unclassified noise, True
2, Signal, Blob
[1]
""",
'path/to/analysis.ica',
[['Unclassified noise'],
 ['Signal', 'Blob']]))

def test_loadLabelFile_good():

    for filecontents, expMelDir, expLabels in goodfiles:

        with tests.testdir() as testdir:

            if expMelDir is not None:
                expMelDir = op.join(testdir, expMelDir)

            fname = op.join(testdir, 'labels.txt')
            with open(fname, 'wt') as f:
                f.write(filecontents.strip())

            resMelDir, resLabels = fixlabels.loadLabelFile(fname)

            assert resMelDir == expMelDir
            
            assert len(resLabels) == len(expLabels)
            for exp, res in zip(expLabels, resLabels):
                assert exp == res




# No contents
badfiles = []
badfiles.append('')

# Badly formed component line
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2 Signal, False
[1]
""")

# Badly formed component line (again)
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
Signal, False
[1]
""")

# Badly formed component line (again)
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
Signal, Movement, False
[1]
""")


# Badly formed component line (again)
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Signal
[1]
""")

# Missing path
badfiles.append("""
1, Signal, False
2, Unclassified noise, True
[2]
""")

# Duplicate component line
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
1, Unclassified noise, True
[1]
""")

# Missing component line
badfiles.append("""
path/to/analysis.ica
2, Unclassified noise, True
3, Signal, False
[2]
""")


# Missing component line (again)
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Unclassified noise, True
5, Signal, False
[1, 2]
""")


# Missing noisy list
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Unclassified noise, True
3, Signal, False
""")

# Invalid noisy list
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Unclassified noise, True
3, Signal, False
[1, 3]
""")

# Invalid noisy list
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Unclassified noise, True
3, Signal, False
[4, 6]
""")

# Invalid noisy list
badfiles.append("""
path/to/analysis.ica
1, Unclassified noise, True
2, Unclassified noise, True
3, Signal, False
[1, 3]
""")


def test_loadLabelFile_bad():

    with pytest.raises(Exception):
        fixlabels.loadLabelFile('notafile')

    for bf in badfiles:
        with tests.testdir() as testdir:
            fname = op.join(testdir, 'labels.txt')
            with open(fname, 'wt') as f:
                f.write(bf.strip())

            with pytest.raises(Exception):
                fixlabels.loadLabelFile(fname)


def test_loadLabelFile_customLabels():

    included = [2, 3, 4, 5]
    contents = '[{}]\n'.format([i + 1 for i in included])

    defIncLabel = 'Unclassified noise'
    defExcLabel = 'Signal'

    with tests.testdir() as testdir:
        fname = op.join(testdir, 'labels.txt')

        with open(fname, 'wt') as f:
            f.write(contents)

        # Check default labels
        _, labels = fixlabels.loadLabelFile(fname)
        for i, ilbls in enumerate(labels):
            assert len(ilbls) == 1
            if i in included:
                assert ilbls[0] == defIncLabel
            else:
                assert ilbls[0] == defExcLabel

        # Check custom labels
        incLabel  = 'Included'
        excLabel  = 'Excluded label'
        _, labels = fixlabels.loadLabelFile(fname,
                                            includeLabel=incLabel,
                                            excludeLabel=excLabel)
        for i, ilbls in enumerate(labels):
            assert len(ilbls) == 1
            if i in included:
                assert ilbls[0] == incLabel
            else:
                assert ilbls[0] == excLabel 


def test_saveLabelFile():


    labels = [['Label1', 'Label2', 'Label3'],
              ['Signal'],
              ['Noise'],
              ['Label1'],
              ['Unknown']]

    expected = textwrap.dedent("""
    1, Label1, Label2, Label3, True
    2, Signal, False
    3, Noise, True
    4, Label1, True
    5, Unknown, False
    """).strip()
    
    with tests.testdir() as testdir:
        fname = op.join(testdir, 'fname.txt')

        # dirname=None, listBad=False
        exp = '.\n{}'.format(expected)
        fixlabels.saveLabelFile(labels, fname, listBad=False)
        with open(fname, 'rt') as f:
            assert f.read().strip() == exp

        # dirname=something, listBad=False
        dirname = 'Blob/a.ica'
        fixlabels.saveLabelFile(labels, fname, dirname=dirname, listBad=False)
        exp = '{}\n{}'.format(dirname, expected)
        with open(fname, 'rt') as f:
            assert f.read().strip() == exp
            
        # dirname=None, listBad=True
        fixlabels.saveLabelFile(labels, fname)
        exp = '.\n{}\n[1, 3, 4]'.format(expected)
        with open(fname, 'rt') as f: 
            assert f.read().strip() == exp 

        # Custom signal labels
        sigLabels = ['Label1']
        exp = textwrap.dedent("""
        .
        1, Label1, Label2, Label3, False
        2, Signal, True
        3, Noise, True
        4, Label1, False
        5, Unknown, True
        [2, 3, 5]
        """).strip()

        fixlabels.saveLabelFile(labels, fname, signalLabels=sigLabels)
        with open(fname, 'rt') as f: 
            assert f.read().strip() == exp 
