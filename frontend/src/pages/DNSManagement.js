import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/outline';
import Modal from '../components/Modal';

function DNSManagement() {
  const [domains, setDomains] = useState([]);
  const [selectedDomain, setSelectedDomain] = useState(null);
  const [dnsRecords, setDNSRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'A',
    content: '',
    ttl: 3600,
    priority: null
  });

  useEffect(() => {
    fetchDomains();
  }, []);

  const fetchDomains = async () => {
    try {
      const response = await axios.get('/api/domains');
      setDomains(response.data);
      if (response.data.length > 0) {
        setSelectedDomain(response.data[0]);
        fetchDNSRecords(response.data[0].id);
      }
    } catch (error) {
      toast.error('Domain listesi yüklenirken bir hata oluştu');
    }
  };

  const fetchDNSRecords = async (domainId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/domains/${domainId}/dns`);
      setDNSRecords(response.data);
    } catch (error) {
      toast.error('DNS kayıtları yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleDomainChange = (domain) => {
    setSelectedDomain(domain);
    fetchDNSRecords(domain.id);
  };

  const handleAddRecord = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`/api/domains/${selectedDomain.id}/dns`, formData);
      toast.success('DNS kaydı başarıyla eklendi');
      setShowAddModal(false);
      fetchDNSRecords(selectedDomain.id);
      resetForm();
    } catch (error) {
      toast.error('DNS kaydı eklenirken bir hata oluştu');
    }
  };

  const handleEditRecord = async (e) => {
    e.preventDefault();
    try {
      await axios.put(
        `//api/domains/${selectedDomain.id}/dns/${selectedRecord.id}`,
        formData
      );
      toast.success('DNS kaydı başarıyla güncellendi');
      setShowEditModal(false);
      fetchDNSRecords(selectedDomain.id);
      resetForm();
    } catch (error) {
      toast.error('DNS kaydı güncellenirken bir hata oluştu');
    }
  };

  const handleDeleteRecord = async (recordId) => {
    if (window.confirm('Bu DNS kaydını silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`/api/domains/${selectedDomain.id}/dns/${recordId}`);
        toast.success('DNS kaydı başarıyla silindi');
        fetchDNSRecords(selectedDomain.id);
      } catch (error) {
        toast.error('DNS kaydı silinirken bir hata oluştu');
      }
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'A',
      content: '',
      ttl: 3600,
      priority: null
    });
  };

  const validateDNSRecords = async () => {
    try {
      const response = await axios.get(`/api/domains/${selectedDomain.id}/dns/validate`);
      if (response.data.valid) {
        toast.success('DNS kayıtları geçerli');
      } else {
        toast.warning(`Eksik DNS kayıtları: ${response.data.missing_records.join(', ')}`);
      }
    } catch (error) {
      toast.error('DNS kayıtları doğrulanırken bir hata oluştu');
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">DNS Yönetimi</h1>
          <p className="mt-2 text-sm text-gray-700">
            Domain DNS kayıtlarını yönetin
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-4">
          <button
            onClick={validateDNSRecords}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <CheckCircleIcon className="h-5 w-5 mr-2" />
            DNS Kayıtlarını Doğrula
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Yeni DNS Kaydı
          </button>
        </div>
      </div>

      {/* Domain Seçimi */}
      <div className="mt-8">
        <label htmlFor="domain" className="block text-sm font-medium text-gray-700">
          Domain Seçin
        </label>
        <select
          id="domain"
          value={selectedDomain?.id || ''}
          onChange={(e) => handleDomainChange(domains.find(d => d.id === parseInt(e.target.value)))}
          className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
        >
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>
      </div>

      {/* DNS Kayıtları Tablosu */}
      <div className="mt-8 flex flex-col">
        <div className="-my-2 -mx-4 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle md:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İsim
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tip
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      İçerik
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      TTL
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Öncelik
                    </th>
                    <th scope="col" className="relative px-6 py-3">
                      <span className="sr-only">İşlemler</span>
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                        Yükleniyor...
                      </td>
                    </tr>
                  ) : dnsRecords.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-6 py-4 text-center text-sm text-gray-500">
                        DNS kaydı bulunamadı
                      </td>
                    </tr>
                  ) : (
                    dnsRecords.map((record) => (
                      <tr key={record.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {record.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {record.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {record.content}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {record.ttl}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {record.priority || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => {
                              setSelectedRecord(record);
                              setFormData({
                                name: record.name,
                                type: record.type,
                                content: record.content,
                                ttl: record.ttl,
                                priority: record.priority
                              });
                              setShowEditModal(true);
                            }}
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            <PencilIcon className="h-5 w-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteRecord(record.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            <TrashIcon className="h-5 w-5" />
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

      {/* DNS Kaydı Ekleme Modalı */}
      <Modal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          resetForm();
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Yeni DNS Kaydı</h3>
          <form onSubmit={handleAddRecord}>
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  İsim
                </label>
                <input
                  type="text"
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="@ veya subdomain"
                  required
                />
              </div>

              <div>
                <label htmlFor="type" className="block text-sm font-medium text-gray-700">
                  Tip
                </label>
                <select
                  id="type"
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="A">A</option>
                  <option value="AAAA">AAAA</option>
                  <option value="CNAME">CNAME</option>
                  <option value="MX">MX</option>
                  <option value="TXT">TXT</option>
                  <option value="NS">NS</option>
                  <option value="SRV">SRV</option>
                  <option value="PTR">PTR</option>
                </select>
              </div>

              <div>
                <label htmlFor="content" className="block text-sm font-medium text-gray-700">
                  İçerik
                </label>
                <input
                  type="text"
                  id="content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="IP adresi veya hedef"
                  required
                />
              </div>

              <div>
                <label htmlFor="ttl" className="block text-sm font-medium text-gray-700">
                  TTL (saniye)
                </label>
                <input
                  type="number"
                  id="ttl"
                  value={formData.ttl}
                  onChange={(e) => setFormData({ ...formData, ttl: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  min="60"
                  required
                />
              </div>

              {formData.type === 'MX' && (
                <div>
                  <label htmlFor="priority" className="block text-sm font-medium text-gray-700">
                    Öncelik
                  </label>
                  <input
                    type="number"
                    id="priority"
                    value={formData.priority || ''}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    min="0"
                    required
                  />
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowAddModal(false);
                  resetForm();
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                İptal
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Ekle
              </button>
            </div>
          </form>
        </div>
      </Modal>

      {/* DNS Kaydı Düzenleme Modalı */}
      <Modal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          resetForm();
        }}
      >
        <div className="p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">DNS Kaydını Düzenle</h3>
          <form onSubmit={handleEditRecord}>
            <div className="space-y-4">
              <div>
                <label htmlFor="edit_name" className="block text-sm font-medium text-gray-700">
                  İsim
                </label>
                <input
                  type="text"
                  id="edit_name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="@ veya subdomain"
                  required
                />
              </div>

              <div>
                <label htmlFor="edit_type" className="block text-sm font-medium text-gray-700">
                  Tip
                </label>
                <select
                  id="edit_type"
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="A">A</option>
                  <option value="AAAA">AAAA</option>
                  <option value="CNAME">CNAME</option>
                  <option value="MX">MX</option>
                  <option value="TXT">TXT</option>
                  <option value="NS">NS</option>
                  <option value="SRV">SRV</option>
                  <option value="PTR">PTR</option>
                </select>
              </div>

              <div>
                <label htmlFor="edit_content" className="block text-sm font-medium text-gray-700">
                  İçerik
                </label>
                <input
                  type="text"
                  id="edit_content"
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="IP adresi veya hedef"
                  required
                />
              </div>

              <div>
                <label htmlFor="edit_ttl" className="block text-sm font-medium text-gray-700">
                  TTL (saniye)
                </label>
                <input
                  type="number"
                  id="edit_ttl"
                  value={formData.ttl}
                  onChange={(e) => setFormData({ ...formData, ttl: parseInt(e.target.value) })}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  min="60"
                  required
                />
              </div>

              {formData.type === 'MX' && (
                <div>
                  <label htmlFor="edit_priority" className="block text-sm font-medium text-gray-700">
                    Öncelik
                  </label>
                  <input
                    type="number"
                    id="edit_priority"
                    value={formData.priority || ''}
                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                    min="0"
                    required
                  />
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowEditModal(false);
                  resetForm();
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                İptal
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Kaydet
              </button>
            </div>
          </form>
        </div>
      </Modal>
    </div>
  );
}

export default DNSManagement; 