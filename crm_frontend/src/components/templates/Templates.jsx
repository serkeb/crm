// src/components/templates/Templates.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Templates = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('templates') // Nombre de tu tabla de plantillas
          .select('*');

        if (fetchError) {
          throw fetchError;
        }
        
        setTemplates(data);

      } catch (err) {
        setError('No se pudieron cargar las plantillas.');
        console.error("Error fetching templates:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Plantillas de Mensajes</h1>
      
      {templates.length > 0 ? (
        <div className="bg-white p-4 rounded shadow">
          <ul className="divide-y divide-gray-200">
            {templates.map(template => (
              <li key={template.id} className="py-3">
                <p className="font-semibold">{template.name}</p>
                <p className="text-sm text-gray-600 truncate">{template.body}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>No has creado ninguna plantilla todavía.</p>
      )}
    </div>
  );
};

export default Templates;
