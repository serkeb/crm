// src/components/reports/Reports.jsx

import React, { useState, useEffect } from 'react';
import { supabase } from '../../lib/supabase';
import LoadingSpinner from '../ui/LoadingSpinner';

const Reports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const { data, error: fetchError } = await supabase
          .from('reports') // Nombre de tu tabla de reportes
          .select('*')
          .order('created_at', { ascending: false }); // Ordenamos para ver los más recientes primero

        if (fetchError) {
          throw fetchError;
        }
        
        setReports(data);

      } catch (err) {
        setError('No se pudieron cargar los reportes.');
        console.error("Error fetching reports:", err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <div className="text-red-500 p-4">{error}</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Reportes</h1>
      
      {reports.length > 0 ? (
        <div className="bg-white p-4 rounded shadow">
          <ul className="divide-y divide-gray-200">
            {reports.map(report => (
              <li key={report.id} className="py-3">
                <p className="font-semibold">{report.title}</p>
                <p className="text-sm text-gray-500">
                  Generado el: {new Date(report.created_at).toLocaleDateString()}
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p>No hay reportes disponibles.</p>
      )}
    </div>
  );
};

export default Reports;
