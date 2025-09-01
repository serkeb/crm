// src/components/automations/Automations.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase'; // Importamos el cliente de Supabase
import LoadingSpinner from '../ui/LoadingSpinner'; // Un indicador de carga

const Automations = () => {
  // 1. Estados para manejar los datos, la carga y los errores
  const [automations, setAutomations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 2. useEffect se ejecuta una vez cuando el componente se monta
  useEffect(() => {
    const fetchAutomations = async () => {
      try {
        // 3. Hacemos la petición a la tabla 'automations' en Supabase
        const { data, error: fetchError } = await supabase
          .from('automations')
          .select('*');

        if (fetchError) {
          throw fetchError; // Si hay un error en la respuesta, lo lanzamos
        }
        
        setAutomations(data); // Guardamos los datos en el estado

      } catch (err) {
        setError('No se pudieron cargar las automatizaciones.');
        console.error("Error fetching automations:", err.message);
      } finally {
        setLoading(false); // Dejamos de cargar, tanto si hubo éxito como si hubo error
      }
    };

    fetchAutomations();
  }, []); // El array vacío [] asegura que se ejecute solo una vez

  // 4. Mostramos un estado de carga mientras se obtienen los datos
  if (loading) {
    return <LoadingSpinner />;
  }

  // 5. Mostramos un mensaje de error si la petición falló
  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  // 6. Mostramos los datos una vez que se han cargado correctamente
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Automatizaciones</h1>
      
      {automations.length > 0 ? (
        <ul className="bg-white p-4 rounded shadow">
          {automations.map(automation => (
            <li key={automation.id} className="border-b py-2">
              <p className="font-semibold">{automation.name}</p>
              <p className="text-sm text-gray-600">Disparador: {automation.trigger}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p>No hay automatizaciones creadas todavía.</p>
      )}
    </div>
  );
};

export default Automations;
