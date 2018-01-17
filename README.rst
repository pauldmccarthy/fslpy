fslpy
=====


.. image:: https://git.fmrib.ox.ac.uk/fsl/fslpy/badges/master/build.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fslpy/commits/master/

.. image:: https://git.fmrib.ox.ac.uk/fsl/fslpy/badges/master/coverage.svg
   :target: https://git.fmrib.ox.ac.uk/fsl/fslpy/commits/master/

.. image:: https://img.shields.io/pypi/v/fslpy.svg
   :target: https://pypi.python.org/pypi/fslpy/


The ``fslpy`` project is a `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_
programming library written in Python. It is used by `FSLeyes
<https://git.fmrib.ox.ac.uk/fsl/fsleyes/fsleyes/>`_.


Installation
------------


Install ``fslpy`` and its core dependencies via pip::

    pip install fslpy


Dependencies
------------


All of the core dependencies of ``fslpy`` are listed in the `requirements.txt
<requirements.txt>`_ file.

Some extra dependencies are listed in `requirements.txt
<requirements-extra.txt>`_ which provide addditional functionality:

 - ``wxPython``: The `fsl.utils.idle <fsl/utils/idle.py>`_ module has
   functionality  to schedule functions on the ``wx`` idle loop.

 - ``indexed_gzip``: The `fsl.data.image.Image <fsl/data/image.py>`_ class
   can use ``indexed_gzip`` to keep large compressed images on disk instead
   of decompressing and loading them into memory..

 - ``trimesh``/``rtree``: The `fsl.data.mesh.TriangleMesh <fsl/data/mesh.py>`_
   class has some methods which use ``trimesh`` to perform geometric queries
   on the mesh.



To install these additional dependencies, you first need to install wxPython,
which is still in pre-relaes.

 - **macOS**: ``pip install --pre wxPython``
 - **Linux** (change the URL for your specific platform): ``pip install --only-binary wxpython -f https://extras.wxpython.org/wxPython4/extras/linux/gtk2/ubuntu-16.04/ wxpython``


The ``rtree`` library also assumes that ``libspatialindex`` is installed on
your system.


Once wxPython has been installed, you can simply type the following to install
the rest of the extra dependencies::

    pip install fslpy[extras]


Documentation
-------------

``fslpy`` is documented using `sphinx <http://http://sphinx-doc.org/>`_. You
can build the API documentation by running::

    python setup.py doc

The HTML documentation will be generated and saved in the ``doc/html/``
directory.


If you are interested in contributing to ``fslpy``, check out the
`contributing guide <doc/contributing.rst>`_.


Tests
-----

Run the test suite via::

    python setup.py test

A test report will be generated at ``report.html``, and a code coverage report
will be generated in ``htmlcov/``.


Credits
-------


The `fsl.data.dicom <fsl/data/dicom/>`_ module is little more than a thin
wrapper around Chris Rorden's `dcm2niix
<https://github.com/rordenlab/dcm2niix>`_ program.


The `example.mgz <tests/testdata/example.mgz>`_ file, used for testing,
originates from the ``nibabel`` test data set.
