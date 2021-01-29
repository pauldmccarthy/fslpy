#!/usr/bin/env python
#
# These tests require an internet connection, and will only work on linux.
#

import os.path        as op
import                   os
import functools      as ft
import subprocess     as sp
import                   tarfile
import                   zipfile
import                   random
import                   string
import                   binascii
import                   contextlib
import urllib.request as request
from   unittest import   mock

import pytest

import fsl.data.dicom    as fsldcm
import fsl.utils.tempdir as tempdir


datadir = op.join(op.dirname(__file__), 'testdata')


pytestmark = pytest.mark.dicomtest


@contextlib.contextmanager
def install_dcm2niix(version='1.0.20201102'):
    filenames = {
        '1.0.20201102' : 'v1.0.20201102/dcm2niix_lnx.zip',
        '1.0.20190902' : 'v1.0.20190902/dcm2niix_lnx.zip',
        '1.0.20181125' : 'v1.0.20181125/dcm2niix_25-Nov-2018_lnx.zip',
        '1.0.20171017' : 'v1.0.20171017/dcm2niix_18-Oct-2017_lnx.zip',
    }
    prefix = 'https://github.com/rordenlab/dcm2niix/releases/download/'
    url    = prefix + filenames[version]

    with tempdir.tempdir() as td:
        request.urlretrieve(url, 'dcm2niix.zip')

        with zipfile.ZipFile('dcm2niix.zip', 'r') as f:
            f.extractall('.')

        os.chmod(op.join(td, 'dcm2niix'), 0o755)

        path = op.pathsep.join((op.abspath('.'), os.environ['PATH']))

        with mock.patch.dict('os.environ', {'PATH' : path}):
            try:
                yield
            finally:
                fsldcm.installedVersion.invalidate()


def test_disabled():
    with mock.patch('fsl.data.dicom.enabled', return_value=False):
        with pytest.raises(RuntimeError):
            fsldcm.scanDir('.')
        with pytest.raises(RuntimeError):
            fsldcm.loadSeries({})



def test_installedVersion():
    tests = [
        ('1.0.20190902', (1, 0, 2019, 9, 2)),
        ('1.0.20181125', (1, 0, 2018, 11, 25)),
        ('1.0.20171017', (1, 0, 2017, 10, 17))]

    for version, expect in tests:
        fsldcm.installedVersion.invalidate()
        with install_dcm2niix(version):
            got = fsldcm.installedVersion()
            assert got == expect



def test_enabled():

    try:
        with install_dcm2niix('1.0.20190902'):
            fsldcm.installedVersion.invalidate()
            assert fsldcm.enabled()

        # test dcm2niix not present
        with mock.patch('subprocess.check_output',
                        side_effect=Exception()):
            fsldcm.installedVersion.invalidate()
            assert not fsldcm.enabled()

        # test presence of different versions
        tests = [(b'version v2.1.20191212', True),
                 (b'version v1.0.20190902', True),
                 (b'version v1.0.20171216', True),
                 (b'version v1.0.20171215', True),
                 (b'version v1.0.20171214', False),
                 (b'version v1.0.20160930', False),
                 (b'version v1.0.20160929', False),
                 (b'version v0.0.00000000', False),
                 (b'version blurgh',        False)]

        for verstr, expected in tests:
            fsldcm.installedVersion.invalidate()
            with mock.patch('subprocess.check_output', return_value=verstr):
                assert fsldcm.enabled() == expected

    finally:
        fsldcm.installedVersion.invalidate()


def test_scanDir():

    with install_dcm2niix():

        series = fsldcm.scanDir('.')
        assert len(series) == 0

        datafile = op.join(datadir, 'example_dicom.tbz2')

        with tarfile.open(datafile) as f:
            f.extractall()

        series = fsldcm.scanDir('.')
        assert len(series) == 2

        for s in series:
            assert s['PatientName'] in ('MCCARTHY_PAUL',
                                        'MCCARTHY^PAUL',
                                        'MCCARTHY_PAUL_2',
                                        'MCCARTHY^PAUL^2')


def test_sersiesCRC():
    RANDOM = object()
    tests = [
        ({'SeriesInstanceUID' : 'hello-world'},            '2983461467'),
        ({'SeriesInstanceUID' : RANDOM, 'EchoNumber' : 0}, RANDOM),
        ({'SeriesInstanceUID' : RANDOM, 'EchoNumber' : 1}, RANDOM),
        ({'SeriesInstanceUID' : RANDOM, 'EchoNumber' : 2}, RANDOM),
        ({'SeriesInstanceUID' : RANDOM, 'EchoNumber' : 3}, RANDOM),
    ]

    for series, expect in tests:
        series = dict(series)
        if expect is RANDOM:
            expect = ''.join([random.choice(string.ascii_letters + string.digits)
                              for i in range(30)])
            series['SeriesInstanceUID'] = expect
            expect = str(binascii.crc32(expect.encode()))
        echo = series.get('EchoNumber', 0)
        if echo > 1:
            expect += '.{}'.format(echo)
        assert fsldcm.seriesCRC(series) == expect


def test_loadSeries():

    # test a pre-CRC and a post-CRC version
    for version in ('1.0.20181125', '1.0.20201102'):

        with install_dcm2niix(version):

            datafile = op.join(datadir, 'example_dicom.tbz2')

            with tarfile.open(datafile) as f:
                f.extractall()

            dcmdir   = os.getcwd()
            series   = fsldcm.scanDir(dcmdir)
            expShape = (512, 512, 1)

            for s in series:

                imgs = fsldcm.loadSeries(s)

                for img in imgs:

                    assert img.dicomDir               == dcmdir
                    assert img.shape                  == expShape
                    assert img[:].shape               == expShape
                    assert img.getMeta('PatientName') in ('MCCARTHY_PAUL',
                                                          'MCCARTHY^PAUL',
                                                          'MCCARTHY_PAUL_2',
                                                          'MCCARTHY^PAUL^2')
                    assert 'PatientName'                      in img.metaKeys()
                    assert 'MCCARTHY_PAUL'                    in img.metaValues() or \
                           'MCCARTHY^PAUL'                    in img.metaValues() or \
                           'MCCARTHY_PAUL_2'                  in img.metaValues() or \
                           'MCCARTHY^PAUL^2'                  in img.metaValues()
                    assert ('PatientName', 'MCCARTHY_PAUL')   in img.metaItems() or \
                           ('PatientName', 'MCCARTHY^PAUL')   in img.metaItems() or \
                           ('PatientName', 'MCCARTHY_PAUL_2') in img.metaItems() or \
                           ('PatientName', 'MCCARTHY^PAUL^2') in img.metaItems()
