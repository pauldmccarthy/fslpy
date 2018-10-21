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
import               glob
import               json
import               logging
import               deprecation

import nibabel    as nib

import fsl.utils.tempdir as tempdir
import fsl.utils.memoize as memoize
import fsl.data.image    as fslimage


log = logging.getLogger(__name__)


MIN_DCM2NIIX_VERSION = (1, 0, 2017, 12, 15)
"""Minimum version of dcm2niix that is required for this module to work. """


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


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use metaKeys instead')
    def keys(self):
        """Deprecated - use :meth:`.Image.metaKeys`. """
        return self.metaKeys()


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use metaValues instead')
    def values(self):
        """Deprecated - use :meth:`.Image.metaValues`. """
        return self.metaValues()


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use metaItems instead')
    def items(self):
        """Deprecated - use :meth:`.Image.metaItems`. """
        return self.metaItems()


    @deprecation.deprecated(deprecated_in='1.6.0',
                            removed_in='2.0.0',
                            details='Use getMeta instead')
    def get(self, *args, **kwargs):
        """Deprecated - use :meth:`.Image.getMeta`. """
        return self.getMeta(*args, **kwargs)


@memoize.memoize
def enabled():
    """Returns ``True`` if ``dcm2niix`` is present, and recent enough,
    ``False`` otherwise.
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

            if match is None:
                continue

            installedVersion = (
                int(match.group('major')),
                int(match.group('minor')),
                int(match.group('year')),
                int(match.group('month')),
                int(match.group('day')))

            # make sure installed version
            # is equal to or newer than
            # minimum required version
            for iv, mv in zip(installedVersion, MIN_DCM2NIIX_VERSION):
                if   iv > mv: return True
                elif iv < mv: return False

            # if we get here, versions are equal
            return True

    except Exception as e:
        log.debug('Error parsing dcm2niix version string: {}'.format(e))

    return False


def scanDir(dcmdir):
    """Uses ``dcm2niix`` to scans the given DICOM directory, and returns a
    list of dictionaries, one for each data series that was identified.
    Each dictionary is populated with some basic metadata about the series.

    :arg dcmdir: Directory containing DICOM files.

    :returns:    A list of dictionaries, each containing metadata about
                 one DICOM data series.
    """

    if not enabled():
        raise RuntimeError('dcm2niix is not available or is too old')

    dcmdir      = op.abspath(dcmdir)
    cmd         = 'dcm2niix -b o -ba n -f %s -o . {}'.format(dcmdir)
    snumPattern = re.compile('^[0-9]+')

    with tempdir.tempdir() as td:

        with open(os.devnull, 'wb') as devnull:
            sp.call(cmd.split(), stdout=devnull, stderr=devnull)

        files = glob.glob(op.join(td, '*.json'))

        if len(files) == 0:
            return []

        # sort numerically by series number if possible
        try:
            def sortkey(f):
                match = re.match(snumPattern, f)
                snum  = int(match.group(0))
                return snum

            files = sorted(files, key=sortkey)

        except Exception:
            files = sorted(files)

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

    if not enabled():
        raise RuntimeError('dcm2niix is not available or is too old')

    dcmdir = series['DicomDir']
    snum   = series['SeriesNumber']
    desc   = series['SeriesDescription']
    cmd    = 'dcm2niix -b n -f %s -z n -o . -n {} {}'.format(snum, dcmdir)

    with tempdir.tempdir() as td:

        with open(os.devnull, 'wb') as devnull:
            sp.call(cmd.split(), stdout=devnull, stderr=devnull)

        files  = glob.glob(op.join(td, '{}*.nii'.format(snum)))
        images = [nib.load(f) for f in files]

        # Force-load images into memory
        [i.get_data() for i in images]

        return [DicomImage(i, series, dcmdir, name=desc) for i in images]
