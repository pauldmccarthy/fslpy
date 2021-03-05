
``fslpy``
=========


The ``fslpy`` package is a collection of utilities and data abstractions used
within `FSL <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki>`_ and by
|fsleyes_apidoc|_.


The top-level Python package for ``fslpy`` is called :mod:`fsl`.  It is
broadly split into the following sub-packages:


.. autosummary::

   fsl.data
   fsl.utils
   fsl.scripts
   fsl.transform
   fsl.version
   fsl.wrappers


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
   contributing
   changelog
