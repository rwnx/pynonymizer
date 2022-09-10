#!/usr/bin/env bash

# get_helptext.sh 
# 
# get the helptext in a canonical format (depends on terminal width)
# You should copy the output of this into README.md
set -e

stty rows 23 cols 80 &> /dev/null
pynonymizer -h
