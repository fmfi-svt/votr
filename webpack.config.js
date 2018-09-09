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
    ],
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel-loader',
        },
      ],
    },
    devtool: 'source-map',
    performance: {
      maxAssetSize: 750 * 1024,
      maxEntrypointSize: 750 * 1024,
    },
  };

  return config;
};
