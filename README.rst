fslpy
=====

.. image:: https://img.shields.io/pypi/v/fslpy.svg
   :target: https://pypi.python.org/pypi/fslpy/

.. image:: https://anaconda.org/conda-forge/fslpy/badges/version.svg
   :target: https://anaconda.org/conda-forge/fslpy

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.1470750.svg
   :target: https://doi.org/10.5281/zenodo.1470750

.. image:: https://git.fmrib.ox.ac.uk/fsl/fslpy/badges/master/coverage.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fslpy/commits/master/


The ``fslpy`` project is a `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_
programming library written in Python. It is used by `FSLeyes
<https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/>`_.


``fslpy`` is tested against Python versions 3.7, 3.8 and 3.9.


Installation
------------


Install ``fslpy`` and its core dependencies via pip::

    pip install fslpy


``fslpy`` is also available on `conda-forge <https://conda-forge.org/>`_::

    conda install -c conda-forge fslpy


Dependencies
------------


All of the core dependencies of ``fslpy`` are listed in the
`requirements.txt <requirements.txt>`_ file.

Some extra dependencies are listed in
`requirements-extra.txt <requirements-extra.txt>`_
which provide addditional functionality:

- ``wxPython``: The `fsl.utils.idle <fsl/utils/idle.py>`_ module has
  functionality  to schedule functions on the ``wx`` idle loop.

- ``indexed_gzip``: The `fsl.data.image.Image <fsl/data/image.py>`_ class
  can use ``indexed_gzip`` to keep large compressed images on disk instead
  of decompressing and loading them into memory..

- ``trimesh``/``rtree``: The `fsl.data.mesh.TriangleMesh <fsl/data/mesh.py>`_
  class has some methods which use ``trimesh`` to perform geometric queries
  on the mesh.

- ``Pillow``: The `fsl.data.bitmap.Bitmap <fsl/data/bitmap.py>`_ class uses
  ``Pillow`` to load image files.


If you are using Linux, you need to install wxPython first, as binaries are
not available on PyPI. Install wxPython like so, changing the URL for your
specific platform::

    pip install -f https://extras.wxpython.org/wxPython4/extras/linux/gtk2/ubuntu-16.04/ wxpython


Once wxPython has been installed, you can type the following to install the
rest of the extra dependencies::

    pip install fslpy[extras]


Dependencies for testing and documentation are listed in the
`requirements-dev.txt <requirements-dev.txt>`_ file.


Non-Python dependencies
^^^^^^^^^^^^^^^^^^^^^^^


The `fsl.data.dicom <fsl/data/dicom.py>`_ module requires the presence of
Chris Rorden's `dcm2niix <https://github.com/rordenlab/dcm2niix>`_ program.


The ``rtree`` library assumes that ``libspatialindex`` is installed on
your system.


The `fsl.transform.x5 <fsl/transform/x5.py>`_ module uses `h5py
<https://www.h5py.org/>`_, which requires ``libhdf5``.


Documentation
-------------

``fslpy`` is documented using `sphinx <http://http://sphinx-doc.org/>`_. You
can build the API documentation by running::

    pip install -r requirements-dev.txt
    python setup.py doc

The HTML documentation will be generated and saved in the ``doc/html/``
directory.


Tests
-----

Run the test suite via::

    pip install -r requirements-dev.txt
    python setup.py test

A test report will be generated at ``report.html``, and a code coverage report
will be generated in ``htmlcov/``.


Contributing
------------


If you are interested in contributing to ``fslpy``, check out the
`contributing guide <doc/contributing.rst>`_.


Credits
-------


The `fsl.data.dicom <fsl/data/dicom.py>`_ module is little more than a thin
wrapper around Chris Rorden's `dcm2niix
<https://github.com/rordenlab/dcm2niix>`_ program.


The `example.mgz <tests/testdata/example.mgz>`_ file, used for testing,
originates from the ``nibabel`` test data set.
