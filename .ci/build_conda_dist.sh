#!/usr/bin/env bash

set -e

name=$1
version=$2

# add any extra channels that are needed
for channel in $CONDA_CHANNELS; do
    conda config  --append channels $channel
done

# insert project name/version into meta.yaml
echo "{% set name    = '$name' %}"    >  vars.txt
echo "{% set version = '$version' %}" >> vars.txt
cat vars.txt .conda/meta.yaml > tempfile
mv tempfile .conda/meta.yaml
rm vars.txt

mkdir -p dist

conda update conda setuptools conda-build

conda build --output-folder=dist .conda

# tar it up
cd dist
tar czf "$name"-"$version"-conda.tar.gz *
