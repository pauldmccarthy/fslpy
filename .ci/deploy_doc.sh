#!/usr/bin/env bash

set -e

rsync -rv doc/"$CI_COMMIT_REF_NAME" "docdeploy:"
