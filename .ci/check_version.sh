#!/usr/bin/env bash

set -e

cat fsl/version.py | egrep "^__version__ += +'$CI_COMMIT_REF_NAME' *$"
