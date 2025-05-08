import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  KeyIcon,
  MailIcon,
  SearchIcon,
  SortAscendingIcon,
  RefreshIcon,
  UserIcon,
  GlobeAltIcon,
} from '@heroicons/react/outline';

function EmailAccounts() {
  const [emailAccounts, setEmailAccounts] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [domainFilter, setDomainFilter] = useState('all');
  const [sortBy, setSortBy] = useState('username');
  const [sortOrder, setSortOrder] = useState('asc');
  const [formData, setFormData] = useState({
    username: '',
    domain_id: '',
    password: '',
    quota: 1000,
  });

  useEffect(() => {
    fetchEmailAccounts();
    fetchDomains();
  }, []);

  const fetchEmailAccounts = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/emails');
      setEmailAccounts(response.data);
    } catch (error) {
      toast.error('E-posta hesapları yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const fetchDomains = async () => {
    try {
      const response = await axios.get('/api/domains');
      setDomains(response.data);
    } catch (error) {
      toast.error('Alan adları yüklenirken bir hata oluştu');
    }
  };

  const handleAddEmailAccount = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/emails', formData);
      toast.success('E-posta hesabı başarıyla eklendi');
      setShowAddModal(false);
      fetchEmailAccounts();
      resetForm();
    } catch (error) {
      toast.error('E-posta hesabı eklenirken bir hata oluştu');
    }
  };

  const handleEditEmailAccount = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/emails/${selectedAccount.id}`, formData);
      toast.success('E-posta hesabı başarıyla güncellendi');
      setShowEditModal(false);
      fetchEmailAccounts();
      resetForm();
    } catch (error) {
      toast.error('E-posta hesabı güncellenirken bir hata oluştu');
    }
  };

  const handleDeleteEmailAccount = async (id) => {
    if (window.confirm('Bu e-posta hesabını silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`/api/emails/${id}`);
        toast.success('E-posta hesabı başarıyla silindi');
        fetchEmailAccounts();
      } catch (error) {
        toast.error('E-posta hesabı silinirken bir hata oluştu');
      }
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/emails/${selectedAccount.id}/password`, {
        password: formData.password,
      });
      toast.success('Şifre başarıyla değiştirildi');
      setShowPasswordModal(false);
      resetForm();
    } catch (error) {
      toast.error('Şifre değiştirilirken bir hata oluştu');
    }
  };

  const resetForm = () => {
    setFormData({
      username: '',
      domain_id: '',
      password: '',
      quota: 1000,
    });
  };

  const getDomainName = (domainId) => {
    const domain = domains.find(d => d.id === domainId);
    return domain ? domain.name : '';
  };

  const filteredEmailAccounts = emailAccounts
    .filter(account => {
      const matchesSearch = 
        account.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        getDomainName(account.domain_id).toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesDomain = domainFilter === 'all' || account.domain_id === parseInt(domainFilter);
      
      return matchesSearch && matchesDomain;
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
          <h1 className="text-2xl font-semibold text-gray-900">E-posta Hesapları</h1>
          <p className="mt-2 text-sm text-gray-700">
            Tüm e-posta hesaplarınızın listesi ve yönetimi
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            Yeni E-posta Hesabı
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
              placeholder="E-posta hesabı ara..."
              className="focus:ring-primary-500 focus:border-primary-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
            />
          </div>
        </div>
        <div className="flex gap-4">
          <select
            value={domainFilter}
            onChange={(e) => setDomainFilter(e.target.value)}
            className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
          >
            <option value="all">Tüm Alan Adları</option>
            {domains.map(domain => (
              <option key={domain.id} value={domain.id}>
                {domain.name}
              </option>
            ))}
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <SortAscendingIcon className={`h-5 w-5 mr-2 ${sortOrder === 'desc' ? 'transform rotate-180' : ''}`} />
            Sırala
          </button>
          <button
            onClick={fetchEmailAccounts}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshIcon className="h-5 w-5 mr-2" />
            Yenile
          </button>
        </div>
      </div>

      {/* E-posta Hesapları Listesi */}
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
                      onClick={() => setSortBy('username')}
                    >
                      E-posta Hesabı
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('domain_id')}
                    >
                      Alan Adı
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('quota')}
                    >
                      Kota
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
                      <td colSpan="5" className="px-3 py-4 text-center text-sm text-gray-500">
                        Yükleniyor...
                      </td>
                    </tr>
                  ) : filteredEmailAccounts.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-3 py-4 text-center text-sm text-gray-500">
                        E-posta hesabı bulunamadı
                      </td>
                    </tr>
                  ) : (
                    filteredEmailAccounts.map((account) => (
                      <tr key={account.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <div className="flex items-center">
                            <div className="h-10 w-10 flex-shrink-0">
                              <UserIcon className="h-10 w-10 text-gray-400" />
                            </div>
                            <div className="ml-4">
                              <div className="font-medium text-gray-900">{account.username}</div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <div className="flex items-center">
                            <GlobeAltIcon className="h-5 w-5 mr-2 text-gray-400" />
                            {getDomainName(account.domain_id)}
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {account.quota} MB
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {new Date(account.created_at).toLocaleDateString('tr-TR')}
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => {
                                setSelectedAccount(account);
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
                                setSelectedAccount(account);
                                setFormData({
                                  username: account.username,
                                  domain_id: account.domain_id,
                                  quota: account.quota,
                                });
                                setShowEditModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Düzenle"
                            >
                              <PencilIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => handleDeleteEmailAccount(account.id)}
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

      {/* Yeni E-posta Hesabı Modal */}
      {showAddModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleAddEmailAccount}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Yeni E-posta Hesabı
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
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
                        Alan Adı
                      </label>
                      <select
                        required
                        value={formData.domain_id}
                        onChange={(e) => setFormData({ ...formData, domain_id: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      >
                        <option value="">Seçiniz</option>
                        {domains.map(domain => (
                          <option key={domain.id} value={domain.id}>
                            {domain.name}
                          </option>
                        ))}
                      </select>
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

                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Kota (MB)
                      </label>
                      <input
                        type="number"
                        required
                        min="100"
                        step="100"
                        value={formData.quota}
                        onChange={(e) => setFormData({ ...formData, quota: parseInt(e.target.value) })}
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

      {/* E-posta Hesabı Düzenleme Modal */}
      {showEditModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleEditEmailAccount}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    E-posta Hesabını Düzenle
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
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
                        Alan Adı
                      </label>
                      <select
                        required
                        value={formData.domain_id}
                        onChange={(e) => setFormData({ ...formData, domain_id: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      >
                        {domains.map(domain => (
                          <option key={domain.id} value={domain.id}>
                            {domain.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Kota (MB)
                      </label>
                      <input
                        type="number"
                        required
                        min="100"
                        step="100"
                        value={formData.quota}
                        onChange={(e) => setFormData({ ...formData, quota: parseInt(e.target.value) })}
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
    </div>
  );
}

export default EmailAccounts; 