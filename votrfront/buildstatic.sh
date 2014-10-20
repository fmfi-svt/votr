#!/bin/bash

set -e

if [ "${1:0:6}" == "--env=" ]; then
  source "${1:6}/bin/activate"
  shift
fi

cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  mkdir -p static/libs/
  rm -f static/ok

  if ! [ -f static/libs/jquery.js ]; then
    npm install jquery@^1
    cp -p node_modules/jquery/dist/*.* static/libs/
  fi

  if ! [ -f static/libs/lodash.js ]; then
    npm install lodash@^2.4
    cp -p node_modules/lodash/dist/*.* static/libs/
  fi

  if ! [ -f static/libs/react.js ]; then
    npm install react@^0.11
    cp -p node_modules/react/dist/*.* static/libs/
  fi

  if ! [ -f node_modules/.bin/jsx ]; then
    npm install react-tools@^0.11
  fi

  if ! [ -f node_modules/.bin/uglifyjs ]; then
    npm install uglify-js@^2.4
  fi

  if ! [ -d node_modules/bootstrap-sass ]; then
    npm install bootstrap-sass@~3.2
  fi
  bs=node_modules/bootstrap-sass/assets
  if ! [ -f static/libs/modal.js ]; then
    cp $bs/javascripts/bootstrap/*.js static/libs/
  fi

  if ! [ -f static/spinner.svg ]; then
    wget https://raw.githubusercontent.com/kvakes/spinner.svg/master/spinner2.svg -O static/spinner.svg
  fi

  ./node_modules/.bin/jsx --harmony js/ static/dev/

  sed -i "
    # Don't use pointer cursor on buttons.
    # http://lists.w3.org/Archives/Public/public-css-testsuite/2010Jul/0024.html
    s@cursor: pointer; // 3@@
    # Don't inherit color and font on inputs and selects.
    s@color: inherit; // 1@@
    s@font: inherit; // 2@@
    " $bs/stylesheets/bootstrap/_normalize.scss

  compressed='-s compressed'
  sassc $compressed -I $bs/stylesheets css/main.scss static/style.css

  deps=$(python jsdeps.py dev/main.js)
  ./node_modules/.bin/uglifyjs \
      -o static/votr.min.js --source-map static/votr.min.js.map \
      $(sed 's@^@static/@' <<<"$deps") --screw-ie8 -m -c -p relative

  libs='dev/old.js libs/jquery.min.js libs/react.min.js libs/lodash.min.js libs/transition.js libs/modal.js'
  echo ${libs//.min} $deps > static/jsdeps-dev
  echo $libs votr.min.js > static/jsdeps-prod

  touch static/ok

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
