#!/bin/bash

set -e

if [ "${1:0:6}" == "--env=" ]; then
  source "${1:6}/bin/activate"
  shift
fi

cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

mkdir -p static

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  sassc -s compressed css/src/main.scss css/dist/votr.css
  cp css/dist/votr.css static/votr.css

elif [ "$1" == "bootstrap" ]; then

  if ! [ -d node_modules/bootstrap-sass ]; then
    npm install bootstrap-sass@^3.3
  fi
  bs=node_modules/bootstrap-sass/assets

  sed -i "
    # Don't use pointer cursor on buttons.
    # http://lists.w3.org/Archives/Public/public-css-testsuite/2010Jul/0024.html
    s@cursor: pointer; // 3@@
    # Don't inherit color and font on inputs and selects.
    s@color: inherit; // 1@@
    s@font: inherit; // 2@@
    " $bs/stylesheets/bootstrap/_normalize.scss

  compressed='-s compressed'
  sassc $compressed -I $bs/stylesheets css/src/_votr-bootstrap.scss css/dist/bootstrap.custom.css
  cp css/dist/bootstrap.custom.css static/bootstrap.custom.css

elif [ "$1" == "setup" ]; then

  cp css/dist/bootstrap.custom.css static/bootstrap.custom.css
  cp css/dist/votr.css static/votr.css

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
