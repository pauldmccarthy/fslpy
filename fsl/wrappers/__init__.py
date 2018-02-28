#!/usr/bin/env python
#
# __init__.py - Wrappers for FSL command-line tools.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This package contains wrappers for various FSL command line tools, allowing
them to be called from Python.
"""


from .bet      import (bet,)            # noqa
from .eddy     import (eddy_cuda,       # noqa
                       topup)
from .flirt    import (flirt,           # noqa
                       invxfm,
                       applyxfm,
                       concatxfm,
                       mcflirt)
from .fnirt    import (fnirt,           # noqa
                       applywarp,
                       invwarp,
                       convertwarp)
from .fslmaths import (fslmaths,)       # noqa
from .fugue    import (fugue,           # noqa
                       sigloss)
from .melodic  import (melodic,         # noqa
                       fsl_regfilt)
from .misc     import (fslreorient2std, # noqa
                       fslroi,
                       slicer,
                       cluster)
