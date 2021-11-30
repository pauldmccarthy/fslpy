#!/usr/bin/env python
#
# pylint: disable=unused-import
# flake8: noqa: F401
#
# __init__.py - Wrappers for FSL command-line tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains wrappers for various FSL command line tools, allowing
them to be called from Python.


For example, you can call BET like so::

    from fsl.wrappers import bet
    bet('struct', 'struct_brain')

If you would like a command to be submitted as a cluster job, all wrappers
accept a ``submit`` keyword argument, which may be given a value of ``True``
indicating that the job should be submitted with default settings, or a
dictionary with submission settings::

    from fsl.wrappers import fnirt
    fnirt('srf', 'ref', 'out', submit=True)
    fnirt('srf', 'ref', 'out', submit={'queue' : 'long.q', 'ram' : '4GB'})


See the :mod:`.fslsub` module for more details.


Most of these wrapper functions strive to provide an interface which is as
close as possible to the underlying command-line tool. Most functions use
positional arguments for required options, and keyword arguments for all other
options, with argument names equivalent to command line option names.


For options where this is not possible (e.g. ``flirt -2D``),an alias is used
instead. Aliases may also be used to provide a more readable interface (e.g.
the :func:`.bet` function uses ``mask`` instead of ``m``).


Two exceptions to the above are :class:`.fslmaths` and :class:`.fslstats`,
which provide a more object-oriented interface::

    from fsl.wrappers import fslmaths, fslstats

    fslmaths('image.nii').mas('mask.nii').bin().run('output.nii')

    imean, imin, imax = fslstats('image.nii').k('mask.nii').m.R.run()


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
    init    = np.eye(4)
    aligned = flirt(src, ref, init=init, out=LOAD)['out']


Similarly, we can run a ``fslmaths`` command on in-memory images::

    import nibabel as nib
    from fsl.wrappers import fslmaths

    image  = nib.load('image.nii')
    mask   = nib.load('mask.nii')
    output = fslmaths(image).mas(mask).bin().run()


If you are *writing* wrapper functions, take a look at the
:mod:`.wrapperutils` module - it contains several useful functions and
decorators.
"""


from fsl.wrappers.wrapperutils import (LOAD,)
from fsl.wrappers.bet          import (bet,
                                       robustfov)
from fsl.wrappers.eddy         import (eddy_cuda,
                                       topup,
                                       applytopup)
from fsl.wrappers.fast         import (fast,)
from fsl.wrappers.fsl_anat     import (fsl_anat,)
from fsl.wrappers.fsl_sub      import (fsl_sub,)
from fsl.wrappers.flirt        import (flirt,
                                       invxfm,
                                       applyxfm,
                                       applyxfm4D,
                                       concatxfm,
                                       mcflirt)
from fsl.wrappers.fnirt        import (fnirt,
                                       applywarp,
                                       invwarp,
                                       convertwarp)
from fsl.wrappers.fslmaths     import (fslmaths,)
from fsl.wrappers.fslstats     import (fslstats,)
from fsl.wrappers.fugue        import (fugue,
                                       prelude,
                                       sigloss,
                                       fsl_prepare_fieldmap)
from fsl.wrappers.melodic      import (melodic,
                                       fsl_regfilt)
from fsl.wrappers.misc         import (fslreorient2std,
                                       fslorient,
                                       fslroi,
                                       slicer,
                                       cluster,
                                       gps)
from fsl.wrappers.epi_reg      import  epi_reg
from fsl.wrappers              import  tbss
