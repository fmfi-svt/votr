#!/bin/bash

cd "$(dirname "$0")"

mkdir -p static/build/

if ! [ -f static/build/jquery.js ]; then
  npm install jquery@^1
  cp -p node_modules/jquery/dist/*.js static/build/
fi

if ! [ -f static/build/react.js ]; then
  npm install react@^0.11
  cp -p node_modules/react/dist/*.js static/build/
fi

if ! [ -f node_modules/.bin/jsx ]; then
  npm install react-tools@^0.11
fi

./node_modules/.bin/jsx "$@" static/src/ static/build/
