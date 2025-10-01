#!/bin/bash

thisdir=$(cd $(dirname $0) && pwd)

source /test.venv/bin/activate

pip install .
pip install requests jinja2

zenodo_url=$1
zenodo_tkn=$2
zenodo_depid=$3

version=$(python -c "import fsl.version as v; print(v.__version__)")
upfile=$(pwd)/dist/fslpy-"$version".tar.gz
metafile=$(pwd)/.ci/zenodo_meta.json.jinja2
date=$(date +"%Y-%m-%d")

pip install --retries 10 requests jinja2

python "$thisdir"/zenodo.py \
       "$zenodo_url" \
       "$zenodo_tkn" \
       "$zenodo_depid" \
       "$upfile" \
       "$metafile" \
       "$version" \
       "$date"
