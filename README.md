fslpy
=====


The `fslpy` project is a [FSL](http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/)
programming library written in Python. It is used by
[FSLeyes](https://git.fmrib.ox.ac.uk/paulmc/fsleyes/).


Dependencies
------------


All of the dependencies of `fslpy` are listed in the
[requirements.txt](requirements.txt) file. Some `fslpy` modules require
[wxPython](http://www.wxpython.org) 3.0.2.0.


Documentation
-------------

`fslpy` is documented using [sphinx](http://http://sphinx-doc.org/). You can
build the API documentation by running:

    python setup.py doc

The HTML documentation will be generated and saved in the `doc/html/` directory.


If you are interested in contributing to `fslpy`, check out the [contributing
guide](doc/contributing.rst).


Tests
-----

Run the test suite via:

    python setup.py test

A test report will be generated at `report.html`, and a code coverage report
will be generated in `htmlcov/`.
