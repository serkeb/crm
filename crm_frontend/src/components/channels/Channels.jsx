// src/components/channels/Channels.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Channels = () => {
  const [channels, setChannels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('channels') // Nombre de tu tabla de canales
          .select('*');

        if (fetchError) {
          throw fetchError;
        }
        
        setChannels(data);

      } catch (err) {
        setError('No se pudieron cargar los canales.');
        console.error("Error fetching channels:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchChannels();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Canales</h1>
      
      {channels.length > 0 ? (
        <ul className="bg-white p-4 rounded shadow">
          {channels.map(channel => (
            <li key={channel.id} className="border-b py-2">
              <p className="font-semibold">{channel.name}</p>
              <p className="text-sm text-gray-600">Tipo: {channel.type}</p>
            </li>
          ))}
        </ul>
      ) : (
        <p>Aún no has configurado ningún canal.</p>
      )}
    </div>
  );
};

export default Channels;
