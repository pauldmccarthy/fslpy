#!/usr/bin/env /bash

python setup.py doc
mv doc/html doc/"$CI_COMMIT_REF_NAME"
