#!/usr/bin/env bash
# This script captures both positional and named arguments
# and passes them on to tcy.

if [[ ! $@ ]]; then
    python3 -m tcy -h
else
    python3 -m tcy $@
fi
