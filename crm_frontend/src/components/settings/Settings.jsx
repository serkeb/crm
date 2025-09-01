// src/components/settings/Settings.jsx (CORREGIDO)

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import { useAuth } from '../../contexts/AuthContext';
import LoadingSpinner from '../ui/LoadingSpinner';

const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  
  useEffect(() => {
    if (user) {
      const fetchProfile = async () => {
        try {
          // Buscamos en la tabla 'users', no 'profiles'
          const { data, error: fetchError } = await supabase
            .from('users') 
            .select('first_name, last_name')
            .eq('id', user.id)
            .single();

          if (fetchError) throw fetchError;

          if (data) {
            setFirstName(data.first_name || '');
            setLastName(data.last_name || '');
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
  }, [user]);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');
    setError(null);

    try {
      const updates = {
        id: user.id,
        first_name: firstName,
        last_name: lastName,
        updated_at: new Date(), // Asumiendo que tu tabla tiene 'updated_at'
      };

      // Actualizamos en la tabla 'users'
      const { error: updateError } = await supabase.from('users').upsert(updates);

      if (updateError) throw updateError;
      
      setMessage('¡Perfil actualizado correctamente!');
    } catch (err) {
      setError('Hubo un error al actualizar el perfil.');
      console.error("Error updating profile:", err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Ajustes del Perfil</h1>
      <form onSubmit={handleUpdateProfile} className="bg-white p-6 rounded-lg shadow max-w-lg">
        {error && <p className="bg-red-100 text-red-700 p-3 rounded mb-4">{error}</p>}
        {message && <p className="bg-green-100 text-green-700 p-3 rounded mb-4">{message}</p>}
        
        <div className="mb-4">
          <label htmlFor="email">Email</label>
          <input type="email" id="email" value={user?.email || ''} disabled className="mt-1 block w-full px-3 py-2 bg-gray-100 border rounded-md" />
        </div>

        <div className="mb-4">
          <label htmlFor="firstName">Nombre</label>
          <input type="text" id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="mt-1 block w-full px-3 py-2 border rounded-md" />
        </div>
        
        <div className="mb-4">
          <label htmlFor="lastName">Apellido</label>
          <input type="text" id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} className="mt-1 block w-full px-3 py-2 border rounded-md" />
        </div>

        <button type="submit" disabled={loading} className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 disabled:bg-gray-400">
          {loading ? 'Guardando...' : 'Guardar Cambios'}
        </button>
      </form>
    </div>
  );
};

export default Settings;
