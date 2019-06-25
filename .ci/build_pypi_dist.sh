#!/usr/bin/env bash

set -e

pip install wheel setuptools twine
python setup.py sdist
python setup.py bdist_wheel
twine check dist/*

# do a test install from both source and wheel
sdist=`find dist -maxdepth 1 -name *.tar.gz`
wheel=`find dist -maxdepth 1 -name *.whl`

# pip < 10 will not install wheels
# with an invalid name. So we can
# generate builds from non-releases
# (e.g. master master branch),
# we hack the wheel file name here
# so that pip will accept it.
#
# This will no longer be necessary
# when pip 10 is available.
nwheel=`echo -n $wheel | sed -e 's/fslpy-/fslpy-0/g'`
mv $wheel $nwheel
wheel=$nwheel

for target in $sdist $wheel; do
    python -m venv test.venv
    . test.venv/bin/activate
    pip install --upgrade pip setuptools
    pip install $target
    deactivate
    rm -r test.venv
done
