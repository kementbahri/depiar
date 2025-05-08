import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  ShieldExclamationIcon,
  SearchIcon,
  SortAscendingIcon,
  RefreshIcon,
  FolderIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  ExclamationCircleIcon,
  BanIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/outline';
import Modal from '../components/Modal';

function Domains() {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sslFilter, setSslFilter] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [formData, setFormData] = useState({
    name: '',
    php_version: '8.1',
    server_type: 'apache',
    ssl_enabled: true
  });
  const [showSSLModal, setShowSSLModal] = useState(false);
  const [selectedDomainForSSL, setSelectedDomainForSSL] = useState(null);
  const [sslLoading, setSslLoading] = useState(false);
  const [showFTPModal, setShowFTPModal] = useState(false);
  const [selectedDomainForFTP, setSelectedDomainForFTP] = useState(null);
  const [ftpAccounts, setFTPAccounts] = useState([]);
  const [ftpLoading, setFTPLoading] = useState(false);
  const [ftpFormData, setFTPFormData] = useState({
    username: '',
    password: '',
    home_directory: '/'
  });
  const [showTasksModal, setShowTasksModal] = useState(false);
  const [showBackupsModal, setShowBackupsModal] = useState(false);
  const [selectedDomainForTasks, setSelectedDomainForTasks] = useState(null);
  const [selectedDomainForBackups, setSelectedDomainForBackups] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [backups, setBackups] = useState([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [backupsLoading, setBackupsLoading] = useState(false);
  const [taskFormData, setTaskFormData] = useState({
    name: '',
    command: '',
    schedule: ''
  });
  const [backupFormData, setBackupFormData] = useState({
    name: '',
    type: 'full',
    schedule: ''
  });
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [selectedDomainForLogs, setSelectedDomainForLogs] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [logFilters, setLogFilters] = useState({
    type: '',
    source: '',
    startDate: '',
    endDate: ''
  });
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [wsConnection, setWsConnection] = useState(null);
  const [showSuspendModal, setShowSuspendModal] = useState(false);
  const [selectedDomainForSuspension, setSelectedDomainForSuspension] = useState(null);
  const [suspensionReason, setSuspensionReason] = useState('');
  const [suspensionLoading, setSuspensionLoading] = useState(false);

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/domains');
      setDomains(response.data);
    } catch (error) {
      toast.error('Alan adları yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleAddDomain = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/domains', formData);
      toast.success('Alan adı başarıyla eklendi');
      setShowAddModal(false);
      fetchDomains();
      resetForm();
    } catch (error) {
      toast.error('Alan adı eklenirken bir hata oluştu');
    }
  };

  const handleEditDomain = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/domains/${selectedDomain.id}`, formData);
      toast.success('Alan adı başarıyla güncellendi');
      setShowEditModal(false);
      fetchDomains();
      resetForm();
    } catch (error) {
      toast.error('Alan adı güncellenirken bir hata oluştu');
    }
  };

  const handleDeleteDomain = async (id) => {
    if (window.confirm('Bu alan adını silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`/api/domains/${id}`);
        toast.success('Alan adı başarıyla silindi');
        fetchDomains();
      } catch (error) {
        toast.error('Alan adı silinirken bir hata oluştu');
      }
    }
  };

  const handleEnableSSL = async (id) => {
    try {
      await axios.post(`/api/domains/${id}/ssl`);
      toast.success('SSL sertifikası başarıyla etkinleştirildi');
      fetchDomains();
    } catch (error) {
      toast.error('SSL sertifikası etkinleştirilirken bir hata oluştu');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      php_version: '8.1',
      server_type: 'apache',
      ssl_enabled: true
    });
  };

  const handleSSLManagement = async (domain) => {
    setSelectedDomainForSSL(domain);
    setShowSSLModal(true);
  };

  const handleSSLInstall = async () => {
    try {
      setSslLoading(true);
      await axios.post(`/api/ssl/install/${selectedDomainForSSL.id}`);
      toast.success('SSL sertifikası başarıyla yüklendi');
      fetchDomains();
      setShowSSLModal(false);
    } catch (error) {
      toast.error('SSL sertifikası yüklenirken bir hata oluştu');
    } finally {
      setSslLoading(false);
    }
  };

  const handleSSLRemove = async () => {
    if (window.confirm('SSL sertifikasını kaldırmak istediğinizden emin misiniz?')) {
      try {
        setSslLoading(true);
        await axios.delete(`/api/ssl/${selectedDomainForSSL.id}`);
        toast.success('SSL sertifikası başarıyla kaldırıldı');
        fetchDomains();
        setShowSSLModal(false);
      } catch (error) {
        toast.error('SSL sertifikası kaldırılırken bir hata oluştu');
      } finally {
        setSslLoading(false);
      }
    }
  };

  const handleFTPManagement = async (domain) => {
    setSelectedDomainForFTP(domain);
    setShowFTPModal(true);
    fetchFTPAccounts(domain.id);
  };

  const fetchFTPAccounts = async (domainId) => {
    try {
      setFTPLoading(true);
      const response = await axios.get(`/api/domains/${domainId}/ftp`);
      setFTPAccounts(response.data);
    } catch (error) {
      toast.error('FTP hesapları yüklenirken bir hata oluştu');
    } finally {
      setFTPLoading(false);
    }
  };

  const handleAddFTPAccount = async (e) => {
    e.preventDefault();
    try {
      setFTPLoading(true);
      await axios.post(`/api/domains/${selectedDomainForFTP.id}/ftp`, ftpFormData);
      toast.success('FTP hesabı başarıyla oluşturuldu');
      setFTPFormData({
        username: '',
        password: '',
        home_directory: '/'
      });
      fetchFTPAccounts(selectedDomainForFTP.id);
    } catch (error) {
      toast.error('FTP hesabı oluşturulurken bir hata oluştu');
    } finally {
      setFTPLoading(false);
    }
  };

  const handleDeleteFTPAccount = async (accountId) => {
    if (window.confirm('Bu FTP hesabını silmek istediğinizden emin misiniz?')) {
      try {
        setFTPLoading(true);
        await axios.delete(`/api/domains/${selectedDomainForFTP.id}/ftp/${accountId}`);
        toast.success('FTP hesabı başarıyla silindi');
        fetchFTPAccounts(selectedDomainForFTP.id);
      } catch (error) {
        toast.error('FTP hesabı silinirken bir hata oluştu');
      } finally {
        setFTPLoading(false);
      }
    }
  };

  const handleTasksManagement = async (domain) => {
    setSelectedDomainForTasks(domain);
    setShowTasksModal(true);
    fetchTasks(domain.id);
  };

  const handleBackupsManagement = async (domain) => {
    setSelectedDomainForBackups(domain);
    setShowBackupsModal(true);
    fetchBackups(domain.id);
  };

  const fetchTasks = async (domainId) => {
    try {
      setTasksLoading(true);
      const response = await axios.get(`/api/domains/${domainId}/tasks`);
      setTasks(response.data);
    } catch (error) {
      toast.error('Zamanlanmış görevler yüklenirken bir hata oluştu');
    } finally {
      setTasksLoading(false);
    }
  };

  const fetchBackups = async (domainId) => {
    try {
      setBackupsLoading(true);
      const response = await axios.get(`/api/domains/${domainId}/backups`);
      setBackups(response.data);
    } catch (error) {
      toast.error('Yedekler yüklenirken bir hata oluştu');
    } finally {
      setBackupsLoading(false);
    }
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    try {
      setTasksLoading(true);
      await axios.post(`/api/domains/${selectedDomainForTasks.id}/tasks`, taskFormData);
      toast.success('Zamanlanmış görev başarıyla oluşturuldu');
      setTaskFormData({
        name: '',
        command: '',
        schedule: ''
      });
      fetchTasks(selectedDomainForTasks.id);
    } catch (error) {
      toast.error('Zamanlanmış görev oluşturulurken bir hata oluştu');
    } finally {
      setTasksLoading(false);
    }
  };

  const handleAddBackup = async (e) => {
    e.preventDefault();
    try {
      setBackupsLoading(true);
      await axios.post(`/api/domains/${selectedDomainForBackups.id}/backups`, backupFormData);
      toast.success('Yedekleme işlemi başlatıldı');
      setBackupFormData({
        name: '',
        type: 'full',
        schedule: ''
      });
      fetchBackups(selectedDomainForBackups.id);
    } catch (error) {
      toast.error('Yedekleme işlemi başlatılırken bir hata oluştu');
    } finally {
      setBackupsLoading(false);
    }
  };

  const handleDeleteTask = async (taskId) => {
    if (window.confirm('Bu zamanlanmış görevi silmek istediğinizden emin misiniz?')) {
      try {
        setTasksLoading(true);
        await axios.delete(`/api/domains/${selectedDomainForTasks.id}/tasks/${taskId}`);
        toast.success('Zamanlanmış görev başarıyla silindi');
        fetchTasks(selectedDomainForTasks.id);
      } catch (error) {
        toast.error('Zamanlanmış görev silinirken bir hata oluştu');
      } finally {
        setTasksLoading(false);
      }
    }
  };

  const handleDeleteBackup = async (backupId) => {
    if (window.confirm('Bu yedeği silmek istediğinizden emin misiniz?')) {
      try {
        setBackupsLoading(true);
        await axios.delete(`/api/domains/${selectedDomainForBackups.id}/backups/${backupId}`);
        toast.success('Yedek başarıyla silindi');
        fetchBackups(selectedDomainForBackups.id);
      } catch (error) {
        toast.error('Yedek silinirken bir hata oluştu');
      } finally {
        setBackupsLoading(false);
      }
    }
  };

  const handleLogsManagement = async (domain) => {
    setSelectedDomainForLogs(domain);
    setShowLogsModal(true);
    fetchLogs(domain.id);
    connectWebSocket(domain.id);
  };

  const fetchLogs = async (domainId) => {
    try {
      setLogsLoading(true);
      const params = new URLSearchParams();
      if (logFilters.type) params.append('type', logFilters.type);
      if (logFilters.source) params.append('source', logFilters.source);
      if (logFilters.startDate) params.append('start_date', logFilters.startDate);
      if (logFilters.endDate) params.append('end_date', logFilters.endDate);
      
      const response = await axios.get(`/api/domains/${domainId}/logs?${params.toString()}`);
      setLogs(response.data);
    } catch (error) {
      toast.error('Günlükler yüklenirken bir hata oluştu');
    } finally {
      setLogsLoading(false);
    }
  };

  const connectWebSocket = (domainId) => {
    const ws = new WebSocket(`ws://${window.location.host}/api/ws/domains/${domainId}/logs`);
    
    ws.onmessage = (event) => {
      const newLogs = JSON.parse(event.data);
      setLogs(newLogs);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Gerçek zamanlı güncelleme bağlantısı kesildi');
    };
    
    setWsConnection(ws);
    
    return () => {
      if (ws) {
        ws.close();
      }
    };
  };

  useEffect(() => {
    return () => {
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, [wsConnection]);

  const handleSuspendDomain = async () => {
    try {
      setSuspensionLoading(true);
      await axios.post(`/api/domains/${selectedDomainForSuspension.id}/suspend`, {
        reason: suspensionReason
      });
      toast.success('Domain başarıyla askıya alındı');
      setShowSuspendModal(false);
      fetchDomains();
    } catch (error) {
      toast.error('Domain askıya alınırken bir hata oluştu');
    } finally {
      setSuspensionLoading(false);
    }
  };

  const handleUnsuspendDomain = async (domainId) => {
    if (window.confirm('Bu domaini askıdan kaldırmak istediğinizden emin misiniz?')) {
      try {
        setSuspensionLoading(true);
        await axios.post(`/api/domains/${domainId}/unsuspend`);
        toast.success('Domain başarıyla askıdan kaldırıldı');
        fetchDomains();
      } catch (error) {
        toast.error('Domain askıdan kaldırılırken bir hata oluştu');
      } finally {
        setSuspensionLoading(false);
      }
    }
  };

  const filteredDomains = domains
    .filter(domain => {
      const matchesSearch = domain.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesSSL = sslFilter === 'all' || 
        (sslFilter === 'enabled' && domain.ssl_enabled) || 
        (sslFilter === 'disabled' && !domain.ssl_enabled);
      
      return matchesSearch && matchesSSL;
    })
    .sort((a, b) => {
      const aValue = a[sortBy]?.toLowerCase() || '';
      const bValue = b[sortBy]?.toLowerCase() || '';
      return sortOrder === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    });

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Alan Adları</h1>
          <p className="mt-2 text-sm text-gray-700">
            Tüm alan adlarınızın listesi ve yönetimi
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            Yeni Alan Adı
          </button>
        </div>
      </div>

      {/* Filtreler ve Arama */}
      <div className="mt-8 flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <SearchIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Alan adı ara..."
              className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        </div>
        <div className="flex gap-4">
          <select
            value={sslFilter}
            onChange={(e) => setSslFilter(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
          >
            <option value="all">Tüm SSL Durumları</option>
            <option value="enabled">SSL Aktif</option>
            <option value="disabled">SSL Pasif</option>
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <SortAscendingIcon className={`h-5 w-5 mr-2 ${sortOrder === 'desc' ? 'transform rotate-180' : ''}`} />
            Sırala
          </button>
          <button
            onClick={fetchDomains}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshIcon className="h-5 w-5 mr-2" />
            Yenile
          </button>
        </div>
      </div>

      {/* Alan Adları Listesi */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Domain Name
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      PHP Version
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Server Type
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      SSL Status
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr>
                      <td colSpan="4" className="px-3 py-4 text-center text-sm text-gray-500">
                        Yükleniyor...
                      </td>
                    </tr>
                  ) : filteredDomains.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-3 py-4 text-center text-sm text-gray-500">
                        Alan adı bulunamadı
                      </td>
                    </tr>
                  ) : (
                    filteredDomains.map((domain) => (
                      <tr key={domain.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {domain.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          PHP {domain.php_version}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {domain.server_type.charAt(0).toUpperCase() + domain.server_type.slice(1)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {domain.ssl_enabled ? (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              <ShieldCheckIcon className="h-4 w-4 mr-1" />
                              Active
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              <ShieldExclamationIcon className="h-4 w-4 mr-1" />
                              Inactive
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            domain.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {domain.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleTasksManagement(domain)}
                            className="text-purple-600 hover:text-purple-900 mr-4"
                          >
                            <ClockIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleBackupsManagement(domain)}
                            className="text-orange-600 hover:text-orange-900 mr-4"
                          >
                            <DocumentDuplicateIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleFTPManagement(domain)}
                            className="text-green-600 hover:text-green-900 mr-4"
                          >
                            FTP
                          </button>
                          <button
                            onClick={() => handleSSLManagement(domain)}
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            SSL
                          </button>
                          <button
                            onClick={() => handleLogsManagement(domain)}
                            className="text-red-600 hover:text-red-900 mr-4"
                          >
                            <ExclamationCircleIcon className="h-5 w-5" />
                          </button>
                          {domain.status === 'suspended' ? (
                            <button
                              onClick={() => handleUnsuspendDomain(domain.id)}
                              className="text-green-600 hover:text-green-900 mr-4"
                              disabled={suspensionLoading}
                            >
                              <BanIcon className="h-5 w-5" />
                            </button>
                          ) : (
                            <button
                              onClick={() => {
                                setSelectedDomainForSuspension(domain);
                                setShowSuspendModal(true);
                              }}
                              className="text-red-600 hover:text-red-900 mr-4"
                            >
                              <BanIcon className="h-5 w-5" />
                            </button>
                          )}
                          <button
                            onClick={() => handleEditDomain(domain)}
                            className="text-indigo-600 hover:text-indigo-900 mr-4"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteDomain(domain.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      {/* Add Domain Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          setFormData({
            name: '',
            php_version: '8.1',
            server_type: 'apache',
            ssl_enabled: true
          });
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Add New Domain</h3>
          <form onSubmit={handleAddDomain}>
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Domain Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="example.com"
                  required
                />
              </div>

              <div>
                <label htmlFor="php_version" className="block text-sm font-medium text-gray-700">
                  PHP Version
                </label>
                <select
                  id="php_version"
                  value={formData.php_version}
                  onChange={(e) => setFormData({ ...formData, php_version: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="8.2">PHP 8.2</option>
                  <option value="8.1">PHP 8.1</option>
                  <option value="8.0">PHP 8.0</option>
                  <option value="7.4">PHP 7.4</option>
                  <option value="7.3">PHP 7.3</option>
                </select>
              </div>

              <div>
                <label htmlFor="server_type" className="block text-sm font-medium text-gray-700">
                  Server Type
                </label>
                <select
                  id="server_type"
                  value={formData.server_type}
                  onChange={(e) => setFormData({ ...formData, server_type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="apache">Apache</option>
                  <option value="nginx">Nginx</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="ssl_enabled"
                  checked={formData.ssl_enabled}
                  onChange={(e) => setFormData({ ...formData, ssl_enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="ssl_enabled" className="ml-2 block text-sm text-gray-700">
                  Enable SSL
                </label>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false);
                  setFormData({
                    name: '',
                    php_version: '8.1',
                    server_type: 'apache',
                    ssl_enabled: true
                  });
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Add Domain
              </button>
            </div>
          </form>
        </div>
      </Modal>

      {/* Edit Domain Modal */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setFormData({
            name: '',
            php_version: '8.1',
            server_type: 'apache',
            ssl_enabled: true
          });
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Edit Domain</h3>
          <form onSubmit={handleEditDomain}>
            <div className="space-y-4">
              <div>
                <label htmlFor="edit_name" className="block text-sm font-medium text-gray-700">
                  Domain Name
                </label>
                <input
                  type="text"
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="example.com"
                  required
                />
              </div>

              <div>
                <label htmlFor="edit_php_version" className="block text-sm font-medium text-gray-700">
                  PHP Version
                </label>
                <select
                  id="edit_php_version"
                  value={formData.php_version}
                  onChange={(e) => setFormData({ ...formData, php_version: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="8.2">PHP 8.2</option>
                  <option value="8.1">PHP 8.1</option>
                  <option value="8.0">PHP 8.0</option>
                  <option value="7.4">PHP 7.4</option>
                  <option value="7.3">PHP 7.3</option>
                </select>
              </div>

              <div>
                <label htmlFor="edit_server_type" className="block text-sm font-medium text-gray-700">
                  Server Type
                </label>
                <select
                  id="edit_server_type"
                  value={formData.server_type}
                  onChange={(e) => setFormData({ ...formData, server_type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="apache">Apache</option>
                  <option value="nginx">Nginx</option>
                </select>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="edit_ssl_enabled"
                  checked={formData.ssl_enabled}
                  onChange={(e) => setFormData({ ...formData, ssl_enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="edit_ssl_enabled" className="ml-2 block text-sm text-gray-700">
                  Enable SSL
                </label>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false);
                  setFormData({
                    name: '',
                    php_version: '8.1',
                    server_type: 'apache',
                    ssl_enabled: true
                  });
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Save Changes
              </button>
            </div>
          </form>
        </div>
      </Modal>

      {/* SSL Yönetim Modalı */}
      <Modal
        isOpen={showSSLModal}
        onClose={() => {
          setShowSSLModal(false);
          setSelectedDomainForSSL(null);
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            SSL Sertifika Yönetimi - {selectedDomainForSSL?.name}
          </h3>
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-md">
              <p className="text-sm text-gray-600">
                {selectedDomainForSSL?.ssl_enabled
                  ? 'Bu domain için SSL sertifikası aktif durumda.'
                  : 'Bu domain için SSL sertifikası bulunmuyor.'}
              </p>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowSSLModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                İptal
              </button>
              {selectedDomainForSSL?.ssl_enabled ? (
                <button
                  type="button"
                  onClick={handleSSLRemove}
                  disabled={sslLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  {sslLoading ? 'İşleniyor...' : 'SSL Sertifikasını Kaldır'}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleSSLInstall}
                  disabled={sslLoading}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {sslLoading ? 'İşleniyor...' : 'SSL Sertifikası Yükle'}
                </button>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {/* FTP Yönetim Modalı */}
      <Modal
        isOpen={showFTPModal}
        onClose={() => {
          setShowFTPModal(false);
          setSelectedDomainForFTP(null);
          setFTPAccounts([]);
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            FTP Hesap Yönetimi - {selectedDomainForFTP?.name}
          </h3>
          
          {/* Yeni FTP Hesabı Formu */}
          <form onSubmit={handleAddFTPAccount} className="mb-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="ftp_username" className="block text-sm font-medium text-gray-700">
                  Kullanıcı Adı
                </label>
                <input
                  type="text"
                  id="ftp_username"
                  value={ftpFormData.username}
                  onChange={(e) => setFTPFormData({ ...ftpFormData, username: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="ftp_password" className="block text-sm font-medium text-gray-700">
                  Şifre
                </label>
                <input
                  type="password"
                  id="ftp_password"
                  value={ftpFormData.password}
                  onChange={(e) => setFTPFormData({ ...ftpFormData, password: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="ftp_home_directory" className="block text-sm font-medium text-gray-700">
                  Ana Dizin
                </label>
                <input
                  type="text"
                  id="ftp_home_directory"
                  value={ftpFormData.home_directory}
                  onChange={(e) => setFTPFormData({ ...ftpFormData, home_directory: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                type="submit"
                disabled={ftpLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {ftpLoading ? 'İşleniyor...' : 'FTP Hesabı Ekle'}
              </button>
            </div>
          </form>
          
          {/* FTP Hesapları Listesi */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Mevcut FTP Hesapları</h4>
            {ftpLoading ? (
              <p className="text-sm text-gray-500">Yükleniyor...</p>
            ) : ftpAccounts.length === 0 ? (
              <p className="text-sm text-gray-500">Henüz FTP hesabı bulunmuyor</p>
            ) : (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kullanıcı Adı
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Ana Dizin
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Durum
                      </th>
                      <th scope="col" className="relative px-6 py-3">
                        <span className="sr-only">İşlemler</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {ftpAccounts.map((account) => (
                      <tr key={account.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {account.username}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {account.home_directory}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            account.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {account.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleDeleteFTPAccount(account.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <TrashIcon className="h-5 w-5" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={() => {
                setShowFTPModal(false);
                setSelectedDomainForFTP(null);
                setFTPAccounts([]);
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Kapat
            </button>
          </div>
        </div>
      </Modal>

      {/* Zamanlanmış Görevler Modalı */}
      <Modal
        isOpen={showTasksModal}
        onClose={() => {
          setShowTasksModal(false);
          setSelectedDomainForTasks(null);
          setTasks([]);
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Zamanlanmış Görevler - {selectedDomainForTasks?.name}
          </h3>
          
          {/* Yeni Görev Formu */}
          <form onSubmit={handleAddTask} className="mb-6">
            <div className="space-y-4">
              <div>
                <label htmlFor="task_name" className="block text-sm font-medium text-gray-700">
                  Görev Adı
                </label>
                <input
                  type="text"
                  id="task_name"
                  value={taskFormData.name}
                  onChange={(e) => setTaskFormData({ ...taskFormData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="task_command" className="block text-sm font-medium text-gray-700">
                  Komut
                </label>
                <input
                  type="text"
                  id="task_command"
                  value={taskFormData.command}
                  onChange={(e) => setTaskFormData({ ...taskFormData, command: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
              
              <div>
                <label htmlFor="task_schedule" className="block text-sm font-medium text-gray-700">
                  Zamanlama (Cron)
                </label>
                <input
                  type="text"
                  id="task_schedule"
                  value={taskFormData.schedule}
                  onChange={(e) => setTaskFormData({ ...taskFormData, schedule: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="* * * * *"
                  required
                />
              </div>
            </div>
            
            <div className="mt-4 flex justify-end">
              <button
                type="submit"
                disabled={tasksLoading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                {tasksLoading ? 'İşleniyor...' : 'Görev Ekle'}
              </button>
            </div>
          </form>
          
          {/* Görevler Listesi */}
          <div className="mt-6">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Mevcut Görevler</h4>
            {tasksLoading ? (
              <p className="text-sm text-gray-500">Yükleniyor...</p>
            ) : logs.length === 0 ? (
              <p className="text-sm text-gray-500">Henüz günlük bulunmuyor</p>
            ) : (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tarih
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tip
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kaynak
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Mesaj
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            log.type === 'error' ? 'bg-red-100 text-red-800' :
                            log.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {log.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {log.source}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {log.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={() => {
                setShowTasksModal(false);
                setSelectedDomainForTasks(null);
                setLogs([]);
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Kapat
            </button>
          </div>
        </div>
      </Modal>

      {/* Günlükler Modalı */}
      <Modal
        isOpen={showLogsModal}
        onClose={() => {
          setShowLogsModal(false);
          setSelectedDomainForLogs(null);
          setLogs([]);
          if (wsConnection) {
            wsConnection.close();
          }
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Domain Günlükleri - {selectedDomainForLogs?.name}
          </h3>
          
          {/* Filtreler */}
          <div className="mb-6 grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="log_type" className="block text-sm font-medium text-gray-700">
                Log Tipi
              </label>
              <select
                id="log_type"
                value={logFilters.type}
                onChange={(e) => setLogFilters({ ...logFilters, type: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tümü</option>
                <option value="error">Hata</option>
                <option value="warning">Uyarı</option>
                <option value="info">Bilgi</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="log_source" className="block text-sm font-medium text-gray-700">
                Kaynak
              </label>
              <select
                id="log_source"
                value={logFilters.source}
                onChange={(e) => setLogFilters({ ...logFilters, source: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                <option value="">Tümü</option>
                <option value="apache">Apache</option>
                <option value="nginx">Nginx</option>
                <option value="php">PHP</option>
                <option value="mysql">MySQL</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">
                Başlangıç Tarihi
              </label>
              <input
                type="datetime-local"
                id="start_date"
                value={logFilters.startDate}
                onChange={(e) => setLogFilters({ ...logFilters, startDate: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
            
            <div>
              <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">
                Bitiş Tarihi
              </label>
              <input
                type="datetime-local"
                id="end_date"
                value={logFilters.endDate}
                onChange={(e) => setLogFilters({ ...logFilters, endDate: e.target.value })}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
            </div>
          </div>
          
          {/* Filtre ve Yenileme Butonları */}
          <div className="mb-4 flex justify-between items-center">
            <button
              onClick={() => fetchLogs(selectedDomainForLogs.id)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Filtrele
            </button>
            
            <div className="flex items-center">
              <label className="inline-flex items-center">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-600">Otomatik Yenile</span>
              </label>
            </div>
          </div>
          
          {/* Günlükler Listesi */}
          <div className="mt-6">
            {logsLoading ? (
              <p className="text-sm text-gray-500">Yükleniyor...</p>
            ) : logs.length === 0 ? (
              <p className="text-sm text-gray-500">Henüz günlük bulunmuyor</p>
            ) : (
              <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                <table className="min-w-full divide-y divide-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tarih
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Tip
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Kaynak
                      </th>
                      <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Mesaj
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            log.type === 'error' ? 'bg-red-100 text-red-800' :
                            log.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {log.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {log.source}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {log.message}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          <div className="mt-6 flex justify-end">
            <button
              type="button"
              onClick={() => {
                setShowLogsModal(false);
                setSelectedDomainForLogs(null);
                setLogs([]);
                if (wsConnection) {
                  wsConnection.close();
                }
              }}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Kapat
            </button>
          </div>
        </div>
      </Modal>

      {/* Askıya Alma Modalı */}
      <Modal
        isOpen={showSuspendModal}
        onClose={() => {
          setShowSuspendModal(false);
          setSelectedDomainForSuspension(null);
          setSuspensionReason('');
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Domain Askıya Alma - {selectedDomainForSuspension?.name}
          </h3>
          
          <div className="space-y-4">
            <div>
    </div>
  );
}

export default Domains; 