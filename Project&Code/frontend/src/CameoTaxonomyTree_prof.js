import React, { useState, useEffect } from 'react';
import Tree from 'rc-tree';
import 'rc-tree/assets/index.css';

const CameoTaxonomyTree = () => {
    const [data, setData] = useState([]);
    const [selectedKeys, setSelectedKeys] = useState([]);
     // Caricamento dinamico della tassonomia da un file TXT locale

    useEffect(() => {
    fetch('/static/CAMEO.eventcodes.txt')
      .then((response) => response.text())
      .then((textData) => {
        const parsedData = buildTreeFromText(textData);
        setData(parsedData);
        console.log("Dati dell'albero:", parsedData); // Log dei dati dell'albero
      })
      .catch((error) => {
        console.error('Errore durante il caricamento del file:', error);
      });
  }, []);

  // Funzione per costruire l'albero dalla tassonomia TXT
  const buildTreeFromText = (textData) => {
    const lookup = {};
    const root = [];

    const lines = textData.split('\n');
    lines.forEach((line) => {
      const [code, name] = line.split('\t');
      if (code && name) {
        const newNode = {
          key: code.trim(),
          title: `${name.trim()} (${code.trim()})`,
          children: [],
        };
        lookup[code.trim()] = newNode;

        const parentCode = code.length > 2 ? code.slice(0, -2) : null;
        if (parentCode && lookup[parentCode]) {
          lookup[parentCode].children.push(newNode);
        } else {
          root.push(newNode);
        }
      }
    });
    
    return root;
  };

  // Funzione per gestire la selezione dei nodi con checkbox
  const onCheck = (checkedKeys) => {
    setSelectedKeys(checkedKeys);
    console.log("Chiavi selezionate:", checkedKeys); // Log delle chiavi selezionate
  };

  useEffect(() => {
    const input = document.getElementById('selectedCodesInput');
    if (input) {
      input.value = JSON.stringify(selectedKeys); // Invia come JSON
    }
  }, [selectedKeys]);

    return (
      <div>
        <h2>Taxonomy of CAMEO Events</h2>
        <Tree
          checkable
          onCheck={onCheck}
          treeData={data}
          checkedKeys={selectedKeys}
        />
      </div>
    );
  };
  
  export default CameoTaxonomyTree;