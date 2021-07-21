const path = require('path')

module.exports = {
  entry: path.join(__dirname, 'app/static/src/components.jsx'),
  // Where files should be sent once they are bundled
  output: {
   path: path.join(__dirname, '/app/static/dist'),
   filename: 'components.js'
  },
  // Rules of how webpack will take our files, complie & bundle them for the browser 
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /nodeModules/,
        use: {
          loader: 'babel-loader'
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  externals: {
    'react': 'React',
    'react-dom': 'ReactDOM',
  }
}
