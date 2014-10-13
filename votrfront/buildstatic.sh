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

  if ! [ -d node_modules/bootstrap-sass ]; then
    npm install bootstrap-sass@^3.2
  fi

  ./node_modules/.bin/jsx --harmony static/src/ static/build/

  sassc -I node_modules/bootstrap-sass/assets/stylesheets \
      -s compressed \
      css/main.scss static/build/style.css

  (
    echo jquery.js
    echo react.js
    echo lodash.js
    python jsdeps.py main.js
  ) > static/build/jsdeps-dev

  (
    echo jquery.min.js
    echo react.min.js
    echo lodash.min.js
    python jsdeps.py main.js
  ) > static/build/jsdeps-prod

  touch static/build/ok

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static/build

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
