
``fslpy``
=========


The ``fslpy`` package is a collection of utilities and data abstractions used
within `FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki>`_ and by
|fsleyes_apidoc|_.


The top-level Python package for ``fslpy`` is called :mod:`fsl`.  It is
broadly split into the following sub-packages:

+----------------------+-----------------------------------------------------+
| :mod:`fsl.data`      | contains data abstractions and I/O routines for a   |
|                      | range of FSL and neuroimaging file types. Most I/O  |
|                      | routines use `nibabel <https://nipy.org/nibabel/>`_ |
|                      | extensively.                                        |
+----------------------+-----------------------------------------------------+
| :mod:`fsl.utils`     | contains a range of miscellaneous utilities,        |
|                      | including :mod:`fsl.utils.path`,                    |
|                      | :mod:`fsl.utils.run`, and :mod:`fsl.utils.bids`     |
+----------------------+-----------------------------------------------------+
| :mod:`fsl.scripts`   | contains a range of scripts which are installed as  |
|                      | FSL commands.                                       |
+----------------------+-----------------------------------------------------+
| :mod:`fsl.transform` | contains functions and classes for working with     |
|                      | FSL-style linear and non-linear transformations.    |
+----------------------+-----------------------------------------------------+
| :mod:`fsl.version`   | simply contains the ``fslpy`` version number.       |
+----------------------+-----------------------------------------------------+
| :mod:`fsl.wrappers`  | contains Python functions which can be used to      |
|                      | invoke FSL commands.                                |
+----------------------+-----------------------------------------------------+

The :mod:`fsl` package provides the top-level Python package namespace for
``fslpy``, and for other FSL python libaries. It is a `native namespace
package <https://packaging.python.org/guides/packaging-namespace-packages/>`_,
which means that there is no ``fsl/__init__.py`` file.


Other libraries can use the ``fsl`` package namepace simply by also omitting a
``fsl/__init__.py`` file, and by ensuring that there are no naming conflicts
with any sub-packages of ``fslpy`` or any other projects which use the ``fsl``
package namespace.



.. toctree::
   :hidden:

   self
   fsl.data
   fsl.scripts
   fsl.transform
   fsl.utils
   fsl.wrappers
   fsl.version
   contributing
   changelog
