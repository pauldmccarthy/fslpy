#!/usr/bin/env /bash

set -e

pip install git+https://github.com/pauldmccarthy/sphinx_rtd_dark_mode.git@bf/fixes
pip install ".[doc]"
sphinx-build doc public
