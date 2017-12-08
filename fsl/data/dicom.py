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
wrappers around functionality provided by ``pydicom`` and ``dcmstack``:

.. autosummary::
   :nosignatures:

   scanDir
   stack
"""


import os
import fnmatch

import pydicom as dicom

from . import dcmstack

from . import image as fslimage


class DicomImage(fslimage.Image):
    """The ``DicomImage`` is a volumetric :class:`.Image` with associated
    DICOM metadata.

    The ``Image`` class is used to manage the data and the voxel-to-world
    transformation. Additional DICOM metadata may be accessed via TODO
    """

    def __init__(self, image, meta):
        """Create a ``DicomImage``.
        """
        fslimage.Image.__init__(self, image)


def scanDir(dcmdir, filePattern='*.dcm', callback=None):
    """Recursively scans the given DICOM directory, and returns a dictionary
    which contains all of the data series that were found.

   :arg dcmdir:       Directory containing DICOM files.

   :arg filePattern:  Glob-like pattern with which to identify DICOM files.
                      Defaults to ``'*.dcm'``.

   :arg callback:     Function which will get called every time a file is
                      loaded, and can be used for e.g. updating progress.
                      Must accept three positional parameters:
                        - ``path``: Path
                        - ``n``:    Index of current path
                        - ``ttl``:  Total number of paths

                      After all files have been loaded, this function is called
                      once more before the files are grouped into data series.
                      For this final call, ``path is None``, and ``n == ttl``.

    :returns:         A list containing one element for each identified data
                      series. Each element itself is a list with one element
                      for each file, where each element is a tuple containing
                      the ``pydicom.dataset.FileDataset``, and a ``dict``
                      containing some basic metadata extracted from the file.

    .. see:: ``dcmstack.parse_and_group`` and ``pydicom.dicomio.dcmread``.
    """

    def default_callback(path, n, ttl):
        pass

    if callback is None:
        callback = default_callback

    # Find all the DICOM files in the directory.
    # If/when we drop python < 3.5, we can use:
    #
    #   glob.glob(op.join(dcmdir, '**', filePattern), recursive=True)
    dcmfiles = []
    for root, dirnames, filenames in os.walk(dcmdir):
        for filename in fnmatch.filter(filenames, filePattern):
            dcmfiles.append(os.path.join(root, filename))

    # No files found
    if len(dcmfiles) == 0:
        return {}

    # Tell pydicom to only load the tags that
    # are necessary to group files into series,
    # and to give us basic metadata.
    tags = [
        'SeriesInstanceUID',
        'SeriesNumber',
        'SeriesDescription',
        'ProtocolName',
        'ImageOrientationPatient',
        'Rows',
        'Columns',
        'PixelSpacing']

    # Load the files one by one
    dcms = []
    for i, path in enumerate(dcmfiles):
        callback(path, i, len(dcmfiles))
        dcms.append(dicom.dcmread(path, defer_size=64, specific_tags=tags))

    callback(None, len(dcmfiles), len(dcmfiles))

    # Group the files into data series
    series = dcmstack.parse_and_group(dcms)

    # parse_and_group returns a dict, with
    # one entry for each data series, where
    # each entry is a list containing
    #   (pydicom file, metadata, filepath)
    #
    # We don't care about the dict keys,
    series = list(series.values())

    return series


def stack(series, callback=None):
    """Takes a DICOM data series, as returned by :func:`scanDir`, and converts
    it to a ``dcmstack.DicomStack``.

    :arg series:

    :arg callback:

    :returns:
    """

    def default_callback(path, n, ttl):
        pass

    if callback is None:
        callback = default_callback

    ds = dcmstack.DicomStack()

    for i, (_, meta, filename) in enumerate(series):
        callback(filename, i, len(series))
        ds.add_dcm(dicom.dcmread(filename), meta)

    return ds
