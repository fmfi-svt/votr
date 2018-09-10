const fs = require('fs');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");

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
      sourceMapFilename: '[file].' + Date.now() + '.map',   // it seems Chrome caches source maps even if "Disable cache" is enabled
    },
    plugins: [
      new MiniCssExtractPlugin({ filename: 'style.css' }),
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
                includePaths: [bootstrapPath],
                outputStyle: mode == 'development' ? undefined : 'compressed',
                importer: importerWhichRewritesBootstrapNormalizeScss,
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
