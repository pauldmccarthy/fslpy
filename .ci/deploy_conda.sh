#!/usr/bin/env bash

set -e

rsync -rv dist/*conda.tar.gz "condadeploy:"
