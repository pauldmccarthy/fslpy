#!/usr/bin/env python
#
# dicom.py - Access data in DICOM directories.
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

   enabled
   scanDir
   loadSeries

See: https://github.com/rordenlab/dcm2niix/

.. note:: These functions will not work if an executable called ``dcm2niix``
          cannot be found.
"""


import               os
import os.path    as op
import subprocess as sp
import               re
import               sys
import               glob
import               json
import               shlex
import               logging
import               binascii

import numpy      as np
import nibabel    as nib

import fsl.utils.tempdir as tempdir
import fsl.utils.memoize as memoize
import fsl.data.image    as fslimage


log = logging.getLogger(__name__)


MIN_DCM2NIIX_VERSION = (1, 0, 2017, 12, 15)
"""Minimum version of ``dcm2niix`` that is required for this module to work.
"""


CRC_DCM2NIIX_VERSION = (1, 0, 2019, 9, 2)
"""For versions of ``dcm2niix`` orf this version or newer, the ``-n`` flag,
used to convert a single DICOM series, requires that a CRC checksum
identifying the series be passed (see the :func:`seriesCRC`
function). Versions prior to this require the series number to be passed.
"""


class DicomImage(fslimage.Image):
    """The ``DicomImage`` is a volumetric :class:`.Image` with some associated
    DICOM metadata.

    The ``Image`` class is used to manage the data and the voxel-to-world
    transformation. Additional DICOM metadata may be accessed via the
    :class:`.Image` metadata access methods.
    """


    def __init__(self, image, metadata, dicomDir, *args, **kwargs):
        """Create a ``DicomImage``.

        :arg image:    Passed through to :meth:`.Image.__init__`.
        :arg metadata: Dictionary containing DICOM meta-data.
        :arg dicomDir: Directory that the dicom image was loaded from.
        """
        fslimage.Image.__init__(self, image, *args, **kwargs)

        self.__dicomDir = dicomDir

        if metadata is not None:
            for k, v in metadata.items():
                self.setMeta(k, v)


    @property
    def dicomDir(self):
        """Returns the directory that the DICOM image data was loaded from. """
        return self.__dicomDir


@memoize.memoize
def installedVersion():
    """Return a tuple describing the version of ``dcm2niix`` that is installed,
    or ``None`` if dcm2niix cannot be found, or its version not parsed.

    The returned tuple contains the following fields, all integers:
      - Major version number
      - Minor version number
      - Year
      - Month
      - Day
    """

    cmd            = 'dcm2niix -h'
    versionPattern = re.compile(r'v'
                                r'(?P<major>[0-9]+)\.'
                                r'(?P<minor>[0-9]+)\.'
                                r'(?P<year>[0-9]{4})'
                                r'(?P<month>[0-9]{2})'
                                r'(?P<day>[0-9]{2})')

    try:
        output = sp.check_output(cmd.split()).decode()
        output = [l for l in output.split('\n') if 'version' in l.lower()]
        output = '\n'.join(output).split()

        for word in output:

            match = re.match(versionPattern, word)

            if match is not None:
                return (int(match.group('major')),
                        int(match.group('minor')),
                        int(match.group('year')),
                        int(match.group('month')),
                        int(match.group('day')))

    except Exception as e:
        log.debug('Error parsing dcm2niix version string: {}'.format(e))
    return None


def compareVersions(v1, v2):
    """Compares two ``dcm2niix`` versions ``v1`` and ``v2``.  The versions are
    assumed to be in the format returned by :func:`installedVersion`.

    :returns: - 1 if ``v1`` is newer than ``v2``
              - -1 if ``v1`` is older than ``v2``
              - 0 if ``v1`` the same as ``v2``.
    """

    for iv1, iv2 in zip(v1, v2):
        if   iv1 > iv2: return  1
        elif iv1 < iv2: return -1
    return 0


def enabled():
    """Returns ``True`` if ``dcm2niix`` is present, and recent enough,
    ``False`` otherwise.
    """
    installed = installedVersion()
    required  = MIN_DCM2NIIX_VERSION
    return ((installed is not None) and
            (compareVersions(installed, required) >= 0))


def scanDir(dcmdir):
    """Uses the ``dcm2niix -b o`` option to generate a BIDS sidecar JSON
    file for each series in the given DICOM directory. Reads them all in,
    and returns them as a sequence of dicts.

    Some additional metadata is added to each dictionary:
     - ``DicomDir``: The absolute path to ``dcmdir``

    :arg dcmdir: Directory containing DICOM series

    :returns:    A list of dicts, each containing the BIDS sidecar JSON
                 metadata for one DICOM series.
    """

    if not enabled():
        raise RuntimeError('dcm2niix is not available or is too old')

    dcmdir = op.abspath(dcmdir)
    cmd    = 'dcm2niix -b o -ba n -f %s -o . "{}"'.format(dcmdir)
    series = []

    with tempdir.tempdir() as td:

        with open(os.devnull, 'wb') as devnull:
            sp.call(shlex.split(cmd), stdout=devnull, stderr=devnull)

        files = glob.glob(op.join(td, '*.json'))

        if len(files) == 0:
            return []

        for fn in files:
            with open(fn, 'rt') as f:
                meta             = json.load(f)
                meta['DicomDir'] = dcmdir
                # SeriesDescription is not
                # guaranteed to be present
                if 'SeriesDescription' not in meta:
                    meta['SeriesDescription'] = meta['SeriesNumber']
                series.append(meta)

    # sort by series number
    def key(s):
        return s.get('SeriesNumber', sys.maxsize)

    series = list(sorted(series, key=key))

    return series


def seriesCRC(series):
    """Calculate a checksum string of the given DICOM series.

    The returned string is of the form::

         SeriesCRC[.echonumber]

    Where ``SeriesCRC`` is an unsigned integer which is the CRC32
    checksum of the ``SeriesInstanceUID``, and ``echonumber`` is
    the ``EchoNumber`` of the series - this is only present for
    multi-echo data, where the series is from the second or subsequent
    echos.

    :arg series: Dict containing BIDS metadata about a DICOM series,
                 as returned by :func:`scanDir`.

    :returns:    String containing a CRC32 checksum for the series.
    """

    uid  = series.get('SeriesInstanceUID', None)
    echo = series.get('EchoNumber',        None)

    if uid is None:
        return None

    crc32 = str(binascii.crc32(uid.encode()))

    if echo is not None and echo > 1:
        crc32 = '{}.{}'.format(crc32, echo)

    return crc32


def loadSeries(series):
    """Takes a DICOM series meta data dictionary, as returned by
    :func:`scanDir`, and loads the associated data as one or more NIFTI
    images.

    :arg series: Dictionary as returned by :func:`scanDir`, containing
                 meta data about one DICOM data series.

    :returns:    List containing one or more :class:`.DicomImage` objects.
    """

    if not enabled():
        raise RuntimeError('dcm2niix is not available or is too old')

    dcmdir  = series['DicomDir']
    snum    = series['SeriesNumber']
    desc    = series['SeriesDescription']
    version = installedVersion()

    # Newer versions of dcm2niix
    # require a CRC to identify
    # series
    if compareVersions(version, CRC_DCM2NIIX_VERSION) >= 0:
        ident = seriesCRC(series)

    # Older versions require
    # the series number
    else:
        ident = snum

    cmd = 'dcm2niix -b n -f %s -z n -o . -n "{}" "{}"'.format(ident, dcmdir)

    with tempdir.tempdir() as td:

        with open(os.devnull, 'wb') as devnull:
            sp.call(shlex.split(cmd), stdout=devnull, stderr=devnull)

        files  = glob.glob(op.join(td, '{}*.nii'.format(snum)))
        images = [nib.load(f, mmap=False) for f in files]

        # copy images so nibabel no longer
        # refs to the files (as they will
        # be deleted), and force-load the
        # the image data into memory (to
        # avoid any disk accesses due to
        # e.g. memmap)
        images = [nib.Nifti1Image(np.asanyarray(i.dataobj), None, i.header)
                  for i in images]

        return [DicomImage(i, series, dcmdir, name=desc) for i in images]
