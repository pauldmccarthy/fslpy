#!/usr/bin/env bash

set -e

micromamba activate /test.env
pip install  dist/*.whl

exp=${CI_COMMIT_REF_NAME}
got=$(python -c "import fsl.version as v;print(v.__version__)")

echo "Tagged version:   ${exp}"
echo "Reported version: ${got}"

if [[ ${exp} == ${got} ]]; then
  exit 0
else
  exit 1
fi
