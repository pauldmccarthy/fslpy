#!/usr/bin/env BASH

set -e

pip install setuptools wheel twine
twine upload dist/*
