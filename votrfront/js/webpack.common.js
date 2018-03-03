const path = require('path');
const webpack = require('webpack');
const LodashModuleReplacementPlugin = require('lodash-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;

module.exports = {
  entry: {
    app: './main.js',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: 'babel-loader',
        },
      },
    ],
  },
  plugins: [
    new LodashModuleReplacementPlugin({
      shorthands: true,
    }),
    // remove the ProvidePlugin when libs/ folder is purged
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
    }),
    new BundleAnalyzerPlugin({
      openAnalyzer: false,
    }),
  ],
  output: {
    filename: 'votr.bundle.js',
    path: path.join(__dirname, '../static'),
  },
};
