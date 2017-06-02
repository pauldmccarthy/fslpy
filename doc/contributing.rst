Contributing to ``fslpy``
=========================


*This document is a work in progress*


Development model
-----------------


- The master branch should always be stable and ready to release. All
  development occurs on the master branch.

- All changes to the master branch occur via merge requests. Individual
  developers are free to choose their own development workflow in their own
  repositories.

- Merge requests will not be accepted unless:

 - All existing tests pass (or have been updated as needed).
 - New tests have been written to cover newly added features.
 - Code coverage is as close to 100% as possible.
 - Coding conventions are adhered to (unless there is good reason not to).


Version number
--------------


The ``fslpy`` version number roughly follows `semantic versioning
<http://semver.org/>`_ rules, so that dependant projects are able to perform
compatibility testing.  The full version number string consists of three
numbers::

    major.minor.patch

- The ``patch`` number is incremented on bugfixes and minor
  (backwards-compatible) changes.

- The ``minor`` number is incremented on feature additions and/or
  backwards-compatible changes.

- The ``major`` number is incremented on major feature additions, and
  backwards-incompatible changes.


Releases
--------


A separate branch is created for each **minor** release. The name of the
branch is ``v[major.minor]``, where ``[major.minor]`` is the first two
components of the release version number (see below). For example, the branch
name for minor release ``1.0`` would be ``v1.0``.


Patches and hotfixes may be added to these release branches. These should be
merged into the master branch, and then cherry-picked onto the release
branch(es).


Every release is also tagged with its full version number.  For example, the
first release off the ``v1.0`` branch would be tagged with ``1.0.0``.
Maintenance release to the ``v1.0`` branch would be tagged with ``1.0.1``,
``1.0.2``, etc.


Testing
-------


Unit and integration tests are currently run with ``py.test`` and
``coverage``. We don't have CI configured yet, so tests have to be run
manually.

- Aim for 100% code coverage.
- Tests must pass on both python 2.7 and 3.5
- Tests must pass on both wxPython 3.0.2.0 and 4.0.0


Coding conventions
------------------


- Clean, readable code is good
- White space and visual alignment is good (where it helps to make the code
  more readable)
- Clear and accurate documentation is good
- Document all modules, functions, classes, and methods using
  `ReStructuredText <http://www.sphinx-doc.org/en/stable/rest.html>`_.


Configure your text editor to use:

- `flake8 <http://flake8.pycqa.org/en/latest/>`_: This checks your code for
  adherence to the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ coding
  standard.

- `pylint <https://www.pylint.org/>`_: This checks that your code follows
  other good conventions.


Because I like whitespace and vertical alignment more than PEP8 does, the
following violations of the PEP8 standard are accepted (see
`here <https://pycodestyle.readthedocs.io/en/latest/intro.html#error-codes>`_
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
