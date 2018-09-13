#!/usr/bin/env /bash

set -e

pip install -r requirements-dev.txt
python setup.py doc
mv doc/html doc/"$CI_COMMIT_REF_NAME"
