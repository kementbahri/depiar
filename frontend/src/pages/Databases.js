import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  KeyIcon,
  DatabaseIcon,
  SearchIcon,
  SortAscendingIcon,
  RefreshIcon,
  CloudDownloadIcon,
  CloudUploadIcon,
} from '@heroicons/react/outline';

function Databases() {
  const [databases, setDatabases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    password: '',
  });
  const [backupPath, setBackupPath] = useState('');
  const [restorePath, setRestorePath] = useState('');

  useEffect(() => {
    fetchDatabases();
  }, []);

  const fetchDatabases = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/databases');
      setDatabases(response.data);
    } catch (error) {
      toast.error('Veritabanları yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleAddDatabase = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/databases', formData);
      toast.success('Veritabanı başarıyla eklendi');
      setShowAddModal(false);
      fetchDatabases();
      resetForm();
    } catch (error) {
      toast.error('Veritabanı eklenirken bir hata oluştu');
    }
  };

  const handleEditDatabase = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/databases/${selectedDatabase.id}`, formData);
      toast.success('Veritabanı başarıyla güncellendi');
      setShowEditModal(false);
      fetchDatabases();
      resetForm();
    } catch (error) {
      toast.error('Veritabanı güncellenirken bir hata oluştu');
    }
  };

  const handleDeleteDatabase = async (id) => {
    if (window.confirm('Bu veritabanını silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`/api/databases/${id}`);
        toast.success('Veritabanı başarıyla silindi');
        fetchDatabases();
      } catch (error) {
        toast.error('Veritabanı silinirken bir hata oluştu');
      }
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/databases/${selectedDatabase.id}/password`, {
        password: formData.password,
      });
      toast.success('Şifre başarıyla değiştirildi');
      setShowPasswordModal(false);
      resetForm();
    } catch (error) {
      toast.error('Şifre değiştirilirken bir hata oluştu');
    }
  };

  const handleBackup = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/databases/${selectedDatabase.id}/backup`, {
        path: backupPath,
      });
      toast.success('Veritabanı yedekleme işlemi başlatıldı');
      setShowBackupModal(false);
      setBackupPath('');
    } catch (error) {
      toast.error('Veritabanı yedeklenirken bir hata oluştu');
    }
  };

  const handleRestore = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/databases/${selectedDatabase.id}/restore`, {
        path: restorePath,
      });
      toast.success('Veritabanı geri yükleme işlemi başlatıldı');
      setShowRestoreModal(false);
      setRestorePath('');
    } catch (error) {
      toast.error('Veritabanı geri yüklenirken bir hata oluştu');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      username: '',
      password: '',
    });
  };

  const filteredDatabases = databases
    .filter(db => 
      db.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      db.username.toLowerCase().includes(searchTerm.toLowerCase())
    )
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
          <h1 className="text-2xl font-semibold text-gray-900">Veritabanları</h1>
          <p className="mt-2 text-sm text-gray-700">
            Tüm veritabanlarınızın listesi ve yönetimi
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            Yeni Veritabanı
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
              placeholder="Veritabanı ara..."
              className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        </div>
        <div className="flex gap-4">
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <SortAscendingIcon className={`h-5 w-5 mr-2 ${sortOrder === 'desc' ? 'transform rotate-180' : ''}`} />
            Sırala
          </button>
          <button
            onClick={fetchDatabases}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshIcon className="h-5 w-5 mr-2" />
            Yenile
          </button>
        </div>
      </div>

      {/* Veritabanları Listesi */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('name')}
                    >
                      Veritabanı Adı
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('username')}
                    >
                      Kullanıcı Adı
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('created_at')}
                    >
                      Oluşturulma Tarihi
                    </th>
                    <th className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">İşlemler</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {loading ? (
                    <tr>
                      <td colSpan="4" className="px-3 py-4 text-center text-sm text-gray-500">
                        Yükleniyor...
                      </td>
                    </tr>
                  ) : filteredDatabases.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-3 py-4 text-center text-sm text-gray-500">
                        Veritabanı bulunamadı
                      </td>
                    </tr>
                  ) : (
                    filteredDatabases.map((database) => (
                      <tr key={database.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <div className="flex items-center">
                            <div className="h-10 w-10 flex-shrink-0">
                              <DatabaseIcon className="h-10 w-10 text-gray-400" />
                            </div>
                            <div className="ml-4">
                              <div className="font-medium text-gray-900">{database.name}</div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {database.username}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {new Date(database.created_at).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => {
                                setSelectedDatabase(database);
                                setFormData({ password: '' });
                                setShowPasswordModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Şifre Değiştir"
                            >
                              <KeyIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDatabase(database);
                                setShowBackupModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Yedekle"
                            >
                              <CloudDownloadIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDatabase(database);
                                setShowRestoreModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Geri Yükle"
                            >
                              <CloudUploadIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedDatabase(database);
                                setFormData({
                                  name: database.name,
                                  username: database.username,
                                });
                                setShowEditModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Düzenle"
                            >
                              <PencilIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => handleDeleteDatabase(database.id)}
                              className="text-red-600 hover:text-red-900"
                              title="Sil"
                            >
                              <TrashIcon className="h-5 w-5" />
                            </button>
                          </div>
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

      {/* Yeni Veritabanı Modal */}
      {showAddModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleAddDatabase}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Yeni Veritabanı
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Veritabanı Adı
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Kullanıcı Adı
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Şifre
                      </label>
                      <input
                        type="password"
                        required
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Ekle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Veritabanı Düzenleme Modal */}
      {showEditModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleEditDatabase}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Veritabanını Düzenle
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Veritabanı Adı
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Kullanıcı Adı
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Güncelle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Şifre Değiştirme Modal */}
      {showPasswordModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleChangePassword}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Şifre Değiştir
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Yeni Şifre
                    </label>
                    <input
                      type="password"
                      required
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Değiştir
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowPasswordModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Yedekleme Modal */}
      {showBackupModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleBackup}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Veritabanı Yedekle
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Yedek Dosya Yolu
                    </label>
                    <input
                      type="text"
                      required
                      value={backupPath}
                      onChange={(e) => setBackupPath(e.target.value)}
                      placeholder="/path/to/backup.sql"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Yedekle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowBackupModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Geri Yükleme Modal */}
      {showRestoreModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleRestore}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Veritabanı Geri Yükle
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Yedek Dosya Yolu
                    </label>
                    <input
                      type="text"
                      required
                      value={restorePath}
                      onChange={(e) => setRestorePath(e.target.value)}
                      placeholder="/path/to/backup.sql"
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Geri Yükle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRestoreModal(false)}
                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                  >
                    İptal
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Databases; 