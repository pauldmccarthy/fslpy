#!/usr/bin/env /bash

set -e

pip install -r requirements-dev.txt
python setup.py doc
mkdir -p public
mv doc/html/* public/
