module.exports = {
    presets: [
      '@babel/preset-env',   // Per trasformare JavaScript moderno (ES6+)
      '@babel/preset-react'  // Per trasformare JSX e funzioni di React
    ],
    plugins: [
      // Puoi aggiungere plugin opzionali qui, se necessari
      '@babel/plugin-transform-runtime' // Per migliorare le performance e gestire riferimenti globali
    ]
  };
  