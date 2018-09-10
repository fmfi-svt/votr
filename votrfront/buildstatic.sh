#!/bin/bash

set -e

if [ "${1:0:6}" == "--env=" ]; then
  source "${1:6}/bin/activate"
  shift
fi

cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  mkdir -p static/
  rm -f static/ok

  yarn --cwd=.. install

  rm -f static/votr.min.js.*.map
  yarn webpack --mode=production --progress --display=minimal

  echo prologue.min.js votr.min.js vendors_votr.min.js > static/jsdeps-dev
  echo prologue.min.js votr.min.js vendors_votr.min.js > static/jsdeps-prod

  touch static/ok

elif [ "$1" == "clean" ]; then

  rm -rf node_modules ../node_modules static

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
