const fs = require('fs');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const webpack = require('webpack');

const bootstrapPath = __dirname + '/node_modules/bootstrap-sass/assets/stylesheets';

// A custom node-sass importer that removes some unwanted rules from _normalize.scss.
function importerWhichRewritesBootstrapNormalizeScss(url, prev, done) {
  if (url != 'bootstrap/normalize') {
    done(null);
    return;
  }

  fs.readFile(bootstrapPath + '/bootstrap/_normalize.scss', 'utf8', (err, data) => {
    if (err) return done(err);

    function remove(what) {
      if (!data.includes(what)) throw Error(`"${what}" not found`);
      data = data.replace(what, '');
    }

    // Don't use pointer cursor on buttons.
    // http://lists.w3.org/Archives/Public/public-css-testsuite/2010Jul/0024.html
    remove('cursor: pointer; // 3');

    // Don't inherit color and font on inputs and selects.
    remove('color: inherit; // 1');
    remove('font: inherit; // 2');

    done({ contents: data });
  });
}

const outputPath = __dirname + '/votrfront/static';

// A plugin which writes the current status to votrfront/static/status.
// - "busy" during compilation
// - "failed" on errors
// - "ok_dev" or "ok_prod" on success
// votrfront/front.py reads the status to check if it can serve the page.
function StatusFilePlugin(mode) {
  this.apply = function(compiler) {
    function writeStatus(content, callback) {
      fs.mkdir(outputPath, function (err) {
        if (err && err.code != 'EEXIST') return callback(err);
        fs.writeFile(outputPath + '/status', content + '\n', 'utf8', callback);
      });
    }

    function handleRunEvent(compilationParams, callback) {
      writeStatus('busy', callback);
    }

    compiler.hooks.run.tapAsync('StatusFilePlugin', handleRunEvent);
    compiler.hooks.watchRun.tapAsync('StatusFilePlugin', handleRunEvent);
    compiler.hooks.done.tapAsync('StatusFilePlugin', (stats, callback) => {
      const status = stats.compilation.errors.length ? 'failed' : 'ok_' + mode;
      writeStatus(status, callback);
    });
  };
}

// A plugin which deletes old .map files. We can't use clean-webpack-plugin to
// delete *.map before every compilation, because in watch mode, if a .js file
// doesn't change then its .map file won't be regenerated.
function CleanMapFilesPlugin() {
  this.apply = function(compiler) {
    compiler.hooks.afterEmit.tapAsync('CleanMapFilesPlugin', function(compilation, callback) {
      fs.readdirSync(outputPath).forEach(file => {
        if (file.match(/\.map$/) && !compilation.assets[file] &&
            compilation.assets[file.replace(/\.\w+\.map$/, '')]) {
          fs.unlinkSync(outputPath + '/' + file);
        }
      });
      callback();
    });
  }
}

module.exports = function (env, args) {
  const mode = args.mode;

  const config = {
    entry: {
      votr: './votrfront/js/main',
      prologue: './votrfront/js/prologue',
    },
    output: {
      path: outputPath,
      filename: mode == 'development' ? '[name].dev.js' : '[name].min.js',
      sourceMapFilename: '[file].[hash].map',   // it seems Chrome caches source maps even if "Disable cache" is enabled
    },
    plugins: [
      new MiniCssExtractPlugin({ filename: 'style.css' }),
      new StatusFilePlugin(mode == 'development' ? 'dev' : 'prod'),
      new CleanMapFilesPlugin(),
      new webpack.ContextReplacementPlugin(/moment[/\\]locale$/, /sk/),
    ],
    module: {
      rules: [
        {
          // Without this, webpack tries to replace `define.amd` in jquery and
          // file-saver with its own definition.
          parser: { amd: false }
        },
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel-loader',
        },
        {
          test: /node_modules\/bootstrap-sass\//,
          loader: 'imports-loader',
          options: { 'jQuery': 'jquery' },
        },
        {
          test: /\.scss$/,
          use: [
            MiniCssExtractPlugin.loader,
            'css-loader',
            {
              loader: 'sass-loader',
              options: {
                sassOptions: {
                  includePaths: [bootstrapPath],
                  outputStyle: mode == 'development' ? undefined : 'compressed',
                  importer: importerWhichRewritesBootstrapNormalizeScss,
                },
              },
            },
          ],
        },
        {
          test: /\.svg$/,
          loader: 'url-loader',
        },
      ],
    },
    optimization: {
      splitChunks: {
        chunks: 'all',
        minSize: 0,
        automaticNameDelimiter: '_',
      },
    },
    devtool: 'source-map',
    performance: {
      maxAssetSize: 750 * 1024,
      maxEntrypointSize: 750 * 1024,
    },
  };

  return config;
};
