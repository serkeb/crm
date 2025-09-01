// src/components/conversations/Conversations.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Conversations = () => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchConversations = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('conversations') // Nombre de tu tabla de conversaciones
          .select('*');

        if (fetchError) {
          throw fetchError;
        }
        
        setConversations(data);

      } catch (err) {
        setError('No se pudieron cargar las conversaciones.');
        console.error("Error fetching conversations:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchConversations();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Conversaciones</h1>
      
      {conversations.length > 0 ? (
        <div className="bg-white p-4 rounded shadow">
          <ul className="divide-y divide-gray-200">
            {conversations.map(conversation => (
              <li key={conversation.id} className="py-3">
                <p className="font-semibold">{conversation.subject}</p>
                <p className="text-sm text-gray-500">
                  Estado: <span className="font-medium text-gray-800">{conversation.status}</span>
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>No hay conversaciones para mostrar.</p>
      )}
    </div>
  );
};

export default Conversations;
