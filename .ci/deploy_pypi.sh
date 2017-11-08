#!/usr/bin/env BASH

pip install setuptools wheel twine
twine upload dist/*
