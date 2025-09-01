import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { HomeIcon, ChatBubbleLeftRightIcon, UsersIcon, TicketIcon, Cog6ToothIcon, ChartBarIcon, DocumentTextIcon, PuzzlePieceIcon, BellIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Conversaciones', href: '/conversations', icon: ChatBubbleLeftRightIcon },
  { name: 'Contactos', href: '/contacts', icon: UsersIcon },
  { name: 'Tickets', href: '/tickets', icon: TicketIcon },
  { name: 'Canales', href: '/channels', icon: BellIcon },
  { name: 'Automatizaciones', href: '/automations', icon: PuzzlePieceIcon },
  { name: 'Plantillas', href: '/templates', icon: DocumentTextIcon },
  { name: 'Reportes', href: '/reports', icon: ChartBarIcon },
  { name: 'Configuración', href: '/settings', icon: Cog6ToothIcon },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <div className="flex flex-col w-64 bg-gray-800 text-white">
      <div className="flex items-center justify-center h-16 bg-gray-900">
        <span className="text-2xl font-semibold">CRM Multicanal</span>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={`
              ${location.pathname === item.href ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}
              group flex items-center px-2 py-2 text-sm font-medium rounded-md
            `}
          >
            <item.icon
              className={`
                ${location.pathname === item.href ? 'text-gray-300' : 'text-gray-400 group-hover:text-gray-300'}
                mr-3 flex-shrink-0 h-6 w-6
              `}
              aria-hidden="true"
            />
            {item.name}
          </Link>
        ))}
      </nav>
    </div>
  );
}

