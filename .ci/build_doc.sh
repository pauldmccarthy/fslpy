#!/usr/bin/env /bash

set -e

source /test.venv/bin/activate
pip install ".[doc]"
sphinx-build doc public
