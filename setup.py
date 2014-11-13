#!/usr/bin/env python
#
# setup.py - setuptools configuration for installing the fslpy package.
#
# Author: Paul McCarthy <pauldmccarthy@gmail.com>
#

from setuptools import setup
from setuptools import find_packages


setup(

    name='fslpy',

    version='0.0',

    description='Front end to FSL tools',

    url='https://git.fmrib.ox.ac.uk/paulmc/fslpy',

    author='Paul McCarthy',

    author_email='pauldmccarthy@gmail.com',

    license='FMRIB',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: Free for non-commercial use',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules'],

    packages=find_packages(exclude=('doc')),

    install_requires=[
        'pyopengl>=3.1.0',
        'numpy>=1.8.1',
        'scipy>=0.14.0',
        'matplotlib>=1.3.1',
        'nibabel>=1.3.0',
        'Pillow>=2.5.3'],

    entry_points={'console_scripts' : ['fslpy = fsl.main']}
)
