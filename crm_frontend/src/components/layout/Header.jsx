import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

export default function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white border-b-4 border-blue-600">
      <div className="flex items-center">
        <h2 className="text-2xl font-semibold text-gray-700">Dashboard</h2>
      </div>

      <div className="flex items-center">
        <span className="mr-4 text-gray-800">Hola, {user?.first_name || 'Usuario'}</span>
        <button
          onClick={logout}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
        >
          Cerrar Sesión
        </button>
      </div>
    </header>
  );
}

