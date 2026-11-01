#!/bin/sh
# usage: scripts/set.sh <bot command> <arg> <arg>   (arguments go as separate '|' fields)
exec python "$(dirname "$0")/live.py" bot "$@"
