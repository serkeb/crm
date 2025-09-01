// src/components/tickets/Tickets.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Tickets = () => {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('tickets') // Nombre de tu tabla de tickets
          .select('*');

        if (fetchError) {
          throw fetchError;
        }
        
        setTickets(data);

      } catch (err) {
        setError('No se pudieron cargar los tickets.');
        console.error("Error fetching tickets:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Tickets de Soporte</h1>
      
      {tickets.length > 0 ? (
        <div className="bg-white p-4 rounded shadow">
          <ul className="divide-y divide-gray-200">
            {tickets.map(ticket => (
              <li key={ticket.id} className="py-3">
                <p className="font-semibold">{ticket.subject}</p>
                <p className="text-sm text-gray-500">
                  Prioridad: <span className="font-medium text-gray-800">{ticket.priority}</span>
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>No hay tickets de soporte activos.</p>
      )}
    </div>
  );
};

export default Tickets;
