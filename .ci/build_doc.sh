#!/usr/bin/env /bash

set -e

pip install ".[doc]"
sphinx-build doc public
