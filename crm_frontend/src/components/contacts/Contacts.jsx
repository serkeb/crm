import React from 'react';
import { supabase } from '../../lib/supabase'; // Importamos el cliente
import LoadingSpinner from '../ui/LoadingSpinner'; // Usamos un spinner de carga

const Contacts = () => {
  return (
    <div>
      <h1>Contactos</h1>
      <p>Aquí se gestionarán tus contactos.</p>
    </div>
  );
};

export default Contacts;

