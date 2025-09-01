// src/components/dashboard/Dashboard.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Dashboard = () => {
  const [stats, setStats] = useState({
    contacts: 0,
    tickets: 0,
    conversations: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        // Usamos Promise.all para ejecutar todas las peticiones en paralelo
        const [contactsRes, ticketsRes, conversationsRes] = await Promise.all([
          supabase.from('contacts').select('*', { count: 'exact', head: true }),
          supabase.from('tickets').select('*', { count: 'exact', head: true }),
          supabase.from('conversations').select('*', { count: 'exact', head: true })
        ]);

        // Verificamos si hubo algún error en las respuestas
        if (contactsRes.error) throw contactsRes.error;
        if (ticketsRes.error) throw ticketsRes.error;
        if (conversationsRes.error) throw conversationsRes.error;

        // Actualizamos el estado con la cuenta de cada tabla
        setStats({
          contacts: contactsRes.count,
          tickets: ticketsRes.count,
          conversations: conversationsRes.count,
        });

      } catch (err) {
        setError('No se pudo cargar la información del dashboard.');
        console.error("Error fetching dashboard stats:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardStats();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        {/* Card de Contactos */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-600">Total de Contactos</h2>
          <p className="text-3xl font-bold mt-2">{stats.contacts}</p>
        </div>

        {/* Card de Tickets */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-600">Tickets Activos</h2>
          <p className="text-3xl font-bold mt-2">{stats.tickets}</p>
        </div>

        {/* Card de Conversaciones */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-lg font-semibold text-gray-600">Conversaciones</h2>
          <p className="text-3xl font-bold mt-2">{stats.conversations}</p>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
