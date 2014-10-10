#!/bin/bash

set -e
cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  mkdir -p static/build/

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

  ./node_modules/.bin/jsx --harmony static/src/ static/build/

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static/build

else
  echo "usage: $0 [build|clean]"
  exit 1
fi
