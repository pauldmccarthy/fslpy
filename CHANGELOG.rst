This document contains the ``fslpy`` release history in reverse chronological
order.


1.3.0 (Wednesday 25th October 2017)
-----------------------------------


* :class:`.Atlas` classes can now pass ``kwargs`` through to the
  :class:`.Image` constructor.
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
