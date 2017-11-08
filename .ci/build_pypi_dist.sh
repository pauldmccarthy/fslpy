#!/usr/bin/env bash

pip install wheel
python setup.py sdist
python setup.py bdist_wheel
