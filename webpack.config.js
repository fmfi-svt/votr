const MiniCssExtractPlugin = require("mini-css-extract-plugin");

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
                includePaths: [__dirname + '/votrfront/static', __dirname + '/node_modules/bootstrap-sass/assets/stylesheets'],
                outputStyle: mode == 'development' ? undefined : 'compressed',
              },
            },
          ],
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
