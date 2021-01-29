"""
Provides a sparse representation of volumetric and/or surface data

The data can be either defined per voxel/vertex (:class:`DenseCifti`) or per parcel (`class:`ParcelCifti`).

The data can be read from NIFTI, GIFTI, or CIFTI files.
Non-sparse volumetric or surface representations can be extracte.
"""
from nibabel.cifti2 import cifti2_axes
from typing import Sequence, Optional, Union
import numpy as np
from fsl.data import image
import nibabel as nib
from fsl.utils.path import addExt


dense_extensions = {
    cifti2_axes.BrainModelAxis: '.dconn.nii',
    cifti2_axes.ParcelsAxis: '.dpconn.nii',
    cifti2_axes.SeriesAxis: '.dtseries.nii',
    cifti2_axes.ScalarAxis: '.dscalar.nii',
    cifti2_axes.LabelAxis: '.dlabel.nii',
}

parcel_extensions = {
    cifti2_axes.BrainModelAxis: '.pdconn.nii',
    cifti2_axes.ParcelsAxis: '.pconn.nii',
    cifti2_axes.SeriesAxis: '.ptseries.nii',
    cifti2_axes.ScalarAxis: '.pscalar.nii',
    cifti2_axes.LabelAxis: '.plabel.nii',
}


class Cifti:
    """
    Parent class for the two types of CIFTI files.

    The type of the CIFTI file is determined by the last axis, which can be one of:

    - :py:class:`BrainModelAxis <cifti2_axes.BrainModelAxis>`
    - :py:class:`ParcelsAxis <cifti2_axes.ParcelsAxis>`
    """
    def __init__(self, arr: np.ndarray, axes: Sequence[Optional[cifti2_axes.Axis]]):
        """
        Defines a new dataset in greyordinate space

        :param data: (..., N) array for N greyordinates or parcels; can contain Nones for undefined axes
        :param axes: sequence of CIFTI axes describing the data along each dimension
        """
        self.arr = arr
        axes = tuple(axes)
        while self.arr.ndim > len(axes):
            axes = (None, ) + axes
        self.axes = axes
        if not all(ax is None or len(ax) == sz for ax, sz in zip(axes, self.arr.shape)):
            raise ValueError(f"Shape of axes {tuple(-1 if ax is None else len(ax) for ax in axes)} does not "
                             f"match shape of array {self.arr.shape}")

    def to_cifti(self, default_axis=None):
        """
        Create a CIFTI image from the data

        :param default_axis: What to use as an axis along any undefined dimensions

            - By default an error is raised
            - if set to "scalar" a ScalarAxis is used with names of "default {index}"
            - if set to "series" a SeriesAxis is used

        :return: nibabel CIFTI image
        """
        if any(ax is None for ax in self.axes):
            if default_axis is None:
                raise ValueError("Can not store to CIFTI without defining what is stored along each dimension")
            elif default_axis == 'scalar':
                def get_axis(n: int):
                    return cifti2_axes.ScalarAxis([f'default {idx + 1}' for idx in range(n)])
            elif default_axis == 'series':
                def get_axis(n: int):
                    return cifti2_axes.SeriesAxis(0, 1, n)
            else:
                raise ValueError(f"default_axis should be set to None, 'scalar', or 'series', not {default_axis}")
            new_axes = [
                get_axis(sz) if ax is None else ax
                for ax, sz in zip(self.axes, self.arr.shape)
            ]
        else:
            new_axes = list(self.axes)

        data = self.arr
        if data.ndim == 1:
            # CIFTI axes are always at least 2D
            data = data[None, :]
            new_axes.insert(0, cifti2_axes.ScalarAxis(['default']))

        return nib.Cifti2Image(data, header=new_axes)

    @classmethod
    def from_cifti(cls, filename, writable=False):
        """
        Creates new greyordinate object from dense CIFTI file

        :param filename: CIFTI filename or :class:`nib.Cifti2Image` object
        :param writable: if True, opens data array in writable mode
        """
        if isinstance(filename, str):
            img = nib.load(filename)
        else:
            img = filename

        if not isinstance(img, nib.Cifti2Image):
            raise ValueError(f"Input {filename} should be CIFTI filename or nibabel Cifti2Image")

        if writable:
            data = np.memmap(filename, img.dataobj.dtype, mode='r+',
                             offset=img.dataobj.offset, shape=img.shape, order='F')
        else:
            data = np.asanyarray(img.dataobj)

        axes = [img.header.get_axis(idx) for idx in range(data.ndim)]

        if isinstance(axes[-1], cifti2_axes.BrainModelAxis):
            return DenseCifti(data, axes)
        elif isinstance(axes[-1], cifti2_axes.ParcelsAxis):
            return ParcelCifti(data, axes)
        raise ValueError("Last axis of CIFTI object should be a BrainModelAxis or ParcelsAxis")

    def save(self, cifti_filename, default_axis=None):
        """
        Writes this sparse representation to/from a filename

        :param cifti_filename: output filename
        :param default_axis: What to use as an axis along any undefined dimensions

            - By default an error is raised
            - if set to "scalar" a ScalarAxis is used with names of "default {index}"
            - if set to "series" a SeriesAxis is used
        :return:
        """
        self.to_cifti(default_axis).to_filename(addExt(cifti_filename, defaultExt=self.extension, mustExist=False))

    @classmethod
    def from_gifti(cls, filename, mask_values=(0, np.nan)):
        """
        Creates a new greyordinate object from a GIFTI file

        :param filename: GIFTI filename
        :param mask_values: values to mask out
        :return: greyordinate object representing the unmasked vertices
        """
        if isinstance(filename, str):
            img = nib.load(filename)
        else:
            img = filename
        datasets = [darr.data for darr in img.darrays]
        if len(datasets) == 1:
            data = datasets[0]
        else:
            data = np.concatenate(
                [np.atleast_2d(d) for d in datasets], axis=0
            )
        mask = np.ones(data.shape, dtype='bool')
        for value in mask_values:
            if value is np.nan:
                mask &= ~np.isnan(data)
            else:
                mask &= ~(data == value)
        while mask.ndim > 1:
            mask = mask.any(0)

        anatomy = BrainStructure.from_gifti(img)

        bm_axes = cifti2_axes.BrainModelAxis.from_mask(mask, name=anatomy.cifti)
        return DenseCifti(data[..., mask], [bm_axes])

    @classmethod
    def from_image(cls, input, mask_values=(np.nan, 0)):
        """
        Creates a new greyordinate object from a NIFTI file

        :param input: FSL :class:`image.Image` object
        :param mask_values: which values to mask out
        :return: greyordinate object representing the unmasked voxels
        """
        img = image.Image(input)

        mask = np.ones(img.data.shape, dtype='bool')
        for value in mask_values:
            if value is np.nan:
                mask &= ~np.isnan(img.data)
            else:
                mask &= ~(img.data == value)
        while mask.ndim > 3:
            mask = mask.any(-1)
        if np.sum(mask) == 0:
            raise ValueError("No unmasked voxels found in NIFTI image")

        inverted_data = np.transpose(img.data[mask], tuple(range(1, img.data.ndim - 2)) + (0, ))
        bm_axes = cifti2_axes.BrainModelAxis.from_mask(mask, affine=img.nibImage.affine)
        return DenseCifti(inverted_data, [bm_axes])


class DenseCifti(Cifti):
    """
    Represents sparse data defined for a subset of voxels and vertices (i.e., greyordinates)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.brain_model_axis, cifti2_axes.BrainModelAxis):
            raise ValueError(f"DenseCifti expects a BrainModelAxis as last axes object, not {type(self.brain_model_axis)}")

    @property
    def brain_model_axis(self, ) -> cifti2_axes.BrainModelAxis:
        return self.axes[-1]

    @property
    def extension(self, ):
        if self.arr.ndim == 1:
            return dense_extensions[cifti2_axes.ScalarAxis]
        return dense_extensions[type(self.axes[-2])]

    def to_image(self, fill=0) -> image.Image:
        """
        Get the volumetric data as an :class:`image.Image`
        """
        if self.brain_model_axis.volume_mask.sum() == 0:
            raise ValueError(f"Can not create volume without voxels in {self}")
        data = np.full(self.brain_model_axis.volume_shape + self.arr.shape[:-1], fill,
                       dtype=self.arr.dtype)
        voxels = self.brain_model_axis.voxel[self.brain_model_axis.volume_mask]
        data[tuple(voxels.T)] = np.transpose(self.arr, (-1,) + tuple(range(self.arr.ndim - 1)))[
            self.brain_model_axis.volume_mask]
        return image.Image(data, xform=self.brain_model_axis.affine)

    def surface(self, anatomy, fill=np.nan, partial=False):
        """
        Gets a specific surface

        If `partial` is True a view of the data rather than a copy is returned.

        :param anatomy: BrainStructure or string like 'CortexLeft' or 'CortexRight'
        :param fill: which value to fill the array with if not all vertices are defined
        :param partial: only return the part of the surface defined in the greyordinate file (ignores `fill` if set)
        :return:
            - if not partial: (..., n_vertices) array
            - if partial: tuple with (N, ) int array with indices on the surface included in (..., N) array
        """
        if isinstance(anatomy, str):
            anatomy = BrainStructure.from_string(anatomy, issurface=True)
        if anatomy.cifti not in self.brain_model_axis.name:
            raise ValueError(f"No surface data for {anatomy.cifti} found")
        slc, bm = None, None
        arr = np.full(self.arr.shape[:-1] + (self.brain_model_axis.nvertices[anatomy.cifti],), fill,
                      dtype=self.arr.dtype)
        for name, slc_try, bm_try in self.brain_model_axis.iter_structures():
            if name == anatomy.cifti:
                if partial:
                    if bm is not None:
                        raise ValueError(f"Surface {anatomy} does not form a contiguous block")
                    slc, bm = slc_try, bm_try
                else:
                    arr[..., bm_try.vertex] = self.arr[..., slc_try]
        if not partial:
            return arr
        else:
            return bm.vertex, self.arr[..., slc]


class ParcelCifti(Cifti):
    """
    Represents sparse data defined at specific parcels
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not isinstance(self.parcel_axis, cifti2_axes.ParcelsAxis):
            raise ValueError(f"ParcelCifti expects a ParcelsAxis as last axes object, not {type(self.parcel_axis)}")

    @property
    def extension(self, ):
        if self.arr.ndim == 1:
            return parcel_extensions[cifti2_axes.ScalarAxis]
        return parcel_extensions[type(self.axes[-2])]

    @property
    def parcel_axis(self, ) -> cifti2_axes.ParcelsAxis:
        return self.axes[-1]

    def to_image(self, fill=0):
        """
        Get the volumetric data as an :class:`Image`
        """
        data = np.full(self.parcel_axis.volume_shape + self.arr.shape[:-1], fill, dtype=self.arr.dtype)
        written = np.zeros(self.parcel_axis.volume_shape, dtype='bool')
        for idx, write_to in enumerate(self.parcel_axis.voxels):
            if written[tuple(write_to.T)].any():
                raise ValueError("Duplicate voxels in different parcels")
            data[tuple(write_to.T)] = self.arr[np.newaxis, ..., idx]
            written[tuple(write_to.T)] = True
        if not written.any():
            raise ValueError("Parcellation does not contain any volumetric data")
        return image.Image(data, xform=self.parcel_axis.affine)

    def surface(self, anatomy, fill=np.nan, partial=False):
        """
        Gets a specific surface

        :param anatomy: BrainStructure or string like 'CortexLeft' or 'CortexRight'
        :param fill: which value to fill the array with if not all vertices are defined
        :param partial: only return the part of the surface defined in the greyordinate file (ignores `fill` if set)
        :return:
            - if not partial: (..., n_vertices) array
            - if partial: tuple with (N, ) int array with indices on the surface included in (..., N) array
        """
        if isinstance(anatomy, str):
            anatomy = BrainStructure.from_string(anatomy, issurface=True)
        if anatomy.cifti not in self.parcel_axis.nvertices:
            raise ValueError(f"No surface data for {anatomy.cifti} found")

        arr = np.full(self.arr.shape[:-1] + (self.parcel_axis.nvertices[anatomy.cifti],), fill,
                      dtype=self.arr.dtype)
        written = np.zeros(self.parcel_axis.nvertices[anatomy.cifti], dtype='bool')
        for idx, vertices in enumerate(self.parcel_axis.vertices):
            if anatomy.cifti not in vertices:
                continue
            write_to = vertices[anatomy.cifti]
            if written[write_to].any():
                raise ValueError("Duplicate vertices in different parcels")
            arr[..., write_to] = self.arr[..., idx, np.newaxis]
            written[write_to] = True

        if not partial:
            return arr
        else:
            return np.where(written)[0], arr[..., written]


class BrainStructure(object):
    """Which brain structure does the parent object describe?

    Supports how brain structures are stored in both GIFTI and CIFTI files
    """
    def __init__(self, primary, secondary=None, hemisphere='both', geometry=None):
        """Creates a new brain structure

        :param primary: Name of the brain structure (e.g. cortex, thalamus)
        :param secondary: Further specification of which part of the brain structure is described (e.g. 'white' or
                          'pial' for the cortex)
        :param hemisphere: which hemisphere is the brain structure in ('left', 'right', or 'both')
        :param geometry: does the parent object describe the 'volume' or the 'surface'
        """
        self.primary = primary.lower()
        self.secondary = None if secondary is None else secondary.lower()
        self.hemisphere = hemisphere.lower()
        if geometry not in (None, 'surface', 'volume'):
            raise ValueError(f"Invalid value for geometry: {geometry}")
        self.geometry = geometry

    def __eq__(self, other):
        """Two brain structures are equal if they could describe the same structure
        """
        if isinstance(other, str):
            other = self.from_string(other)
        match_primary = (self.primary == other.primary or self.primary == 'all' or other.primary == 'all' or
                         self.primary == other.geometry or self.geometry == other.primary)
        match_hemisphere = self.hemisphere == other.hemisphere
        match_secondary = (self.secondary is None or other.secondary is None or self.secondary == other.secondary)
        match_geometry = (self.geometry is None or other.geometry is None or self.geometry == other.geometry)
        return match_primary and match_hemisphere and match_secondary and match_geometry

    @property
    def gifti(self, ):
        """Returns the keywords needed to define the surface in the meta information of a GIFTI file
        """
        main = self.primary.capitalize() + ('' if self.hemisphere == 'both' else self.hemisphere.capitalize())
        res = {'AnatomicalStructurePrimary': main}
        if self.secondary is not None:
            res['AnatomicalStructureSecondary'] = self.secondary.capitalize()
        return res

    def __str__(self, ):
        """Returns a short description of the brain structure
        """
        if self.secondary is None:
            return self.primary.capitalize() + self.hemisphere.capitalize()
        else:
            return "%s%s(%s)" % (self.primary.capitalize(), self.hemisphere.capitalize(), self.secondary)

    @property
    def cifti(self, ):
        """Returns a description of the brain structure needed to define the surface in a CIFTI file
        """
        return 'CIFTI_STRUCTURE_' + self.primary.upper() + ('' if self.hemisphere == 'both' else ('_' + self.hemisphere.upper()))

    @classmethod
    def from_string(cls, value, issurface=None):
        """Parses a string to find out which brain structure is being described

        :param value: string to be parsed
        :param issurface: defines whether the object describes the volume or surface of the brain structure (default: surface if the brain structure is the cortex volume otherwise)
        """
        if '_' in value:
            items = [val.lower() for val in value.split('_')]
            if items[-1] in ['left', 'right', 'both']:
                hemisphere = items[-1]
                others = items[:-1]
            elif items[0] in ['left', 'right', 'both']:
                hemisphere = items[0]
                others = items[1:]
            else:
                hemisphere = 'both'
                others = items
            if others[0] in ['nifti', 'cifti', 'gifti']:
                others = others[2:]
            primary = '_'.join(others)
        else:
            low = value.lower()
            if 'left' == low[-4:]:
                hemisphere = 'left'
                primary = low[:-4]
            elif 'right' == low[-5:]:
                hemisphere = 'right'
                primary = low[:-5]
            elif 'both' == low[-4:]:
                hemisphere = 'both'
                primary = low[:-4]
            else:
                hemisphere = 'both'
                primary = low
        if issurface is None:
            issurface = primary == 'cortex'
        if primary == '':
            primary = 'all'
        return cls(primary, None, hemisphere, 'surface' if issurface else 'volume')

    @classmethod
    def from_gifti(cls, gifti_obj):
        """
        Extracts the brain structure from a GIFTI object
        """
        primary_str = 'AnatomicalStructurePrimary'
        secondary_str = 'AnatomicalStructureSecondary'
        primary = "other"
        secondary = None
        for meta in [gifti_obj] + gifti_obj.darrays:
            if primary_str in meta.meta.metadata:
                primary = meta.meta.metadata[primary_str]
            if secondary_str in meta.meta.metadata:
                secondary = meta.meta.metadata[secondary_str]
        anatomy = cls.from_string(primary, issurface=True)
        anatomy.secondary = None if secondary is None else secondary.lower()
        return anatomy


def load(filename, mask_values=(0, np.nan), writable=False) -> Union[DenseCifti, ParcelCifti]:
    """
    Reads CIFTI data from the given file

    File can be:

        - NIFTI file
        - GIFTI file
        - CIFTI file

    :param filename: input filename
    :param mask_values: which values are outside of the mask for NIFTI or GIFTI input
    :param writable: allow to write to disk
    :return: appropriate CIFTI sub-class (parcellated or dense)
    """
    possible_extensions = (
        tuple(dense_extensions.values()) +
        tuple(parcel_extensions.values()) +
        tuple(image.ALLOWED_EXTENSIONS) +
        ('.shape.gii', '.gii')
    )
    if isinstance(filename, str):
        filename = addExt(filename, possible_extensions, fileGroups=image.FILE_GROUPS)
        img = nib.load(filename)
    else:
        img = filename

    if isinstance(img, nib.Cifti2Image):
        return Cifti.from_cifti(img, writable=writable)
    if isinstance(img, nib.GiftiImage):
        if writable:
            raise ValueError("Can not open GIFTI file in writable mode")
        return Cifti.from_gifti(img, mask_values)
    try:
        vol_img = image.Image(img)
    except ValueError:
        raise ValueError(f"I do not know how to convert {type(img)} into greyordinates (from {filename})")
    if writable:
        raise ValueError("Can not open NIFTI file in writable mode")
    return Cifti.from_image(vol_img, mask_values)
