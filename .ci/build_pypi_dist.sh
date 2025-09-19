#!/usr/bin/env bash

set -e

pip install --upgrade pip wheel setuptools setuptools-scm twine build

python -m build
twine check dist/*

# do a test install from both source and wheel
sdist=`find dist -maxdepth 1 -name *.tar.gz`
wheel=`find dist -maxdepth 1 -name *.whl`

for target in $sdist $wheel; do
    python -m venv test.venv
    . test.venv/bin/activate
    pip install --upgrade pip setuptools
    pip install $target
    deactivate
    rm -r test.venv
done
