#!/usr/bin/env bash

rsync -rv doc/"$CI_COMMIT_REF_NAME" "docdeploy:"
