#!/usr/bin/env python
#
# dicom.py -
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.DicomImage` class, which represents a
volumetric DICOM data series. The ``DicomImage`` is simply an :class:`.`Image`
which provides accessors for additional DICOM meta data.

The following other functions are provided in this module, which are thin
wrappers around functionality provided by Chris Rorden's ``dcm2niix`` program:

.. autosummary::
   :nosignatures:

   scanDir
   loadSeries

.. note:: These functions will not work if an executable called ``dcm2niix``
          cannot be found.

.. see:: https://github.com/rordenlab/dcm2niix/
"""


import os.path    as op
import subprocess as sp
import               glob
import               json

import nibabel    as nib

import fsl.utils.tempdir as tempdir
import fsl.data.image    as fslimage


class DicomImage(fslimage.Image):
    """The ``DicomImage`` is a volumetric :class:`.Image` with some associated
    DICOM metadata.

    The ``Image`` class is used to manage the data and the voxel-to-world
    transformation. Additional DICOM metadata may be accessed via TODO
    """

    def __init__(self, image, meta, *args, **kwargs):
        """Create a ``DicomImage``.

        :arg image: Passed through to :meth:`.Image.__init__`.
        :arg meta:  Dictionary containing DICOM meta-data.
        """
        fslimage.Image.__init__(self, image, *args, **kwargs)
        self.__meta = meta


    def keys(self):
        """Returns the keys contained in the DICOM metadata dictionary
        (``dict.keys``).
        """
        return self.__meta.keys()


    def values(self):
        """Returns the values contained in the DICOM metadata dictionary
        (``dict.values``).
        """
        return self.__meta.values()


    def items(self):
        """Returns the items contained in the DICOM metadata dictionary
        (``dict.items``).
        """
        return self.__meta.items()


    def get(self, *args, **kwargs):
        """Returns the metadata value with the specified key (``dict.get``).
        """
        return self.__meta.get(*args, **kwargs)


def scanDir(dcmdir):
    """Uses ``dcm2niix`` to scans the given DICOM directory, and returns a
    list of dictionaries, one for each data series that was identified.
    Each dictionary is populated with some basic metadata about the series.

    :arg dcmdir: Directory containing DICOM files.

    :returns:    A list of dictionaries, each containing metadata about
                 one DICOM data series.
    """

    dcmdir = op.abspath(dcmdir)
    cmd    = 'dcm2niix -b o -ba n -f %s -o . {}'.format(dcmdir)

    with tempdir.tempdir() as td:

        sp.call(cmd.split(), stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        files = glob.glob(op.join(td, '*.json'))

        if len(files) == 0:
            return []

        # sort numerically by series number
        def sortkey(f):
            return int(op.splitext(op.basename(f))[0])

        files = sorted(files, key=sortkey)

        series = []
        for fn in files:
            with open(fn, 'rt') as f:
                meta = json.load(f)
                meta['DicomDir'] = dcmdir
                series.append(meta)

        return series


def loadSeries(series):
    """Takes a DICOM series meta data dictionary, as returned by
    :func:`scanDir`, and loads the associated data as one or more NIFTI
    images.

    :arg series: Dictionary as returned by :func:`scanDir`, containing
                 meta data about one DICOM data series.

    :returns:    List containing one or more :class:`.DicomImage` objects.
    """

    dcmdir = series['DicomDir']
    snum   = series['SeriesNumber']
    desc   = series['SeriesDescription']
    cmd    = 'dcm2niix -b n -f %s -z n -o . {}'.format(dcmdir)

    with tempdir.tempdir() as td:

        sp.call(cmd.split(), stdout=sp.DEVNULL, stderr=sp.DEVNULL)

        files  = glob.glob(op.join(td, '{}.nii'.format(snum)))
        images = [nib.load(f, mmap=False) for f in files]

        return [DicomImage(i, series, name=desc) for i in images]
