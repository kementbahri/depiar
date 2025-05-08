import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { GlobeAltIcon } from '@heroicons/react/24/outline';

// Pages
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Domains from './pages/Domains';
import EmailAccounts from './pages/EmailAccounts';
import Databases from './pages/Databases';
import FileManager from './pages/FileManager';
import DNSManagement from './pages/DNSManagement';

// Components
import Layout from './components/Layout';
import PrivateRoute from './components/PrivateRoute';

function App() {
  return (
    <Router>
      <ToastContainer position="top-right" autoClose={3000} />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="domains" element={<Domains />} />
          <Route path="emails" element={<EmailAccounts />} />
          <Route path="databases" element={<Databases />} />
          <Route path="files" element={<FileManager />} />
          <Route path="dns" element={<DNSManagement />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App; 