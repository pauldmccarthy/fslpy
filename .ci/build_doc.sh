#!/usr/bin/env /bash

set -e

python setup.py doc
mv doc/html doc/"$CI_COMMIT_REF_NAME"
