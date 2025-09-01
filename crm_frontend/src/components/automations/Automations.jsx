// src/components/automations/Automations.jsx (CORREGIDO)

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Automations = () => {
  const [automations, setAutomations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAutomations = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('automations')
          .select('id, last_executed, is_active'); // Seleccionamos columnas que existen

        if (fetchError) throw fetchError;
        setAutomations(data);
      } catch (err) {
        setError('No se pudieron cargar las automatizaciones.');
        console.error("Error fetching automations:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAutomations();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Automatizaciones</h1>
      {automations.length > 0 ? (
        <ul className="bg-white p-4 rounded shadow">
          {automations.map(auto => (
            <li key={auto.id} className="border-b py-2">
              <p className="font-semibold">Automatización ID: {auto.id}</p>
              <p className="text-sm text-gray-500">
                Última ejecución: {auto.last_executed ? new Date(auto.last_executed).toLocaleString() : 'Nunca'}
              </p>
            </li>
          ))}
        </ul>
      ) : (
        <p>No hay automatizaciones creadas.</p>
      )}
    </div>
  );
};

export default Automations;
