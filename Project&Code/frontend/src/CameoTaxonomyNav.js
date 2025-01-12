import React, { useState, useEffect } from 'react';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Form from 'react-bootstrap/Form';

const CameoTaxonomyNav = () => {
  const [data, setData] = useState([]);
  const [selectedKeys, setSelectedKeys] = useState([]);

  useEffect(() => {
    fetch('/static/CAMEO.eventcodes.txt')
      .then((response) => response.text())
      .then((textData) => {
        const parsedData = parseTaxonomy(textData);
        setData(parsedData);
      })
      .catch((error) => {
        console.error('Errore durante il caricamento del file:', error);
      });
  }, []);

  useEffect(() => {
    const hiddenInput = document.getElementById('selectedCodes');
    if (hiddenInput) {
      hiddenInput.value = JSON.stringify(selectedKeys); //aggiornamento campo hidden!!
    }
  }, [selectedKeys]);

  const parseTaxonomy = (textData) => {
    return textData
      .split('\n')
      .map((line) => {
        const [code, name] = line.split('\t');
        if (code && name) {
          return { code: code.trim(), name: name.trim() };
        }
        return null;
      })
      .filter(Boolean); 
  };

  const handleCheckboxChange = (event) => {
    const { value, checked } = event.target;
    if (checked) {
      setSelectedKeys((prevKeys) => [...prevKeys, value]);
    } else {
      setSelectedKeys((prevKeys) => prevKeys.filter((key) => key !== value));
    }
  };

  return (
    <>
      <NavDropdown title="Event Options" id="event-dropdown" menuVariant="dark">
        <div style={{ maxHeight: '300px', overflowY: 'auto', padding: '10px' }}>
          {data.map((item) => (
            <Form.Check
              key={item.code}
              type="checkbox"
              id={`checkbox-${item.code}`}
              label={`${item.name} (${item.code})`}
              value={item.code}
              checked={selectedKeys.includes(item.code)}
              onChange={handleCheckboxChange}
            />
          ))}
        </div>
      </NavDropdown>
      <input type="hidden" id="selectedCodes" name="selectedCodes" value="[]" /> 
    </>
  ); //L'input hidden dovrebbe mantenere i valori selezionati per poi spedirli insieme al form in POST
};

export default CameoTaxonomyNav;
