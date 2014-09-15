#!/bin/bash

set -e
cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "watch" ] || [ "$1" == "" ]; then

  mkdir -p static/build/

  if ! [ -f static/build/jquery.js ]; then
    npm install jquery@^1
    cp -p node_modules/jquery/dist/*.* static/build/
  fi

  if ! [ -f static/build/react.js ]; then
    npm install react@^0.11
    cp -p node_modules/react/dist/*.* static/build/
  fi

  if ! [ -f node_modules/.bin/jsx ]; then
    npm install react-tools@^0.11
  fi

  if [ "$1" == "watch" ]; then
    watchopt=--watch
  else
    watchopt=
  fi
  ./node_modules/.bin/jsx $watchopt --harmony static/src/ static/build/

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static/build

else
  echo "usage: $0 [build|watch|clean]"
  exit 1
fi
