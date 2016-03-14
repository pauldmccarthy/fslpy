#!/usr/bin/env python
#
# tensorimage.py - The TensorImage class.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#
"""This module provides the :class:`.TensorImage` class, which encapsulates
the diffusion tensor data generated by the FSL ``dtifit`` tool.
"""


import                   logging
import                   re
import                   glob
import os.path        as op

import fsl.data.image as fslimage


log = logging.getLogger(__name__)


def getTensorDataPrefix(path):
    """Returns the prefix used for the DTI file names in the given
    directory, or ``None`` if the DTI files could not be identified.
    """
    
    v1s   = glob.glob(op.join(path, '*_V1.*'))
    v2s   = glob.glob(op.join(path, '*_V2.*'))
    v3s   = glob.glob(op.join(path, '*_V3.*'))
    l1s   = glob.glob(op.join(path, '*_L1.*'))
    l2s   = glob.glob(op.join(path, '*_L2.*'))
    l3s   = glob.glob(op.join(path, '*_L3.*'))
    fas   = glob.glob(op.join(path, '*_FA.*'))
    mds   = glob.glob(op.join(path, '*_MD.*'))
    files = [v1s, v2s, v3s, l1s, l2s, l3s, fas, mds]
    
    # Make sure there is exactly one
    # of each of the above files
    def lenone(l):
        return len(l) == 1

    if not all(map(lenone, files)):
        return None

    files = [f[0] for f in files]

    # Make sure that all of the above
    # files have the same prefix
    pattern  = '^(.*)_(?:V1|V2|V3|L1|L2|L3|FA|MD).*$'
    prefixes = [re.findall(pattern, f)[0] for f in files]

    if any([p != prefixes[0] for p in prefixes]):
        return None

    # And there's our prefix
    return op.basename(prefixes[0])


def isPathToTensorData(path):
    """Returns ``True`` if the given directory path looks like it contains
    ``dtifit`` data, ``False`` otherwise.
    """
    
    return getTensorDataPrefix(path) is not None


class TensorImage(fslimage.Nifti1):
    """The ``TensorImage`` class is able to load and encapsulate the diffusion
    tensor data generated by the FSL ``dtifit`` tool.
    """

    
    def __init__(self, path):
        """Create a ``TensorImage``.

        :arg path: A path to a ``dtifit`` directory. Alternately, the ``path``
                   may be a dictionary with keys
                   ``{'v1', 'v2', 'v3', 'l1', 'l2', 'l3'}``, which specify
                   paths to images containing the tensor eigenvectors and
                   eigenvalues.
        """

        dtifitDir = isinstance(path, basestring)

        if dtifitDir:

            prefix = getTensorDataPrefix(path)

            if prefix is None:
                raise ValueError('Invalid path: {}'.format(path))

            v1 = op.join(path, '{}_V1'.format(prefix))
            v2 = op.join(path, '{}_V2'.format(prefix))
            v3 = op.join(path, '{}_V3'.format(prefix))
            l1 = op.join(path, '{}_L1'.format(prefix))
            l2 = op.join(path, '{}_L2'.format(prefix))
            l3 = op.join(path, '{}_L3'.format(prefix))

            paths = {'v1' : v1, 'v2' : v2, 'v3' : v3,
                     'l1' : l1, 'l2' : l2, 'l3' : l3}
            
        else:
            paths = path

        fslimage.Nifti1.__init__(self, paths['l1'], loadData=False)

        self.__v1 = fslimage.Image(paths['v1'])
        self.__v2 = fslimage.Image(paths['v2'])
        self.__v3 = fslimage.Image(paths['v3'])
        self.__l1 = fslimage.Image(paths['l1'])
        self.__l2 = fslimage.Image(paths['l2'])
        self.__l3 = fslimage.Image(paths['l3'])

        l1dir = op.abspath(op.dirname(paths['l1']))

        self.dataSource = l1dir
        self.name       = '{}[tensor]'.format(op.basename(l1dir))

        log.memory('{}.init({})'.format(type(self).__name__, id(self)))

        
    def __del__(self):
        if log:
            log.memory('{}.del({})'.format(type(self).__name__, id(self)))

        
    def V1(self): return self.__v1
    def V2(self): return self.__v2
    def V3(self): return self.__v3
    def L1(self): return self.__l1
    def L2(self): return self.__l2
    def L3(self): return self.__l3