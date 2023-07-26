#!/usr/bin/env python
#
# test_parse_data.py -
#
# Author: Michiel Cottaar <Michiel.Cottaar@ndcn.ox.ac.uk>
#

import argparse
from fsl.utils import parse_data, tempdir, path
import os.path as op
from fsl.data.vtk import VTKMesh
from fsl.data.gifti import GiftiMesh
from fsl.data.image import Image
from fsl.data.atlases import Atlas
from pytest import raises
from .test_image import make_image
import os
import pytest


datadir = op.join(op.dirname(__file__), 'testdata')


def test_mesh():
    mesh_parser = argparse.ArgumentParser("Reads a VTK file")
    mesh_parser.add_argument("mesh", type=parse_data.Mesh)

    real_filename = op.join(datadir, 'test_mesh.vtk')
    args = mesh_parser.parse_args([real_filename])
    assert isinstance(args.mesh, VTKMesh)

    real_filename = op.join(datadir, 'test_mesh')
    args = mesh_parser.parse_args([real_filename])
    assert isinstance(args.mesh, VTKMesh)

    real_filename = op.join(datadir, 'example.surf.gii')
    args = mesh_parser.parse_args([real_filename])
    assert isinstance(args.mesh, GiftiMesh)

    real_filename = op.join(datadir, 'example')
    args = mesh_parser.parse_args([real_filename])
    assert isinstance(args.mesh, GiftiMesh)

    fake_filename = op.join(datadir, 'test_mesh_fake.vtk')
    with raises(SystemExit):
        mesh_parser.parse_args([fake_filename])

    fake_filename = op.join(datadir, 'example.shape.gii')
    with raises(SystemExit):
        mesh_parser.parse_args([fake_filename])


def test_image():
    with tempdir.tempdir() as testdir:
        image_parser = argparse.ArgumentParser("Reads an image")
        image_parser.add_argument("image", type=parse_data.Image)

        for filetype in range(3):
            filename = op.join(testdir, 'image%r' % filetype)
            make_image(filename, filetype)
            args = image_parser.parse_args([filename])
            assert isinstance(args.image, Image)
            if filetype == 0:
                args = image_parser.parse_args([filename + '.hdr'])
                assert isinstance(args.image, Image)
                args = image_parser.parse_args([filename + '.img'])
                assert isinstance(args.image, Image)
                with raises(SystemExit):
                    image_parser.parse_args([filename + '.nii'])
                with raises(SystemExit):
                    image_parser.parse_args([filename + '.nii.gz'])
            else:
                args = image_parser.parse_args([filename + '.nii'])
                assert isinstance(args.image, Image)

                with raises(SystemExit):
                    image_parser.parse_args([filename + '.img'])
                with raises(SystemExit):
                    image_parser.parse_args([filename + '.hdr'])
                with raises(SystemExit):
                    image_parser.parse_args([filename + '.nii.gz'])
            args = None

        double_filename = op.join(testdir, 'image1')
        make_image(double_filename, 0)
        with raises(SystemExit):
            image_parser.parse_args([double_filename])


def test_image_out():
    image_parser = argparse.ArgumentParser("Reads an image")
    image_parser.add_argument("image_out", type=parse_data.ImageOut)
    for fsl_output_type, extension in (
            ('NIFTI', '.nii'),
            ('NIFTI_PAIR', '.img'),
            ('NIFTI_GZ', '.nii.gz')
    ):
        os.environ['FSLOUTPUTTYPE'] = fsl_output_type
        args = image_parser.parse_args(['test'])
        assert path.hasExt(args.image_out, extension)
        assert args.image_out == 'test' + extension

        args = image_parser.parse_args(['test.nii'])
        assert path.hasExt(args.image_out, '.nii')
        assert args.image_out == 'test.nii'

        args = image_parser.parse_args(['test.nii.gz'])
        assert path.hasExt(args.image_out, '.nii.gz')
        assert args.image_out == 'test.nii.gz'

        args = image_parser.parse_args(['test.img'])
        assert path.hasExt(args.image_out, '.img')
        assert args.image_out == 'test.img'

        args = image_parser.parse_args(['test.surf.gii'])
        assert path.hasExt(args.image_out, extension)
        assert args.image_out == 'test.surf.gii' + extension


@pytest.mark.fsltest
def test_atlas():
    atlas_parser = argparse.ArgumentParser('reads an atlas')
    atlas_parser.add_argument('atlas', type=parse_data.Atlas)

    args = atlas_parser.parse_args(['cerebellum_mniflirt'])
    assert isinstance(args.atlas, Atlas)

    with raises(SystemExit):
        atlas_parser.parse_args(['fake'])
