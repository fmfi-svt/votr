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

  bs=../node_modules/bootstrap-sass/assets

  if ! [ -f static/_spinner.scss ]; then
    node -e 'console.log("$spinner: url(data:image/svg+xml," + escape(require("fs").readFileSync("css/spinner.svg", "ascii")) + ");")' > static/_spinner.scss
  fi

  sed -i "
    # Don't use pointer cursor on buttons.
    # http://lists.w3.org/Archives/Public/public-css-testsuite/2010Jul/0024.html
    s@cursor: pointer; // 3@@
    # Don't inherit color and font on inputs and selects.
    s@color: inherit; // 1@@
    s@font: inherit; // 2@@
    " $bs/stylesheets/bootstrap/_normalize.scss

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
