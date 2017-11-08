#!/usr/bin/env bash

conda update conda
conda install setuptools conda-build

mkdir -p dist

cd .conda

# get version and name. We call
# setup.py beforehand because it
# will install a bunch of deps,
# and output a bunch of stuff.
python ../setup.py -V &> /dev/null
version=`python ../setup.py -V`
name=`python ../setup.py --name`

# invoking setup.py causes it to
# install deps, which conda will
# incklude in thye build
rm -rf .eggs

# insert name/version into meta.yaml
echo "{% set name    = '$name' %}"    >  vars.txt
echo "{% set version = '$version' %}" >> vars.txt

cat vars.txt meta.yaml > tempfile
mv tempfile meta.yaml
rm vars.txt

# do the build
conda build --output-folder=../dist .

# tar it up
cd ../dist
tar czf "$name"-"$version"-conda.tar.gz *
cd ..
