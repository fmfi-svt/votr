#!/bin/bash

set -e

if [ "${1:0:6}" == "--env=" ]; then
  source "${1:6}/bin/activate"
  shift
fi

cd "$(dirname "$0")"

! [ -w "$HOME" ] && echo "HOME is not writable" && exit 1

if [ "$1" == "build" ] || [ "$1" == "" ]; then

  mkdir -p static/libs/ static/cache/
  rm -f static/ok

  if ! [ -f static/libs/jquery.js ]; then
    npm install jquery@^3
    cp -p node_modules/jquery/dist/jquery.* static/libs/
  fi

  if ! [ -f static/libs/lodash.js ]; then
    npm install lodash@^4
    cp -p node_modules/lodash/lodash.{min.,}js static/libs/
  fi

  if ! [ -f static/libs/react.js ]; then
    npm install react@^16.3.1
    cp -p node_modules/react/umd/react.development.js static/libs/react.js
    cp -p node_modules/react/umd/react.production.min.js static/libs/react.min.js
  fi

  if ! [ -f static/libs/react-dom.js ]; then
    npm install react-dom@^16.3.1
    cp -p node_modules/react-dom/umd/react-dom.development.js static/libs/react-dom.js
    cp -p node_modules/react-dom/umd/react-dom.production.min.js static/libs/react-dom.min.js
  fi

  if ! [ -f static/libs/prop-types.js ]; then
    npm install prop-types@^15.6.1
    cp -p node_modules/prop-types/prop-types*.js static/libs/
  fi

  if ! [ -f static/libs/FileSaver.min.js ]; then
    npm install file-saver@1.3.8  # pinned! breaks too often.
    cp node_modules/file-saver/FileSaver*.* static/libs/
  fi

  if ! [ -f node_modules/.bin/webpack ]; then
    npm install node-libs-browser@^0.5   # from peerDependencies of webpack
    npm install babel-core@^5   # from peerDependencies of babel-loader
    npm install webpack@^1.10
    npm install babel-loader@^5
  fi

  if ! [ -d node_modules/bootstrap-sass ]; then
    npm install bootstrap-sass@^3.3
  fi
  bs=node_modules/bootstrap-sass/assets
  if ! [ -f static/libs/modal.js ]; then
    cp $bs/javascripts/bootstrap/*.js static/libs/
  fi

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

  compressed='-s compressed'
  sassc $compressed -I $bs/stylesheets -I static css/main.scss static/style.css

  if ! [ -f static/webpacktime ] || [ "$(find js/ webpack.config.js -newer static/webpacktime)" ]; then
    touch static/webpacktime
    rm -f static/votr.min.js.*.map
    ./node_modules/.bin/webpack
  else
    echo "webpack output is up to date."
  fi

  libs='prologue.js libs/jquery.min.js libs/react.min.js libs/react-dom.min.js libs/prop-types.min.js libs/lodash.min.js libs/transition.js libs/modal.js libs/FileSaver.min.js'
  dev=(static/dev/*)
  echo ${libs//.min} "${dev[@]//"static/"}" votr.dev.js > static/jsdeps-dev
  echo $libs votr.min.js > static/jsdeps-prod

  touch static/ok

elif [ "$1" == "clean" ]; then

  rm -rf node_modules static

else
  echo "usage: $0 [--env=path/to/venv] [build|clean]"
  exit 1
fi
