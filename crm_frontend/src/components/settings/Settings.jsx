// src/components/settings/Settings.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext'; // Usamos el contexto para obtener el usuario
import LoadingSpinner from '../ui/LoadingSpinner';

const Settings = () => {
  const { user } = useAuth(); // Obtenemos el usuario actual del contexto de autenticación

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');

  // Estados para los campos del formulario
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [company, setCompany] = useState('');

  // 1. Cargar los datos del perfil del usuario actual
  useEffect(() => {
    if (user) {
      const fetchProfile = async () => {
        try {
          const { data, error: fetchError } = await supabase
            .from('profiles') // Asumimos que tienes una tabla 'profiles'
            .select('first_name, last_name, company')
            .eq('id', user.id) // Buscamos el perfil que coincide con el ID del usuario
            .single(); // .single() para obtener un solo objeto en lugar de un array

          if (fetchError) throw fetchError;

          if (data) {
            setFirstName(data.first_name || '');
            setLastName(data.last_name || '');
            setCompany(data.company || '');
          }
        } catch (err) {
          setError('No se pudo cargar el perfil del usuario.');
          console.error("Error fetching profile:", err.message);
        } finally {
          setLoading(false);
        }
      };
      
      fetchProfile();
    }
  }, [user]); // Se ejecuta cada vez que el objeto 'user' cambia

  // 2. Función para manejar la actualización del perfil
  const handleUpdateProfile = async (e) => {
    e.preventDefault(); // Evita que la página se recargue al enviar el formulario
    setLoading(true);
    setMessage('');
    setError(null);

    try {
      const updates = {
        id: user.id,
        first_name: firstName,
        last_name: lastName,
        company,
        updated_at: new Date(),
      };

      const { error: updateError } = await supabase.from('profiles').upsert(updates);

      if (updateError) throw updateError;
      
      setMessage('¡Perfil actualizado correctamente!');

    } catch (err) {
      setError('Hubo un error al actualizar el perfil.');
      console.error("Error updating profile:", err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Ajustes del Perfil</h1>
      
      <form onSubmit={handleUpdateProfile} className="bg-white p-6 rounded-lg shadow max-w-lg">
        {error && <p className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</p>}
        {message && <p className="bg-green-100 text-green-700 p-3 rounded mb-4">{message}</p>}
        
        <div className="mb-4">
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
          <input type="email" id="email" value={user?.email || ''} disabled className="mt-1 block w-full px-3 py-2 bg-gray-100 border border-gray-300 rounded-md shadow-sm" />
        </div>

        <div className="mb-4">
          <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">Nombre</label>
          <input type="text" id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        </div>
        
        <div className="mb-4">
          <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">Apellido</label>
          <input type="text" id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        </div>

        <div className="mb-4">
          <label htmlFor="company" className="block text-sm font-medium text-gray-700">Empresa</label>
          <input type="text" id="company" value={company} onChange={(e) => setCompany(e.target.value)} className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500" />
        </div>

        <button type="submit" disabled={loading} className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400">
          {loading ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </form>
    </div>
  );
};

export default Settings;
