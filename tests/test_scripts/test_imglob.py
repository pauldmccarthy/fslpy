#!/usr/bin/env python

import mock

import fsl.scripts.imglob as imglob

from .. import testdir
from .. import CaptureStdout


def test_imglob_script_shouldPass():

    # (files to create, args, expected)
    tests = [
        ('file.hdr file.img', 'file',                          'file'),
        ('file.hdr file.img', '-extension file',               'file.hdr'),
        ('file.hdr file.img', '-extensions file',              'file.hdr file.img'),
        ('file.hdr file.img', 'file.hdr',                      'file'),
        ('file.hdr file.img', ' -extension file.hdr',           'file.hdr'),
        ('file.hdr file.img', '-extensions file.hdr',          'file.hdr file.img'),
        ('file.hdr file.img', 'file.img',                      'file'),
        ('file.hdr file.img', '-extension file.img',           'file.hdr'),
        ('file.hdr file.img', '-extensions file.img',          'file.hdr file.img'),
        ('file.hdr file.img', 'file.hdr file.img',             'file'),
        ('file.hdr file.img', '-extension file.hdr file.img',  'file.hdr'),
        ('file.hdr file.img', '-extensions file.hdr file.img', 'file.hdr file.img'),
        ('file.hdr file.img', 'file file.img',                 'file'),
        ('file.hdr file.img', '-extension file file.img',      'file.hdr'),
        ('file.hdr file.img', '-extensions file file.img',     'file.hdr file.img'),

        # no file or incomplete prefix
        ('file.hdr file.img', 'bag',             ''),
        ('file.hdr file.img', '-extension  bag', ''),
        ('file.hdr file.img', '-extensions bag', ''),
        ('file.hdr file.img', 'fi',              ''),
        ('file.hdr file.img', '-extension  fi',  ''),
        ('file.hdr file.img', '-extensions fi',  ''),
    ]

    capture = CaptureStdout()

    for to_create, args, expected in tests:
        with testdir(to_create.split()) as td:

            capture.reset()

            with capture:
                assert imglob.main(args.split()) == 0

            assert capture.stdout.strip().split() == expected.split()


def test_imglob_script_shouldFail():

    capture = CaptureStdout()

    with capture:
        assert imglob.main([]) != 0

    assert capture.stdout.strip().lower().startswith('usage:')

    with capture, mock.patch('sys.argv', ['imglob']):
        assert imglob.main() != 0

    assert capture.stdout.strip().lower().startswith('usage:')
