// src/components/contacts/Contacts.jsx (CORREGIDO)

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Contacts = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchContacts = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('contacts')
          .select('id, messenger_id, telegram_id, tags'); // Seleccionamos columnas que existen

        if (fetchError) throw fetchError;
        setContacts(data);
      } catch (err) {
        setError('No se pudieron cargar los contactos.');
        console.error("Error fetching contacts:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchContacts();
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <div className="text-red-500 p-4">{error}</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Contactos</h1>
      {contacts.length > 0 ? (
        <div className="bg-white p-4 rounded shadow">
          <ul className="divide-y divide-gray-200">
            {contacts.map(contact => (
              <li key={contact.id} className="py-3">
                <p className="font-semibold">
                  ID de Contacto: {contact.messenger_id || contact.telegram_id || contact.id}
                </p>
                <p className="text-sm text-gray-500">Tags: {contact.tags?.join(', ') || 'Sin tags'}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>No tienes ningún contacto guardado.</p>
      )}
    </div>
  );
};

export default Contacts;
