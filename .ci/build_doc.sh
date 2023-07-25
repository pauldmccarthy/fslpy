#!/usr/bin/env /bash

set -e

source /test.env/bin/activate
pip install ".[doc]"
sphinx-build doc public
