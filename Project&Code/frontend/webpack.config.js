const path = require('path');

module.exports = {
  entry: './src/index.js',  // Punto di ingresso principale
  output: {
    path: path.resolve(__dirname, '../flask-app/app/static/js'), // Percorso di output nella directory static di Flask
    filename: 'bundle.js', // Nome del file generato
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,  // Processa file .js e .jsx
        exclude: /node_modules/,
        use: 'babel-loader',  // Usa babel-loader, che leggerà babel.config.js
      },
      {
        test: /\.css$/,  // Supporto per file CSS
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  resolve: {
    extensions: ['.js', '.jsx'],  // Supporto per estensioni .js e .jsx
  },
  mode: 'production',  // Modalità di produzione
};

