#!/usr/bin/env bash

if [[ "x$CI_COMMIT_TAG" != "x" ]]; then
  echo "Release detected - patching version - $CI_COMMIT_REF_NAME";
  python -c "import fsl.version as v; v.patchVersion('fsl/version.py', '$CI_COMMIT_REF_NAME')";
fi
