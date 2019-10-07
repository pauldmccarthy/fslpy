#!/usr/bin/env bash

set -e

# If running on a fork repository, we merge in the
# upstream/master branch. This is done so that merge
# requests from fork to the parent repository will
# have unit tests run on the merged code, something
# which gitlab CE does not currently do for us.
if [[ "$CI_PROJECT_PATH" != "$UPSTREAM_PROJECT" ]]; then
  git fetch upstream;
  git merge --no-commit --no-ff -s recursive -X ours upstream/master;
fi;

source /test.venv/bin/activate

pip install --retries 10 -r requirements.txt
pip install --retries 10 -r requirements-extra.txt
pip install --retries 10 -r requirements-dev.txt

# style stage
if [ "$TEST_STYLE"x != "x" ]; then pip install --retries 10 pylint flake8; fi;
if [ "$TEST_STYLE"x != "x" ]; then flake8                           fsl || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then pylint --output-format=colorized fsl || true; fi;
if [ "$TEST_STYLE"x != "x" ]; then exit 0; fi

# We need the FSL atlases for the atlas
# tests, and need $FSLDIR to be defined
export FSLDIR=/fsl/
mkdir -p $FSLDIR/data/
rsync -rv "fsldownload:$FSL_ATLAS_DIR" "$FSLDIR/data/atlases/"

# Finally, run the damned tests.
TEST_OPTS="--cov-report= --cov-append"

# We run some tests under xvfb-run
# because they invoke wx. Sleep in
# between, otherwise xvfb gets upset.
xvfb-run -a python setup.py test --addopts="$TEST_OPTS tests/test_idle.py"
sleep 5
xvfb-run -a python setup.py test --addopts="$TEST_OPTS tests/test_platform.py"

# We run the immv/imcp tests as the nobody
# user because some tests expect permission
# denied errors when looking at files, and
# root never gets denied. Make everything in
# this directory writable by anybody (which,
# unintuitively, includes nobody)
chmod -R a+w `pwd`
cmd="source /test.venv/bin/activate && python setup.py test"
cmd="$cmd --addopts='$TEST_OPTS tests/test_scripts/test_immv_imcp.py tests/test_immv_imcp.py'"
su -s /bin/bash -c "$cmd" nobody

# All other tests can be run as normal.
python setup.py test --addopts="$TEST_OPTS -m 'not longtest' --ignore=tests/test_idle.py --ignore=tests/test_platform.py --ignore=tests/test_immv_imcp.py --ignore=tests/test_scripts/test_immv_imcp.py"

# Long tests are only run on release branches
if [[ $CI_COMMIT_REF_NAME == v* ]]; then
    python setup.py test --addopts="$TEST_OPTS -m 'longtest'"
fi

python -m coverage report
