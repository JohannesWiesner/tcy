#!/usr/bin/env bash
# This script is used to provide tcy as a command-line application
# after users install tcy via pip. It passes all command-line arguments
# over to tcy.

if (( $# == 0 )); then
    python3 -m tcy -h
else
    python3 -m tcy "$@"
fi

