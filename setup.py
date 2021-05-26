#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing the fslpy package.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#


from __future__ import print_function

import os.path       as op
import                  shutil
import unittest.mock as mock

from setuptools import setup
from setuptools import find_namespace_packages
from setuptools import Command


# The directory in which this setup.py file is contained.
basedir = op.dirname(__file__)

# Dependencies are listed in requirements.txt
with open(op.join(basedir, 'requirements.txt'), 'rt') as f:
    install_requires = [l.strip() for l in f.readlines()]

# Optional dependencies are listed in requirements-extra.txt
with open(op.join(basedir, 'requirements-extra.txt'), 'rt') as f:
    extra_requires = {'extras' : [l.strip() for l in f.readlines()]}

packages = find_namespace_packages(include=('fsl', 'fsl.*'))

# Figure out the current fslpy version, as defined in fsl/version.py. We
# don't want to import the fsl package,  as this may cause build problems.
# So we manually parse the contents of fsl/version.py to extract the
# version number.
version = {}
with open(op.join(basedir, "fsl", "version.py")) as f:
    for line in f:
        if line.startswith('__version__'):
            exec(line, version)
            break
version = version['__version__']

with open(op.join(basedir, 'README.rst'), 'rt') as f:
    readme = f.read()


class doc(Command):
    """Build the API documentation. """

    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):

        docdir  = op.join(basedir, 'doc')
        destdir = op.join(docdir, 'html')

        if op.exists(destdir):
            shutil.rmtree(destdir)

        print('Building documentation [{}]'.format(destdir))

        import sphinx.cmd.build as sphinx_build

        mockobj       = mock.MagicMock()
        mockobj.__version__ = '2.2.0'
        mockedModules = open(op.join(docdir, 'mock_modules.txt')).readlines()
        mockedModules = [l.strip()   for l in mockedModules]
        mockedModules = {m : mockobj for m in mockedModules}

        patches = [mock.patch.dict('sys.modules', **mockedModules)]

        [p.start() for p in patches]
        sphinx_build.main([docdir, destdir])
        [p.stop() for p in patches]


setup(

    name='fslpy',
    version=version,
    description='FSL Python library',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://git.fmrib.ox.ac.uk/fsl/fslpy',
    author='Paul McCarthy',
    author_email='pauldmccarthy@gmail.com',
    license='Apache License Version 2.0',
    python_requires='>=3.7',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Python Modules'],

    packages=packages,

    install_requires=install_requires,
    extras_require=extra_requires,
    package_data={'fsl': ['utils/filetree/trees/*']},

    test_suite='tests',

    cmdclass={'doc' : doc},

    entry_points={
        'console_scripts' : [
            'imcp           = fsl.scripts.imcp:main',
            'imln           = fsl.scripts.imln:main',
            'immv           = fsl.scripts.immv:main',
            'imrm           = fsl.scripts.imrm:main',
            'imglob         = fsl.scripts.imglob:main',
            'imtest         = fsl.scripts.imtest:main',
            'remove_ext     = fsl.scripts.remove_ext:main',
            'fsl_abspath    = fsl.scripts.fsl_abspath:main',
            'Text2Vest      = fsl.scripts.Text2Vest:main',
            'Vest2Text      = fsl.scripts.Vest2Text:main',
            'atlasq         = fsl.scripts.atlasq:main',
            'atlasquery     = fsl.scripts.atlasq:atlasquery_emulation',
            'fsl_ents       = fsl.scripts.fsl_ents:main',
            'resample_image = fsl.scripts.resample_image:main',
            'fsl_convert_x5 = fsl.scripts.fsl_convert_x5:main',
            'fsl_apply_x5   = fsl.scripts.fsl_apply_x5:main'
        ]
    }
)
