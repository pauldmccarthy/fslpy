from fsl.data import cifti
import os.path as op
import numpy as np
import nibabel as nib
from numpy import testing
import tests
from nibabel.cifti2 import cifti2_axes


def volumetric_brain_model():
    mask = np.random.randint(2, size=(10, 10, 10)) > 0
    return cifti2_axes.BrainModelAxis.from_mask(mask, affine=np.eye(4))


def surface_brain_model():
    mask = np.random.randint(2, size=100) > 0
    return cifti2_axes.BrainModelAxis.from_mask(mask, name='cortex')


def volumetric_parcels(return_mask=False):
    mask = np.random.randint(5, size=(10, 10, 10))
    axis = cifti2_axes.ParcelsAxis(
        [f'vol_{idx}' for idx in range(1, 5)],
        voxels=[np.stack(np.where(mask == idx), axis=-1) for idx in range(1, 5)],
        vertices=[{} for _ in range(1, 5)],
        volume_shape=mask.shape,
        affine=np.eye(4),
    )
    if return_mask:
        return axis, mask
    else:
        return axis


def surface_parcels(return_mask=False):
    mask = np.random.randint(5, size=100)
    axis = cifti2_axes.ParcelsAxis(
        [f'surf_{idx}' for idx in range(1, 5)],
        voxels=[np.zeros((0, 3), dtype=int) for _ in range(1, 5)],
        vertices=[{'CIFTI_STRUCTURE_CORTEX': np.where(mask == idx)[0]} for idx in range(1, 5)],
        nvertices={'CIFTI_STRUCTURE_CORTEX': 100},
    )
    if return_mask:
        return axis, mask
    else:
        return axis


def gen_data(axes):
    return np.random.randn(*(5 if ax is None else len(ax) for ax in axes))


def test_read_gifti():
    testdir = op.join(op.dirname(__file__), 'testdata')

    shapefile = op.join(testdir, 'example.shape.gii')
    ref_data = nib.load(shapefile).darrays[0].data

    data = cifti.load(shapefile)
    assert isinstance(data, cifti.DenseCifti)
    assert data.arr.shape == (642, )
    testing.assert_equal(data.arr, ref_data)
    testing.assert_equal(data.brain_model_axis.vertex, np.arange(642))
    assert len(data.brain_model_axis.nvertices) == 1
    assert data.brain_model_axis.nvertices['CIFTI_STRUCTURE_OTHER'] == 642

    data = cifti.load(shapefile, mask_values=(ref_data[0], ))
    assert isinstance(data, cifti.DenseCifti)
    assert data.arr.shape == (np.sum(ref_data != ref_data[0]), )
    testing.assert_equal(data.arr, ref_data[ref_data != ref_data[0]])
    testing.assert_equal(data.brain_model_axis.vertex, np.where(ref_data != ref_data[0])[0])
    assert len(data.brain_model_axis.nvertices) == 1
    assert data.brain_model_axis.nvertices['CIFTI_STRUCTURE_OTHER'] == 642

    cifti.load(op.join(testdir, 'example'))


def test_read_nifti():
    mask = np.random.randint(2, size=(10, 10, 10)) > 0
    values = np.random.randn(10, 10, 10)
    for mask_val in (0, np.nan):
        values[~mask] = mask_val
        affine = np.concatenate((np.random.randn(3, 4), np.array([0, 0, 0, 1])[None, :]), axis=0)
        with tests.testdir():
            nib.Nifti1Image(values, affine).to_filename("masked_image.nii.gz")
            data = cifti.load("masked_image")
            assert isinstance(data, cifti.DenseCifti)
            testing.assert_equal(data.arr, values[mask])
            testing.assert_allclose(data.brain_model_axis.affine, affine)
            assert len(data.brain_model_axis.nvertices) == 0


def check_io(data: cifti.Cifti, extension):
    with tests.testdir():
        data.save("test")
        assert op.isfile(f'test.{extension}.nii')
        loaded = cifti.load("test")
        if data.arr.ndim == 1:
            testing.assert_equal(data.arr, loaded.arr[0])
            assert data.axes == loaded.axes[1:]
        else:
            testing.assert_equal(data.arr, loaded.arr)
            assert data.axes == loaded.axes


def test_io_cifti():
    for cifti_class, cifti_type, main_axis_options in (
        (cifti.DenseCifti, 'd', (volumetric_brain_model(), surface_brain_model(),
                                 volumetric_brain_model() + surface_brain_model())),
        (cifti.ParcelCifti, 'p', (volumetric_parcels(), surface_parcels(),
                                  volumetric_parcels() + surface_parcels())),
    ):
        for main_axis in main_axis_options:
            with tests.testdir():
                data_1d = cifti_class(gen_data([main_axis]), [main_axis])
                check_io(data_1d, f'{cifti_type}scalar')

                connectome = cifti_class(gen_data([main_axis, main_axis]), (main_axis, main_axis))
                check_io(connectome, f'{cifti_type}conn')

                scalar_axis = cifti2_axes.ScalarAxis(['A', 'B', 'C'])
                scalar = cifti_class(gen_data([scalar_axis, main_axis]), (scalar_axis, main_axis))
                check_io(scalar, f'{cifti_type}scalar')

                label_axis = cifti2_axes.LabelAxis(['A', 'B', 'C'], {1: ('some parcel', (1, 0, 0, 1))})
                label = cifti_class(gen_data([label_axis, main_axis]), (label_axis, main_axis))
                check_io(label, f'{cifti_type}label')

                series_axis = cifti2_axes.SeriesAxis(10, 3, 50, unit='HERTZ')
                series = cifti_class(gen_data([series_axis, main_axis]), (series_axis, main_axis))
                check_io(series, f'{cifti_type}tseries')

                if cifti_type == 'd':
                    parcel_axis = surface_parcels()
                    dpconn = cifti_class(gen_data([parcel_axis, main_axis]), (parcel_axis, main_axis))
                    check_io(dpconn, 'dpconn')
                else:
                    dense_axis = surface_brain_model()
                    pdconn = cifti_class(gen_data([dense_axis, main_axis]), (dense_axis, main_axis))
                    check_io(pdconn, 'pdconn')


def test_extract_dense():
    vol_bm = volumetric_brain_model()
    surf_bm = surface_brain_model()
    for bm in (vol_bm + surf_bm, surf_bm + vol_bm):
        for ndim, no_other_axis in ((1, True), (2, False), (2, True)):
            if ndim == 1:
                data = cifti.DenseCifti(gen_data([bm]), [bm])
            else:
                scl = cifti2_axes.ScalarAxis(['A', 'B', 'C'])
                data = cifti.DenseCifti(gen_data([scl, bm]),
                                        [None if no_other_axis else scl, bm])

            # extract volume
            ref_arr = data.arr[..., data.brain_model_axis.volume_mask]
            vol_image = data.to_image(fill=np.nan)
            if ndim == 1:
                assert vol_image.shape == data.brain_model_axis.volume_shape
            else:
                assert vol_image.shape == data.brain_model_axis.volume_shape + (3, )
            assert np.isfinite(vol_image.data).sum() == len(vol_bm) * (3 if ndim == 2 else 1)
            testing.assert_equal(vol_image.data[tuple(vol_bm.voxel.T)], ref_arr.T)

            from_image = cifti.DenseCifti.from_image(vol_image)
            assert from_image.brain_model_axis == vol_bm
            testing.assert_equal(from_image.arr, ref_arr)

            # extract surface
            ref_arr = data.arr[..., data.brain_model_axis.surface_mask]
            mask, surf_data = data.surface('cortex', partial=True)
            assert surf_data.shape[-1] < 100
            testing.assert_equal(ref_arr, surf_data)
            testing.assert_equal(surf_bm.vertex, mask)

            surf_data_full = data.surface('cortex', fill=np.nan)
            assert surf_data_full.shape[-1] == 100
            mask_full = np.isfinite(surf_data_full)
            if ndim == 2:
                assert (mask_full.any(0) == mask_full.all(0)).all()
                mask_full = mask_full[0]
            assert mask_full.sum() == len(surf_bm)
            assert mask_full[..., mask].sum() == len(surf_bm)
            testing.assert_equal(surf_data_full[..., mask_full], ref_arr)


def test_extract_parcel():
    vol_parcel, vol_mask = volumetric_parcels(return_mask=True)
    surf_parcel, surf_mask = surface_parcels(return_mask=True)
    parcel = vol_parcel + surf_parcel
    for ndim, no_other_axis in ((1, True), (2, False), (2, True)):
        if ndim == 1:
            data = cifti.ParcelCifti(gen_data([parcel]), [parcel])
        else:
            scl = cifti2_axes.ScalarAxis(['A', 'B', 'C'])
            data = cifti.ParcelCifti(gen_data([scl, parcel]),
                                     [None if no_other_axis else scl, parcel])

        # extract volume
        vol_image = data.to_image(fill=np.nan)
        if ndim == 1:
            assert vol_image.shape == data.parcel_axis.volume_shape
        else:
            assert vol_image.shape == data.parcel_axis.volume_shape + (3, )
        assert np.isfinite(vol_image.data).sum() == np.sum(vol_mask != 0) * (3 if ndim == 2 else 1)
        if ndim == 1:
            testing.assert_equal(vol_mask != 0, np.isfinite(vol_image.data))
            for idx in range(1, 5):
                testing.assert_allclose(vol_image.data[vol_mask == idx], data.arr[..., idx - 1])
        else:
            for idx in range(3):
                testing.assert_equal(vol_mask != 0, np.isfinite(vol_image.data[..., idx]))
                for idx2 in range(1, 5):
                    testing.assert_allclose(vol_image.data[vol_mask == idx2, idx], data.arr[idx, idx2 - 1])

        # extract surface
        mask, surf_data = data.surface('cortex', partial=True)
        assert surf_data.shape[-1] == (surf_mask != 0).sum()
        assert (surf_mask[mask] != 0).all()
        print(data.arr)
        for idx in range(1, 5):
            if ndim == 1:
                testing.assert_equal(surf_data.T[surf_mask[mask] == idx], data.arr[idx + 3])
            else:
                for idx2 in range(3):
                    testing.assert_equal(surf_data.T[surf_mask[mask] == idx, idx2], data.arr[idx2, idx + 3])

        surf_data_full = data.surface('cortex', partial=False)
        assert surf_data_full.shape[-1] == 100
        if ndim == 1:
            testing.assert_equal(np.isfinite(surf_data_full), surf_mask != 0)
            for idx in range(1, 5):
                testing.assert_equal(surf_data_full.T[surf_mask == idx], data.arr[idx + 3])
        else:
            for idx2 in range(3):
                testing.assert_equal(np.isfinite(surf_data_full)[idx2], (surf_mask != 0))
                for idx in range(1, 5):
                    testing.assert_equal(surf_data_full.T[surf_mask == idx, idx2], data.arr[idx2, idx + 3])


def test_brainstructure():
    for primary in ['cortex', 'cerebellum']:
        for secondary in [None, 'white', 'pial']:
            for gtype in [None, 'volume', 'surface']:
                for orientation in ['left', 'right', 'both']:
                    bst = cifti.BrainStructure(primary, secondary, orientation, gtype)
                    print(bst.cifti)
                    assert bst.cifti == 'CIFTI_STRUCTURE_%s%s' % (primary.upper(), '' if orientation == 'both' else '_' + orientation.upper())
                    assert bst.gifti['AnatomicalStructurePrimary'][:len(primary)] == primary.capitalize()
                    assert len(bst.gifti) == (1 if secondary is None else 2)
                    if secondary is not None:
                        assert bst.gifti['AnatomicalStructureSecondary'] == secondary.capitalize()
                    assert bst == cifti.BrainStructure(primary, secondary, orientation, gtype)
                    assert bst == bst
                    assert bst != cifti.BrainStructure('Thalamus', secondary, orientation, gtype)
                    if secondary is None:
                        assert bst == cifti.BrainStructure(primary, 'midplane', orientation, gtype)
                    else:
                        assert bst != cifti.BrainStructure(primary, 'midplane', orientation, gtype)
                    if (gtype == 'volume' and primary == 'cortex') or (gtype == 'surface' and primary != 'cortex'):
                        assert cifti.BrainStructure.from_string(bst.cifti) != bst
                    else:
                        assert cifti.BrainStructure.from_string(bst.cifti) == bst
                    assert cifti.BrainStructure.from_string(bst.cifti).secondary is None
