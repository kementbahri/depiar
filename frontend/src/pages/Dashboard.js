import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  GlobeAltIcon,
  MailIcon,
  DatabaseIcon,
  FolderIcon,
} from '@heroicons/react/outline';

function Dashboard() {
  const [stats, setStats] = useState({
    domains: 0,
    emails: 0,
    databases: 0,
    diskUsage: '0 MB',
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get('/api/stats');
        setStats(response.data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      }
    };

    fetchStats();
  }, []);

  const cards = [
    {
      name: 'Domains',
      value: stats.domains,
      icon: GlobeAltIcon,
      color: 'bg-blue-500',
    },
    {
      name: 'Email Accounts',
      value: stats.emails,
      icon: MailIcon,
      color: 'bg-green-500',
    },
    {
      name: 'Databases',
      value: stats.databases,
      icon: DatabaseIcon,
      color: 'bg-purple-500',
    },
    {
      name: 'Disk Usage',
      value: stats.diskUsage,
      icon: FolderIcon,
      color: 'bg-yellow-500',
    },
  ];

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map((card) => (
          <div
            key={card.name}
            className="bg-white overflow-hidden shadow rounded-lg"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className={`flex-shrink-0 rounded-md p-3 ${card.color}`}>
                  <card.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {card.name}
                    </dt>
                    <dd className="text-lg font-semibold text-gray-900">
                      {card.value}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity Section */}
      <div className="mt-8">
        <h2 className="text-lg font-medium text-gray-900">Recent Activity</h2>
        <div className="mt-4 bg-white shadow overflow-hidden sm:rounded-md">
          <ul className="divide-y divide-gray-200">
            <li className="px-6 py-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">
                  New domain added: example.com
                </p>
                <p className="text-sm text-gray-500">2 hours ago</p>
              </div>
            </li>
            <li className="px-6 py-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">
                  SSL certificate renewed for example.com
                </p>
                <p className="text-sm text-gray-500">5 hours ago</p>
              </div>
            </li>
            <li className="px-6 py-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900">
                  New email account created: info@example.com
                </p>
                <p className="text-sm text-gray-500">1 day ago</p>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Dashboard; 