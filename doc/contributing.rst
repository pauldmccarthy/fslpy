Contributing to fslpy
=====================


*This document is a work in progress*


Development model
-----------------


 - The master branch should always be stable and ready to release. All
   development occurs on the master branch.

 - All changes to the master branch occur via merge requests. Individual
   developers are free to choose their own development workflow in their own
   repositories.

 - A separate branch is created for each release. Hotfixes may be added to
   these release branches.

 - Merge requests will not be accepted unless:
   
     - All existing tests pass (or have been updated as needed).
     - New tests have been written to cover newly added features.
     - Code coverage is as close to 100% as possible.
     - Coding conventions are adhered to (unless there is good reason not to).


Version number
--------------


The `fslpy` version number follows [semantic versioning](http://semver.org/)
rules, so that dependant projects are able to perform compatibility testing.
The version number comprises three numbers::

    major.minor.patch

 - The `patch` number is incremented on bugfixes and minor
   (backwards-compatible) changes.
   
 - The `minor` number is incremented on feature additions and major
   backwards-compatible changes.

 - The `major` number is incremented on backwards-incompatible changes.


Testing
-------


Unit and integration tests are currently run with `py.test` and `coverage`. We
don't have CI configured yet, so tests have to be run manually.

 - Aim for 100% code coverage.
 - Tests must pass on both python 2.7 and 3.5
 - Tests must pass on both wxPython 3.0.2.0 and 4.0.0


Coding conventions
------------------


 - Clean, readable code is good
 - White space and visual alignment is good (where it helps to make the code
   more readable)
 - Clear and accurate documentation is good


Configure your text editor to use [pylint](https://www.pylint.org/) and
[flake8](http://flake8.pycqa.org/en/latest/).

The following violations of the PEP8 standard are accepted (see
[here](https://pycodestyle.readthedocs.io/en/latest/intro.html#error-codes)
for a list of error codes):

 - E127: continuation line over-indented for visual indent
 - E201: whitespace after '('
 - E203: whitespace before ':'
 - E221: multiple spaces before operator
 - E222: multiple spaces after operator
 - E241: multiple spaces after ','
 - E271: multiple spaces after keyword
 - E272: multiple spaces before keyword
 - E301: expected 1 blank line, found 0
 - E302: expected 2 blank lines, found 0
 - E303: too many blank lines (3)
 - E701: multiple statements on one line (colon)
