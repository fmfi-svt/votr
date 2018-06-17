
var webpack = require("webpack");
var ConcatSource = require("webpack/lib/ConcatSource");


function VotrDevelPlugin(moduleVariablePrefix, outputPath) {
  this.moduleVariablePrefix = moduleVariablePrefix;
  this.outputPath = outputPath;
}

VotrDevelPlugin.prototype.apply = function (compiler) {
  var self = this;
  compiler.plugin('compilation', function (compilation) {
    compilation.moduleTemplate.plugin('package', function (moduleSource, module) {
      // Ugly hack to remove the newlines added by FunctionModuleTemplatePlugin.
      if (moduleSource instanceof ConcatSource && moduleSource.children[0].constructor === String) {
        moduleSource.children[0] = moduleSource.children[0].replace(/\n*$/, '');
      }

      // Uglier hack to move the whole source code to a separate file.
      var id = self.moduleVariablePrefix + module.id;
      var req = module.readableIdentifier(this.requestShortener);
      var devFilename = self.outputPath + req.replace(/\.\w+$/, '').replace(/^\.\//, '').replace(/\W/g, '_') + '.js';

      compilation.assets[devFilename] = new ConcatSource(id, ' = ', moduleSource);
      return id;
    });
  });
};


function makeConfig() {
  return {
    context: __dirname + '/js',
    entry: './main',
    output: {
      path: __dirname + '/static',
      sourceMapFilename: '[file].' + Date.now() + '.map',   // it seems Chrome caches source maps even if "Disable cache" is enabled
    },
    externals: { "react": "React", "prop-types": "PropTypes" },
    plugins: [],
    module: {
      loaders: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          loader: 'babel',
          query: {
            cacheDirectory: __dirname + '/static/cache',
            loose: ['es6.destructuring', 'es6.properties.computed', 'es6.spread'],
            optional: ['es7.classProperties'],
          },
        },
      ],
    },
    records: __dirname + '/static/records',
  };
};


var prodConfig = makeConfig();
prodConfig.output.filename = 'votr.min.js';
prodConfig.plugins.push(new webpack.optimize.UglifyJsPlugin());
prodConfig.plugins.push(new webpack.optimize.OccurenceOrderPlugin());
prodConfig.devtool = 'source-map';


var devConfig = makeConfig();
devConfig.output.filename = 'votr.dev.js';
devConfig.plugins.push(new VotrDevelPlugin('_votr_module_', 'dev/'));
devConfig.module.loaders[0].query.retainLines = true;


var prologueConfig = makeConfig();
prologueConfig.entry = './prologue';
prologueConfig.output.filename = 'prologue.js';
prologueConfig.plugins.push(new webpack.optimize.UglifyJsPlugin());
prologueConfig.plugins.push(new webpack.optimize.OccurenceOrderPlugin());


module.exports = [prodConfig, devConfig, prologueConfig];
