#!/bin/bash

set -e

if [ "${1:0:6}" == "--env=" ]; then
  source "${1:6}/bin/activate"
  shift
fi

cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  mkdir -p static/build/
  rm -f static/build/ok

  if ! [ -f static/build/jquery.js ]; then
    npm install jquery@^1
    cp -p node_modules/jquery/dist/*.* static/build/
  fi

  if ! [ -f static/build/lodash.js ]; then
    npm install lodash@^2.4
    cp -p node_modules/lodash/dist/*.* static/build/
  fi

  if ! [ -f static/build/react.js ]; then
    npm install react@^0.11
    cp -p node_modules/react/dist/*.* static/build/
  fi

  if ! [ -f node_modules/.bin/jsx ]; then
    npm install react-tools@^0.11
  fi

  if ! [ -f static/build/spinner.svg ]; then
    wget https://raw.githubusercontent.com/kvakes/spinner.svg/master/spinner2.svg -O static/build/spinner.svg
  fi

  if ! [ -d node_modules/bootstrap-sass ]; then
    npm install bootstrap-sass@~3.2
  fi
  bs=node_modules/bootstrap-sass/assets
  if ! [ -f static/build/modal.js ]; then
    cp $bs/javascripts/bootstrap/*.js static/build/
  fi

  ./node_modules/.bin/jsx --harmony static/src/ static/build/

  sed -i "
    # Don't use pointer cursor on buttons.
    # http://lists.w3.org/Archives/Public/public-css-testsuite/2010Jul/0024.html
    s@cursor: pointer; // 3@@
    # Don't inherit color and font on inputs and selects.
    s@color: inherit; // 1@@
    s@font: inherit; // 2@@
    " $bs/stylesheets/bootstrap/_normalize.scss

  compressed='-s compressed'
  sassc $compressed -I $bs/stylesheets css/main.scss static/build/style.css

  (
    echo jquery.js
    echo react.js
    echo lodash.js
    echo transition.js
    echo modal.js
    python jsdeps.py main.js
  ) > static/build/jsdeps-dev

  (
    echo jquery.min.js
    echo react.min.js
    echo lodash.min.js
    echo transition.js
    echo modal.js
    python jsdeps.py main.js
  ) > static/build/jsdeps-prod

  touch static/build/ok

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static/build

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
