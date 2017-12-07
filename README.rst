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


Dependencies
------------


All of the dependencies of ``fslpy`` are listed in the `requirements.txt
<requirements.txt>`_ file. Some ``fslpy`` modules require `wxPython
<http://www.wxpython.org>`_ 3.0.2.0 or higher.


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

The `fsl.data.dcmstack <fsleyes/dcmstack/>`_ package contains a copy of
Brendan Moloney's `dcmstack
<https://github.com/moloney/dcmstack/tree/c12d27d2c802d75a33ad70110124500a83e851ee>`_
project (version 0.7.0.dev), with python 2-to-3 fixes made by `Ghislain Antony
Vaillant
<https://github.com/ghisvail/dcmstack/tree/1a1573b3869a0920953f64d3d0b99e4ecb1a4c81>`_.
