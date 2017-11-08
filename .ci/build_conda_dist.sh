#!/usr/bin/env bash

conda update conda
conda install setuptools conda-build
cd .conda

# get version and name
version=`python ../setup.py -V`
name=`python ../setup.py --name`

# get requirements, and make
# them conda compatible...

# strip all spaces
reqs=`cat ../requirements.txt ../requirements-dev.txt | sed -e 's/ //g'`

# add a space after package name -
# package names must match a-zA-Z0-9_
reqs=`echo "$reqs" | sed -e "s/^[a-zA-Z0-9_][a-zA-Z0-9_]*/& /g"`

# remove ==, replace it with a space
reqs=`echo "$reqs" | sed -e "s/==/ /g"`

# wrap each dep in quotes
reqs=`echo "$reqs" | sed -e "s/^.*$/'&'/g"`

# add a comma at the end
reqs=`echo "$reqs" | sed -e "s/$/,/g"`

# remove newlines
reqs=`echo $reqs`

echo "version: $version"
echo "name:    $name"
echo "reqs:    $reqs"

echo "{% set name         = 'name' %}"     >  vars.txt
echo "{% set version      = '$version' %}" >> vars.txt
echo "{% set requirements = [$reqs] %}"    >> vars.txt
cat vars.txt meta.yaml > tempfile
mv tempfile meta.yaml
rm vars.txt

conda build fslpy

cd ..
