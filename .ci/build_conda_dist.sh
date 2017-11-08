#!/usr/bin/env bash

conda update conda
conda install setuptools conda-build

cd .conda

mkdir -p ../dist

# get version and name
version=`python ../setup.py -V`
name=`python ../setup.py --name`

cat ../requirements.txt     >  requirements.txt
cat ../requirements-dev.txt >> requirements.txt

echo "{% set name    = '$name' %}"    >  vars.txt
echo "{% set version = '$version' %}" >> vars.txt

cat vars.txt meta.yaml > tempfile
mv tempfile meta.yaml
rm vars.txt

conda build --output-folder=../dist .
