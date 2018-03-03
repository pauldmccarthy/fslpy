#!/usr/bin/env python
#
# __init__.py - Wrappers for FSL command-line tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains wrappers for various FSL command line tools, allowing
them to be called from Python.


Most of these wrapper functions strive to provide as-close an interface to the
command-line tool as possible. Most functions use positional arguments for
required options, and keyword arguments for all other options, with argument
names equivalent to command line option names.


For options where this is not possible (e.g. ``flirt -2D``),an alias is used
instead. Aliases may also be used to provide a more readable interface (e.g.
the :func:`.bet` function uses ``mask`` instead of ``m``).


Wrapper functions for commands which accept NIfTI image or numeric text files
will for the most part accept either in-memory ``nibabel`` images/Numpy arrays
or file names as inputs. For commands which produce image or numeric text file
outputs, the special :data:`.LOAD` value can be used to indicate that the file
should be loaded and returned in-memory from the wrapper function. For example,
if we want to FLIRT two images and get the result, we can do this::

    import nibabel as nib
    from fsl.wrappers import flirt, LOAD

    src     = nib.load('src.nii')
    ref     = nib.load('ref.nii')
    aligned = flirt(src, ref, out=LOAD)['out']


If you are writing wrapper functions, read through the :mod:`.wrapperutils`
module - it contains several useful functions and decorators.
"""


from .wrapperutils import (LOAD,)           # noqa
from .bet          import (bet,             # noqa
                           robustfov)
from .eddy         import (eddy_cuda,       # noqa
                           topup)
from .flirt        import (flirt,           # noqa
                           invxfm,
                           applyxfm,
                           concatxfm,
                           mcflirt)
from .fnirt        import (fnirt,           # noqa
                           applywarp,
                           invwarp,
                           convertwarp)
from .fslmaths     import (fslmaths,)       # noqa
from .fugue        import (fugue,           # noqa
                           sigloss)
from .melodic      import (melodic,         # noqa
                           fsl_regfilt)
from .misc         import (fslreorient2std, # noqa
                           fslroi,
                           slicer,
                           cluster)
