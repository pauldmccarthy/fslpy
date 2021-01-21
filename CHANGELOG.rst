This document contains the ``fslpy`` release history in reverse chronological
order.


3.5.1 (Thursday 21st January 2021)
----------------------------------


Added
^^^^^


* New :func:`.featanalysis.loadFsf` function, for loading arbitrary ``.fsf``
  files (!276).


Fixed
^^^^^


* Adjustments to :mod:`.dicom` tests to work with different versions of
  ``dcm2niix`` (!277).


3.5.0 (Wednesday 20th January 2021)
-----------------------------------


Added
^^^^^


* New ``fsl_anat.tree``, for use with the :mod:`.filetree` package (!264).
* New :func:`.fsl_prepare_fieldmap` wrapper function (!265).
* The :class:`.fslmaths` wrapper now supports the ``fslmaths -s`` option
  via the :meth:`.fslmaths.smooth` method (!271).


Fixed
^^^^^


* Windows/WSL-specific workaround to the :func:`fsl.utils.run.run` function to
  avoid console windows from popping up, when used from a graphical program
  (!272).


3.4.0 (Tuesday 20th October 2020)
---------------------------------


Added
^^^^^


* New :mod:`.tbss` wrapper functions for `TBSS
  <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TBSS>`_ commands.


Changed
^^^^^^^


* Calls to functions in the :mod:`.assertions` module are disabled when a
  wrapper function is called with ``cmdonly=True``.


3.3.3 (Wednesday 13th October 2020)
-----------------------------------


Changed
^^^^^^^


* The :func:`.fileOrImage` (and related) decorators will not manipulate the
  return value of a decorated function if an argument ``cmdonly=True`` is
  passed. This is so that wrapper functions will directly return the command
  that would be executed when ``cmdonly=True``.


3.3.2 (Tuesday 12th October 2020)
---------------------------------


Changed
^^^^^^^


* Most :func:`.wrapper` functions now accept an argument called ``cmdonly``
  which, if ``True``, will cause the generated command-line call to be
  returned, instead of executed.


3.3.1 (Thursday 8th October 2020)
---------------------------------


Changed
^^^^^^^


* The :func:`.affine.decompose` and :func:`.affine.compose` functions now
  have the ability to return/accept shear components.


Fixed
^^^^^


* Fixed a bug in the :func:`.affine.decompose` function which was corrupting
  the scale estimates when given an affine containing shears.


3.3.0 (Tuesday 22nd September 2020)
-----------------------------------


Added
^^^^^

* New ported versions of various core FSL tools, including ``imrm``, ``imln``,
  ``imtest``, ``fsl_abspath``, ``remove_ext``, ``Text2Vest``, and
  ``Vest2Text``.
* New :func:`.gps` function, wrapping the FSL ``gps`` command.
* New :func:`.vest.loadVestFile` and :func:`.vest.generateVest` functions.


Changed
^^^^^^^


* Updates to the BIDS filetree specification.


Fixed
^^^^^


* The :class:`.CoefficientField` class now works with alternate reference
  images (i.e. a reference image with different dimensions to that which
  was originally used when the non-linear transformation was calculated).


3.2.2 (Thursday 9th July 2020)
------------------------------


Changed
^^^^^^^


* The :func:`.fslsub.func_to_cmd` function allows more fine-grained control
  over whether the script file is removed after the job has finished running.


3.2.1 (Tuesday 23rd June 2020)
------------------------------


Changed
^^^^^^^


* Minor updates to documentation.


3.2.0 (Thursday 11th June 2020)
-------------------------------


Added
^^^^^


* A new :func:`.fslsub.hold` function to wait on previously submitted jobs, to
  be used in place of the ``wait`` function.


Removed
^^^^^^^


* The :func:`.fslsub.wait` (and :func:`.run.wait`) function has been removed, as
  repeated calls to ``qstat`` can adversely affect the cluster job submission
  system.


3.1.0 (Thursday 21st May 2020)
------------------------------


Added
^^^^^


* New :mod:`.cifti` module, providing classes and functions for working with
  `CIFTI <https://www.nitrc.org/projects/cifti/>`_ data.
* New :func:`.winpath` and :func:`wslpath` functions for working with paths
  when using FSL in a Windows Subsystem for Linux (WSL) environment.
* New :func:`.wslcmd` function for generating a path to a FSL command installed
  in a WSL environment.
* New :meth:`.Platform.fslwsl` attribute for detecting whether FSL is installed
  in a WSL environment.
* New :meth:`.Image.niftiDataType` property.
* The :class:`.FileTree` class has been updated to allow creation of
  deep copies via the new :meth:`.FileTree.copy` method.


Changed
^^^^^^^


* :func:`.Image` objects created from ``numpy`` arrays will be NIFTI1 or
  NIFTI2, depending on the value of the ``$FSLOUTPUTTYPE`` environment
  variable.


Fixed
^^^^^


* Updated the :func:`.fast` wrapper to support some single-character
  command-line flags.


3.0.1 (Wednesday 15th April 2020)
---------------------------------


Changed
^^^^^^^


* The :func:`.isMelodicDir` function now accepts directories that do not end
  with ``.ica``, as long as all required files are present.
* Added the ``dataclasses`` backport, so ``fslpy`` is now compatible with
  Python 3.6 again.


3.0.0 (Sunday 29th March 2020)
------------------------------


Added
^^^^^


* New wrapper functions for the FSL :class:`.fslstats`, :func:`.prelude` and
  :func:`applyxfm4D` commands.
* New ``firstDot`` option to the :func:`.path.getExt`,
  :func:`.path.removeExt`, and :func:`.path.splitExt`, functions, offering
  rudimentary support for double-barrelled filenames.
* The :func:`.nonlinear.applyDeformation` function now accepts a ``premat``
  affine, which is applied to the input image before the deformation field.
* New :class:`.SubmitParams` class, providing a higer level interface for
  cluster submission.
* New :meth:`.FileTree.load_json` and  :meth:`.FileTree.save_json` methods.


Changed
^^^^^^^


* ``fslpy`` now requires a minimum Python version of 3.7.
* The default value for the ``partial_fill`` option to :meth:`.FileTree.read`
  has been changed to ``False``. Accordingly, the :class:`.FileTreeQuery`
  calls the :meth:`.FileTree.partial_fill` method on the ``FileTree`` it is
  given.
* The :func:`.gifti.relatedFiles` function now supports files with
  BIDS-style naming conventions.
* The :func:`.run.run` and :func:`.run.runfsl` functions now pass through any
  additional keyword arguments to ``subprocess.Popen`` or, if ``submit=True``,
  to :func:`fslsub.submit`.
* The :func:`.fslsub.submit` function now accepts an ``env`` option, allowing
  environment variables to be specified.
* The :func:`.run.runfsl` function now raises an error on attempts to
  run a command which is not present in ``$FSLDIR/bin/`` (e.g. ``ls``).
* The :mod:`.bids` module has been updated to support files with any
  extension, not just those in the core BIDS specification (``.nii``,
  ``.nii.gz``, ``.json``, ``.tsv``).
* The return value of a function decorated with :func:`.fileOrImage`,
  :func:`.fileOrArray`, or :func:`.fileOrText` is now accessed via an attribute
  called ``stdout``, instead of ``output``.
* Output files of functions decorated with :func:`.fileOrImage`,
  :func:`.fileOrArray`, or :func:`.fileOrText`, which have been loaded via the
  :attr:`.LOAD` symbol, can now be accessed as attributes of the returned
  results object, in addition to being accessed as dict items.
* Wrapper functions decorated with the :func:`.fileOrImage`,
  :func:`.fileOrArray`, or :func:`.fileOrText` decorators will now pass all
  arguments and return values through unchanged if an argument called ``submit``
  is passed in, and is set to ``True`` (or any non-``False``
  value). Furthermore, in such a scenario a :exc:`ValueError` will be raised if
  any in-memory objects or ``LOAD`` symbols are passed.
* The :func:`.fileOrText` decorator has been updated to work with input
  values - file paths must be passed in as ``pathlib.Path`` objects, so they
  can be differentiated from input values.
* Loaded :class:`.Image` objects returned by :mod:`fsl.wrappers` functions
  are now named according to the wrapper function argument name.


Fixed
^^^^^


* Updated the :func:`.prepareArgs` function to use ``shlex.split`` when
  preparing shell command arguments, instead of performing a naive whitespace
  split.
* Fixed some bugs in the :func:`.fslsub.info` and :func:`.fslinfo.wait`
  functions.
* Fixed the :func:`.DeformationField.transform` method so it works with
  a single set of coordinates.
* :class:`.Image` creation does not fail if ``loadMeta`` is set, and a
  sidecar file containing invalid JSON is present.

Removed
^^^^^^^


* Removed the deprecated ``.StatisticAtlas.proportions``,
  ``.StatisticAtlas.coordProportions``, and
  ``.StatisticAtlas.maskProportions`` methods.
* Removed the deprecated ``indexed`` option to :meth:`.Image.__init__`.
* Removed the deprecated ``.Image.resample`` method.
* Removed the deprecated ``.image.loadIndexedImageFile`` function.
* Removed the deprecatd ``.FileTreeQuery.short_names`` and
  ``.Match.short_name`` properties.
* Removed the deprecated ``.idle.inIdle``, ``.idle.cancelIdle``,
  ``.idle.idleReset``, ``.idle.getIdleTimeout``, and
  ``.idle.setIdleTimeout`` functions.
* Removed the deprecated ``resample.calculateMatrix`` function.


2.8.4 (Monday 2nd March 2020)
-----------------------------


Added
^^^^^


* Added a new ``partial_fill`` option to :meth:`.FileTree.read`, which
  effectively eliminates any variables which only have one value. This was
  added to accommodate some behavioural changes that were introduced in 2.8.2.



2.8.3 (Friday 28th February 2020)
---------------------------------


Fixed
^^^^^


* Fixed a bug in the :meth:`.Image.save` method.


2.8.2 (Thursday 27th February 2020)
-----------------------------------


Fixed
^^^^^


* Fixed some subtle bugs in the :func:`.filetree.utils.get_all` function.


2.8.1 (Thursday 20th February 2020)
-----------------------------------


Fixed
^^^^^


* Fixed a bug where an error would be raised on attempts to load an image file
  without a BIDS-compatible name from a BIDS-like directory.


2.8.0 (Wednesday 29th January 2020)
-----------------------------------


Added
^^^^^


* New :meth:`.Nifti.adjust` method, for creating a copy of a :class:`.Nifti`
  header with adjusted shape, pixdims, and affine. This can be useful for
  creating a resampling reference.
* New :func:`.affine.rescale` function, for adjusting a scaling matrix.
* New :func:`.mghimage.voxToSurfMat` function, for creating a
  voxel-to-freesurfer affine transform from any image.


Changed
^^^^^^^


* The :class:`.ImageWrapper` now maintains its own image data cache, rather
  than depending on ``nibabel``.
* Internal changes to avoid using the deprecated
  ``nibabel.dataobj_images.DataobjImage.get_data`` method.


Fixed
^^^^^


* Improved the algorithm used by the :func:`.mesh.needsFixing` function.
* The :meth:`.fslmaths.run` method now accepts :attr:`.wrappers.LOAD` as an
  output specification.
* Fixed a bug in the :class:`.Mesh` class to prevent indices from being loaded
  as floating point type.
* Fixed a bug in the :func:`.resample` function.
* Fixed a bug in the :class:`.MGHImage` class, which was causing pixdims to
  be overridden by scales derived from the affine.


Deprecated
^^^^^^^^^^


* :func:`.calculateMatrix` - its functionality has been moved to the
  :func:`.affine.rescale` function.


2.7.0 (Wednesday 6th November 2019)
-----------------------------------


Added
^^^^^


* New ``until`` option to the :func:`.idle.block` function.
* New :meth:`.Idle.neverQueue` setting, which can be used to force all
  tasks passed to :func:`.idle.idle` to be executed synchronously.
* New :meth:`.IdleLoop.synchronous` context manager, to temporarily change the
  value of :meth:`.IdleLoop.neverQueue`.
* New :mod:`.bids` module, containing a few simple functions for working with
  `BIDS <https://bids.neuroimaging.io>`_ datasets.
* New :func:`.image.loadMetadata` function, and ``loadMeta`` option to the
  :class:`.Image` class, to automatically find and load any sidecar JSON files
  associated with an image file.


Changed
^^^^^^^


* Internal reorganisation in the :mod:`.idle` module.


Fixed
^^^^^


* Fixed incorrect usage of ``setuptools.find_packages``, which was causing
  unit tests to be installed.


Deprecated
^^^^^^^^^^


* :func:`.idle.inIdle` - replaced by :meth:`.IdleLoop.inIdle`.
* :func:`.idle.cancelIdle` - replaced by :meth:`.IdleLoop.cancelIdle`.
* :func:`.idle.idleReser` - replaced by :meth:`.IdleLoop.idleReset`.
* :func:`.idle.getIdleTimeout` - replaced by :meth:`.IdleLoop.callRate`.
* :func:`.idle.setIdleTimeout` - replaced by :meth:`.IdleLoop.callRate`.


2.6.2 (Monday 7th October 2019)
-------------------------------


Changed
^^^^^^^


* Added a debugging hook in the :mod:`.idle` module.
* The :func:`.fslsub.submit` function is now more flexible in the way it
  accepts the command and input arguments.
* The :func:`.run.prepareArgs` function has been renamed (from
  ``_prepareArgs``).


2.6.1 (Thursday 19th September 2019)
------------------------------------


Changed
^^^^^^^


* ``fslpy`` is no longer tested against Python 3.5, and is now tested against
  Python 3.6, 3.7, and 3.8.


2.6.0 (Tuesday 10th September 2019)
-----------------------------------


Added
^^^^^


* New :meth:`.Image.iscomplex` attribute.
* Support for a new ``Statistic`` atlas type.


Changed
^^^^^^^


* The :class:`.Cache` class has a new ``lru`` option, allowing it to be used
  as a least-recently-used cache.
* The :mod:`fsl.utils.filetree` module has been refactored to make it easier
  for the :mod:`.query` module to work with file tree hierarchies.
* The :meth:`.LabelAtlas.get` method has a new ``binary`` flag, allowing
  either a binary mask, or a mask with the original label value, to be
  returned.
* The :mod:`.dicom` module has been updated to work with the latest version of
  ``dcm2niix``.


Deprecated
^^^^^^^^^^


* :meth:`.ProbabilisticAtlas.proportions`,
  :meth:`.ProbabilisticAtlas.maskProportions`, and
  :meth:`.ProbabilisticAtlas.labelProportions` have been deprecated in favour
  of :meth:`.StatisticAtlas.values`, :meth:`.StatisticAtlas.maskValues`, and
  :meth:`.StatisticAtlas.labelValues`


2.5.0 (Tuesday 6th August 2019)
-------------------------------


Added
^^^^^


* New :meth:`.Image.getAffine` method, for retrieving an affine between any of
  the voxel, FSL, or world coordinate systems.
* New :mod:`fsl.transforms` package, which contains classes and functions for
  working with linear and non-linear FLIRT and FNIRT transformations.
* New static methods :meth:`.Nifti.determineShape`,
  :meth:`.Nifti.determineAffine`, :meth:`.Nifti.generateAffines`, and
  :meth:`.Nifti.identifyAffine`.
* New prototype :mod:`fsl.transforms.x5`  module, for reading/writing linear
  and non-linear X5 files (*preliminary release, subject to change*).
* New prototype :mod:`.fsl_convert_x5` :mod:`.fsl_apply_x5` programs, for
  working with X5 transformations (*preliminary release, subject to change*).



Changed
^^^^^^^


* The :mod:`.vest.looksLikeVestLutFile` function has been made slightly more
  lenient.
* `h5py <https://www.h5py.org/>`_ has been added to the ``fslpy`` dependencies.


Deprecated
^^^^^^^^^^


* The :mod:`fsl.utils.transform` module has been deprecated; its functions can
  now be found in the :mod:`fsl.transforms.affine` and
  :mod:`fsl.transform.flirt` modules.


2.4.0 (Wednesday July 24th 2019)
--------------------------------


Added
^^^^^


* New :mod:`.image.roi` module, for extracting an ROI of an image, or expanding
  its field-of-view.


Changed
^^^^^^^


* The :mod:`.resample_image` script has been updated to support resampling of
  images with more than 3 dimensions.


2.3.1 (Friday July 5th 2019)
----------------------------


Fixed
^^^^^


* The :class:`.Bitmap` class now supports greyscale images and palette images.


2.3.0 (Tuesday June 25th 2019)
------------------------------


Added
^^^^^


* New :class:`.Bitmap` class, for loading bitmap images. The
  :meth:`.Bitmap.asImage` method can be used to convert a ``Bitmap`` into
  an :class:`.Image`.
* The :class:`.Image` class now has support for the ``RGB24`` and ``RGBA32``
  NIfTI data types.
* New :attr:`.Image.nvals` property, for use with ``RGB24``/``RGBA32``
  images.
* New :meth:`.LabelAtlas.get` and :meth:`ProbabilisticAtlas.get` methods,
  which return an :class:`.Image` for a specific region.
* The :meth:`.AtlasDescription.find` method also now a ``name`` parameter,
  allowing labels to be looked up by name.
* New :meth:`.FileTree.defines` and :meth:`.FileTree.on_disk` methods, to
  replace the :func:`.FileTree.exists` method.


Fixed
^^^^^


* The :func:`.makeWriteable` function will always create a copy of an
  ``array`` if its base is a ``bytes`` object.
* Fixed a bug in the :meth:`.GitfitMesh.loadVertices` method.
* Fixed a bug in the :meth:`.Mesh.addVertices` method where the wrong face
  normals could be used for newly added vertex sets.


2.2.0 (Wednesday May 8th 2019)
------------------------------


Added
^^^^^


* New :mod:`.resample_image` script.
* New :mod:`.resample` module (replacing the :func:`.Image.resample` method),
  containing functions to resample an :class:`.Image`.
* New :func:`.resample.resampleToPixdim` and
  :func:`.resample.resampleToReference` functions, convenience wrappers around
  :func:`.resample.resample`.
* New :func:`.idle.block` function.


Changed
^^^^^^^


* The :func:`.resample` function (formerly :meth:`.Image.resample`) now
  accepts ``origin`` and ``matrix`` parameters, which can be used to adjust
  the alignment of the voxel grids of the input and output images.
* The :func:`.transform.decompose` function now accepts both ``(3, 3)``
  and ``(4, 4)`` matrices.


Fixed
^^^^^


* Minor fixes to some :mod:`.filetree.filetree` tree definitions.


Deprecated
^^^^^^^^^^


* The :meth:`.Image.resample` method has been deprecated in favour of the
  :func:`.resample.resample` function.


2.1.0 (Saturday April 13th 2019)
--------------------------------


Added
^^^^^


* New tensor conversion routines in the :mod:`.dtifit` module (Michiel
  Cottaar).
* New :func:`.makeWriteable` function which ensures that a ``numpy.array`` is
  writeable, and creates a copy if necessary


Changed
^^^^^^^


* The :class:`.GiftiMesh` class no longer creates copies of the mesh
  vertex/index arrays. This means that, these arrays will be flagged as
  read-only.
* The :class:`.Mesh` class handles vertex data sets requiring different
  triangle unwinding orders, at the cost of potentially having to store
  two copies of the mesh indices.


Fixed
^^^^^


* The :class:`.FeatDesign` class now handles "compressed" voxelwise EV files,
  such as those generated by `PNM
  <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/PNM>`_.


2.0.1 (Monday April 1st 2019)
-----------------------------


Fixed
^^^^^


* Fixed a bug with the :func:`.gifti.relatedFiles` function returning
  duplicate files.


2.0.0 (Friday March 20th 2019)
------------------------------


Added
^^^^^

* New :mod:`fsl.utils.filetree` package for defining and working with
  file/directory templates (Michiel Cottaar).
* Simple built-in :mod:`.deprecated` decorator.
* New :mod:`fsl.data.utils` module, which currently contains one function
  :func:`.guessType`, which guesses the data type of a file/directory path.
* New :func:`.commonBase` function for finding the common prefix of a set of
  file/directory paths.


Changed
^^^^^^^


* Removed support for Python 2.7 and 3.4.
* Minimum required version of ``nibabel`` is now 2.3.
* The :class:`.Image` class now fully delegates to ``nibabel`` for managing
  file handles.
* The :class:`.GiftiMesh` class can now load surface files which contain
  vertex data, and will accept surface files which end in ``.gii``, rather
  than requiring files which end in ``.surf.gii``.
* The ``name`` property of :class:`.Mesh` instances can now be updated.


Removed
^^^^^^^

* Many deprecated items removed.


Deprecated
^^^^^^^^^^


* Deprecated the :func:`.loadIndexedImageFile`  function, and the ``indexed``
  flag to the :class:`.Image` constructor.


1.13.3 (Friday February 8th 2019)
---------------------------------


Fixed
^^^^^


* Fixed an issue with the :func:`.dicom.loadSeries` using memory-mapping for
  image files that would subsequently be deleted.
* Fixed an issue in the :class:`.GiftiMesh` class, where
  ``numpy``/``nibabel`` was returning read-only index arrays.


1.13.2 (Friday November 30th 2018)
----------------------------------


Changed
^^^^^^^


* The :meth:`.Image.resample` method now supports images with more than three
  dimensions.
* The :func:`fsl.utils.fslsub.submit` now returns the job-id as a string
  rather than a one-element tuple. It now also accepts a nested sequence
  of job ids rather than just a flat sequence. This will also changes the
  output from the function wrappers in :mod:`fsl.wrappers` if submitted.


Fixed
^^^^^


* Fix to the :class:`.ImageWrapper` regarding complex data types.


1.13.1 (Friday November 23rd 2018)
----------------------------------


Fixed
^^^^^


* Added a missing ``image`` attribute in the :class:`.VoxelwiseConfoundEV`
  class.
* Make sure that FEAT ``Cluster`` objects (created by the
  :func:`.loadClusterResults` function) contain ``p`` and ``logp`` attributes,
  even when cluster thresholding was not used.


1.13.0 (Thursday 22nd November 2018)
------------------------------------


Added
^^^^^

* New wrapper functions for :func:`.fsl_anat`, :func:`.applytopup` (Martin
  Craig).
* New :func:`.fileOrText` decorator for use in wrapper functions (Martin
  Craig).


Changed
^^^^^^^

* Various minor changes and enhancements to the FSL function :mod:`.wrappers`
  interfaces (Martin Craig).


Fixed
^^^^^

* The ``immv`` and ``imcp`` scripts now accept incorrect file extensions on
  input arguments.


1.12.0 (Sunday October 21st 2018)
---------------------------------


Changed
^^^^^^^


* The ``extract_noise`` script has been renamed to :mod:`.fsl_ents`.
* Increased the minimum required version of ``dcm2niix`` in the
  :mod:`fsl.data.dicom` module.


Deprecated
^^^^^^^^^^


* The ``extract_noise`` script.


1.11.1 (Friday September 14th 2018
----------------------------------


Fixed
^^^^^


* Fixed a Python 2 incompatibility in the :mod:`.settings` module.


1.11.0 (Thursday September 13th 2018)
-------------------------------------


Added
^^^^^


* A couple of new convenience functions to the :mod:`.settings` module.


Changed
^^^^^^^


* Development (test and documentation dependencies) are no longer listed
  in ``setup.py`` - they now need to be installed manually.
* Removed conda build infrastructure.


1.10.3 (Sunday September 9th 2018)
----------------------------------


Added
^^^^^


* The :func:`.parseVersionString` function accepts (and ignores) `local
  version identifer
  <https://www.python.org/dev/peps/pep-0440/#local-version-identifiers>`_
  strings.


1.10.2 (Friday September 7th 2018)
----------------------------------


Fixed
^^^^^


* The :meth:`.Image.save` method was not handling memory-mapped images
  correctly.


1.10.1 (Friday August 3rd 2018)
-------------------------------


Changed
^^^^^^^


* Minor adjustmenets to improve Windows compatibility.


Fixed
^^^^^

* The :mod:`.FEATImage.getCOPE` method was returning PE images.


1.10.0 (Wednesday July 18th 2018)
---------------------------------


Added
^^^^^


* A new script, :mod:`.extract_noise`, which can be used to extract ICA
  component time courses from a MELODIC ICA analysis.
* New :func:`.path.allFiles` function which returns all files underneath a
  directory.
* The :func:`.fileOrImage` and :func:`.fileOrArray` decorators now support
  loading of files which are specified with an output basename.
* New :mod:`.fast` wrapper function for the FSL FAST tool.


Changed
^^^^^^^


* When using the :func:`.run.run` function, the command output/error streams
  are now forwarded immediately.
* Removed dependency on ``pytest-runner``.


1.9.0 (Monday June 4th 2018)
----------------------------


Added
^^^^^


* New :meth:`.Image.data` property method, for easy access to image data
  as a ``numpy`` array.
* New ``log`` option to the :func:`.run.run` function, allowing more
  fine-grained control over sub-process output streams.
* New :meth:`.Platform.fsldevdir` property, allowing the ``$FSLDEVDIR``
  environment variable to be queried/changed.


Changed
^^^^^^^


* :meth:`.Image.ndims` has been renamed to :meth:`.Image.ndim`, to align
  more closely with ``numpy`` naming conventions.
* The ``err`` and ``ret`` parameters to the :func:`.run.run` function have
  been renamed to ``stderr`` and ``exitcode`` respectively.
* The :func:`.runfsl` function will give priority to the ``$FSLDEVDIR``
  environment variable if it is set.


Deprecated
^^^^^^^^^^


* :meth:`.Image.ndims`.
* The ``err`` and ``ret`` parameters to :func:`.run.run`.


1.8.1 (Friday May 11th 2018)
----------------------------


Changed
^^^^^^^


* The :func:`.fileOrImage` decorator function now accepts :class:`.Image`
  objects as well as ``nibabel`` image objects.


1.8.0 (Thursday May 3rd 2018)
-----------------------------


Added
^^^^^


* New :mod:`.wrappers` package, containing wrapper functions for a range of
  FSL tools.
* New :mod:`fsl.utils.run` module, to replace the :mod:`fsl.utils.callfsl`
  module.
* New :mod:`fsl.utils.fslsub` module, containing a :func:`.fslsub.submit`
  function which submits a cluster job via ``fsl_sub``.
* Assertions (in the :mod:`.assertions` module) can be disabled with the
  new :func:`.assertions.disabled` context manager.
* New :mod:`fsl.utils.parse_data` module containing various neuroimaging
  data constructors for use with ``argparse``.
* The :func:`.memoize.skipUnchanged` decorator has an ``invalidate`` function
  which allows its cache to be cleared.


Changed
^^^^^^^


* The :func:`.tempdir` function has an option to not change to the newly
  created directory.


Deprecated
^^^^^^^^^^


* The :mod:`fsl.utils.callfsl` module (replaced with :mod:`fsl.utils.run`).


1.7.2 (Monday March 19th 2018)
------------------------------


Added
^^^^^


* Added the :meth:`.MGHImage.voxToSurfMat` and related properties, giving
  access to the voxel-to-surface affine for an MGH image.


1.7.1 (Monday March 12th 2018)
------------------------------



Changed
^^^^^^^


* Adjusted :func:`.parseVersionString` so it accepts ``.dev*`` suffixes.


Fixed
^^^^^


* Removed deprecated use of :func:`.imagewrapper.canonicalShape`.


1.7.0 (Tuesday March 6th 2018)
------------------------------


Added
^^^^^


* The :mod:`fsl.utils.assertions` module contains a range of functions
  which can be used to assert that some condition is met.
* The :mod:`fsl.utils.ensure` module contains a range of functions (currently
  just one) which can be used to ensure that some condiution is met.


Changed
^^^^^^^


* The :mod:`.settings` module now saves its files in a format that is
  compatible with Python 2 and 3.
* The :func:`.tempdir` function now accepts a ``root`` argument, which
  specifies the location in which the temporary directory should be created.
* An image's data source can now be set via  :meth:`.Image.__init__`.
* :meth:`.MGHImage` objects now have a :meth:`.MGHImage.save` method.
* Adjustments to the ``conda`` package build and deployment process.
* The :func:`.ImageWrapper.canonicalShape` function has been moved
  to the :mod:`.data.image` class.
* The :func:`.ImageWrapper.naninfrange` function has been moved
  into its own :mod:`.naninfrange` module.


Fixed
^^^^^


* Fixed a bug in the :class:`.MutexFactory` class.


Deprecated
^^^^^^^^^^


* :func:`.ImageWrapper.canonicalShape` (moved to the :mod:`.data.image` module)
* :func:`.ImageWrapper.naninfrange` function (moved to the :mod:`.naninfrange`
  module)


1.6.8 (Monday February 12th 2018)
---------------------------------


* The `atlasq`, `immv`, `imcp` and `imglob` scripts suppress some warnings.


1.6.7 (Friday February 9th 2018)
--------------------------------


* More further adjustments to the ``conda`` package build.
* Adjustments to pypi source distribution - the ``requirements-extra.txt`` file
  was not being included.


1.6.6 (Thursday February 8th 2018)
----------------------------------


* Further adjustments to the ``conda`` package build.


1.6.5 (Tuesday February 6th 2018)
---------------------------------


* Adjustments to the ``conda`` package build.


1.6.4 (Monday February 5th 2018)
--------------------------------


* The :mod:`.platform` module emits a warning if it cannot import ``wx``.


1.6.3 (Friday February 2nd 2018)
--------------------------------


* Minor enhancements to the :class:`.WeakFunctionRef` class.
* Some bugfixes to the :mod:`fsl.utils.imcp` module, with respect to handling
  relative path names, moving file groups (e.g. `.img`/`.hdr` pairs), and
  non-existent directories.


1.6.2 (Tuesday January 30th 2018)
---------------------------------


* Updates to the ``conda`` installation process.
* A new script is installed when ``fslpy`` is installed via ``pip`` or
  ``conda`` - ``atlasquery``, which emulates the FSL ``atlasquery`` tool.


1.6.1 (Monday January 29th 2018)
--------------------------------


* Removed ``lxml`` as a dependency - this was necessary in older versions of
  ``trimesh``.


1.6.0 (Friday January 26th 2018)
--------------------------------


* The new :class:`.Mesh` class is now the base class for all mesh types. It
  has been written to allow multiple sets of vertices to be associated with a
  mesh object (to support e.g. white matter, inflated, spherical models for a
  GIFTI/freeusrfer mesh).
* The new :class:`.VTKMesh` class must now be used for loading VTK model files,
  instead of the old :class:`.TriangleMesh` class.
* The new :class:`.Mesh` class uses the ``trimesh`` library
  (https://github.com/mikedh/trimesh) to perform various geometrical
  operations, accessible via new :meth:`.Mesh.rayIntersection`,
  :meth:`.Mesh.planeIntersection`, :meth:`.Mesh.nearestVertex` methods.
* The :class:`.Nifti` and :class:`.Mesh` classes have new methods allowing
  arbitrary metadata to be stored with the image, as key-value
  pairs. These are provided by a new mixin class, :class:`.Meta`.
* Freesurer surface files and vertex data can now be loaded via the
  :class:`.FreesurferMesh` class, in the new :mod:`.freesurfer` module.
* Freesurfer ``mgz`` / ``mgh`` image files can now be loaded via the new
  :mod:`.mghimage` module. Internally, these image files are converted to NIFTI
  - the :class:`.MGHImage` class derives from the :class:`.Image` class.
* Meta-data access methods on the :class:`.DicomImage` class have been
  deprecated, as their functionality is provided by the new :class:`.Meta`
  mixin.
* The :class:`.TriangleMesh` class has been deprecated in favour of the new
  :class:`.Mesh` class.
* Optional dependencies ``wxpython``, ``indexed_gzip``, ``trimesh``, and
  ``rtree`` are now listed separately, so ``fslpy`` can be used without them
  (although relevant functionality will be disabled if they are not present).


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
