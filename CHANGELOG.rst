This document contains the ``fslpy`` release history in reverse chronological
order.


1.6.0 (Under development)
-------------------------


* The :class:`.TriangleMesh` class now uses the ``trimesh`` library
  (https://github.com/mikedh/trimesh) to perform ray-mesh intersections,
  via a new :meth:`.TriangleMesh.rayIntersection` method.
* Optional dependencies ``wxpython``, ``indexed_gzip``, ``trimesh``, and
  ``rtree`` are now listed separately, so ``fslpy`` can be used without
  them (although relevant functionality will be disabled).



1.5.4 (Wednesday January 10th 2018)
-----------------------------------


* Actually included the fix that was supposed to be in version 1.5.3.


1.5.3 (Tuesday January 9th 2018)
--------------------------------


* Bug fix to :meth:`.ImageWrapper.__expandCoverage` - was not correctly handling
  large images with lots of ``nan`` values.


1.5.2 (Tuesday January 2nd 2018)
--------------------------------


* Fixed issue with ``MANIFEST.in`` file.


1.5.1 (Thursday December 14th 2017)
-----------------------------------


* Fixed bug in :func:`.dicom.scanDir` function related to data series ordering.


1.5.0 (Wednesday December 13th 2017)
------------------------------------


* New module :mod:`.dicom`, which provides a thin wrapper on top of Chris
  Rorden's `dcm2niix <https://github.com/rordenlab/dcm2niix>`_.
* New module :mod:`.tempdir`, which has a convenience function for creating
  temporary directories.
* Fixed small issue in :meth:`.Image.dtype` - making sure that it access
  image data via the :class:`.ImageWrapper`, rather than via the `Nifti1Image`
  object.


1.4.2 (Tuesday December 5th 2017)
---------------------------------


* New function :func:`.transform.rmsdev` function, which implements the RMS
  deviation equation for comparing two affine transformations (FMRIB Technical
  Report TR99MJ1, available at https://www.fmrib.ox.ac.uk/datasets/techrep/).
* Some small bugfixes to the :mod:`.atlasq` and :mod:`.atlases` moduless.


1.4.1 (Thursday November 9th 2017)
----------------------------------


* Fixed bug in ``setup.py``.


1.4.0 (Thursday November 9th 2017)
----------------------------------


* The :func:`.uniquePrefix` function now raises a :exc:`~.path.PathError`
  instead of a :exc:`.ValueError`, when an invalid path is provided.
* The :mod:`fsl.utils.async` module is now deprecated, as ``async`` will
  become a reserved word in Python 3.7. It has been renamed to
  ``fsl.utils.idle``, with no other API changes.
* For image file pairs, the ``hdr`` extension now takes precedence over the
  ``img`` extension, when using the :func:`fsl.data.image.addExt` (and
  related) functions.
* The :func:`fsl.utils.path.addExt` function accepts a new parameter,
  ``unambiguous`` which causes it to allow an ambiguous prefix, and return
  all matching paths.
* New :mod:`~fsl.scripts.atlasq` application, intended to replace the FSL
  ``atlasquery`` tool.
* New :mod:`~fsl.scripts.imglob` application, intended to replace the FSL
  ``imglob`` tool.
* The :meth:`.Image.resample` method explicitly raises a ``ValueError``
  if incompatible shapes are provided.


1.3.1 (Wednesday October 25th 2017)
-----------------------------------


* Fixed bug in :meth:`.Platform.wxPlatform` causing it to always return
  ``WX_UNKNOWN``.


1.3.0 (Wednesday October 25th 2017)
-----------------------------------


* :class:`.Atlas` classes can now pass ``kwargs`` through to the
  :class:`.Image` constructor.
* :class:`.LabelAtlas` image values no longer need to match the index of the
  label into the :class:`.AtlasDescription` ``labels`` list. This means that
  label atlas XML files may contain non-sequential label values.
* :class:`.Cache` now implements ``__getitem__`` and ``__setitem__``
* The :func:`.image.read_segments` function (monkey-patched into ``nibabel``)
  is deprecated, as it is no longer necessary as of ``nibabel`` 2.2.0.
* :func:`.platform.isWidgetAlive` is deprecated in favour of an equivalent
  function in the ``fsleyes-widgets`` library.
* ``scipy`` is now explicitly listed as a requirement (this should have been
  done in 1.2.1).



1.2.2 (Saturday October 21st 2017)
----------------------------------


* The :func:`.image.read_segments` function is only monkey-patched into
  ``nibabel`` 2.1.0, as it breaks when used with 2.2.0.


1.2.1 (Saturday October 7th 2017)
---------------------------------


* If an :class:`.Image` is passed an existing ``nibabel`` header object,
  it creates a copy, rather than using the original.
* New :meth:`.Image.resample` method, which resamples the image data to a
  different resolution.
* New :meth:`.LabelAtlas.coordLabel`, :meth:`.LabelAtlas.maskLabel`,
  :meth:`.ProbabilisticAtlas.coordProportions` and
  :meth:`.ProbabilisticAtlas.maskProportions` methods. The ``coord``
  methods perform coordinate queries in voxel or world coordinates,
  and the ``mask`` methods perform mask-based queries.


1.2.0 (Thursday September 21st 2017)
------------------------------------


* :meth:`fsl.data.image.Nifti.voxelsToScaledVoxels` method deprecated in
  favour of new :meth:`.Nifti.voxToScaledVoxMat` and
  :meth:`Nifti.scaledVoxToVoxMat` properties.


1.1.0 (Monday September 11th 2017)
----------------------------------


* The :mod:`fsl` package is now a ``pkgutil``-style `namespace package
  <https://packaging.python.org/guides/packaging-namespace-packages/>`_, so it
  can be used for different projects.
* Updates to :class:`fsl.data.image.Nifti` and :class:`fsl.data.image.Image`
  to add support for images with more than 4 dimensions:
  - New ``ndims`` property
  - ``is4DImage`` method deprecated


1.0.5 (Thursday August 10th 2017)
---------------------------------


* New functions and further adjustments in :mod:`fsl.utils.transform` module:

 - :func:`.transform.rotMatToAffine` converts a ``(3, 3)`` rotation matrix
   into a ``(4, 4)`` affine.
 - :func:`.transform.transformNormal` applies an affine transform to one or
   more vectors.
 - :func:`.transform.veclength` calculates the length of a vector
 - :func:`.transform.normalise` normalises a vector
 - :func:`.transform.scaleOffsetXform` adjusted to have more flexibility with
   respect to inputs.
 - :func:`.transform.decompose` can return rotations either as three
   axis-angles, or as a rotation matrix

* Updates to :class:`fsl.data.mesh.TriangleMesh` - ``vertices`` and ``indices``
  are now ``property`` attributes. New lazily generated ``normals`` and
  ``vnormals`` properties (face and vertex normals respectively). Option
  to ``__init__`` to fix the face winding order of a mesh.
* :func:`fsl.utils.memoize.memoize` decorator made into a class rather than a
  function. The new :class:`.Memoize` class has an ``invalidate`` method, which
  clears the cache.


1.0.4 (Friday July 14th 2017)
-----------------------------


* Python 2/3 compatibility fix to :mod:`fsl.utils.callfsl`.
* Fix to :func:`fsl.utils.transform.scaleOffsetXform` - accepts inputs
  that are not lists.
* :func:`fsl.utils.transform.compose` accepts either a sequence of three
  axis angles, or a ``(3, 3)`` rotation matrix.


1.0.3 (Sunday June 11th 2017)
-----------------------------


* Fix to :mod:`fsl.utils.async` which was breaking environments where multiple
  ``wx.App`` instances were being created.


1.0.2 (Thursday June 8th 2017)
------------------------------


* Python 2/3 compatibility fixes
* New :func:`fsl.version.patchVersion` function.


1.0.1 (Sunday 4th June 2017)
----------------------------


* New version number parsing functions in :mod:`fsl.version`.


1.0.0 (Saturday May 27th 2017)
------------------------------


* Removed many GUI-related modules - they have been moved to the
  ``fsleyes-widgets`` project. The following modules have been removed:
  - :mod:`fsl.utils.colourbarbitmap`
  - :mod:`fsl.utils.dialog`
  - :mod:`fsl.utils.imagepanel`
  - :mod:`fsl.utils.layout`
  - :mod:`fsl.utils.platform`
  - :mod:`fsl.utils.runwindow`
  - :mod:`fsl.utils.status`
  - :mod:`fsl.utils.textbitmap`
  - :mod:`fsl.utils.typedict`
  - :mod:`fsl.utils.webpage`
* :mod:`fsl.utils.settings` module rewritten. It no longer uses ``wx``,
  but instead stores plain-text and ``pickle`` files in the user's home
  directory.
* Software GL renderer test in :mod:`fsl.utils.platform` is more lenient
* New :class:`.AtlasLabel` class
* :meth:`.Image.__init__` allows arguments to be passed through to
  ``nibabel.load``.
* New :meth:`.Nifti.strval` method to handle escaped strings in NIFTI headers.
* Python 2/3 compatibility fixes


0.11.0 (Thursday April 20th 2017)
---------------------------------


* First public release as part of FSL 5.0.10
