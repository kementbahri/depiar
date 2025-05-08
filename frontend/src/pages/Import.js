import React, { useState } from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';
import {
  CloudUploadIcon,
  DocumentIcon,
  CheckCircleIcon,
  ExclamationIcon,
} from '@heroicons/react/outline';

function Import() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [importType, setImportType] = useState('cpanel'); // 'cpanel' veya 'plesk'
  const [importStatus, setImportStatus] = useState(null);
  const [importProgress, setImportProgress] = useState(0);
  const [importLogs, setImportLogs] = useState([]);
  const [isImporting, setIsImporting] = useState(false);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Dosya uzantısı kontrolü
      const validExtensions = importType === 'cpanel' 
        ? ['.tar.gz', '.zip'] 
        : ['.xml', '.zip'];
      
      const fileExtension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!validExtensions.includes(fileExtension)) {
        toast.error(`Geçersiz dosya formatı. ${importType === 'cpanel' ? 'TAR.GZ veya ZIP' : 'XML veya ZIP'} dosyası yükleyin.`);
        return;
      }

      setSelectedFile(file);
      setImportStatus(null);
      setImportProgress(0);
      setImportLogs([]);
    }
  };

  const handleImport = async () => {
    if (!selectedFile) {
      toast.error('Lütfen bir dosya seçin');
      return;
    }

    setIsImporting(true);
    setImportStatus('preparing');
    setImportLogs(prev => [...prev, 'İçe aktarma başlatılıyor...']);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('type', importType);

    try {
      const response = await axios.post('/api/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setImportProgress(progress);
        },
      });

      if (response.data.success) {
        setImportStatus('success');
        setImportLogs(prev => [...prev, 'İçe aktarma başarıyla tamamlandı']);
        toast.success('İçe aktarma başarıyla tamamlandı');
      } else {
        throw new Error(response.data.message || 'İçe aktarma sırasında bir hata oluştu');
      }
    } catch (error) {
      setImportStatus('error');
      setImportLogs(prev => [...prev, `Hata: ${error.message}`]);
      toast.error('İçe aktarma sırasında bir hata oluştu');
    } finally {
      setIsImporting(false);
    }
  };

  const getStatusIcon = () => {
    switch (importStatus) {
      case 'success':
        return <CheckCircleIcon className="h-8 w-8 text-green-500" />;
      case 'error':
        return <ExclamationIcon className="h-8 w-8 text-red-500" />;
      default:
        return <DocumentIcon className="h-8 w-8 text-gray-400" />;
    }
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-semibold text-gray-900">Toplu İçe Aktarma</h1>
          <p className="mt-2 text-sm text-gray-700">
            cPanel veya Plesk'ten dışa aktarılan verileri içe aktarın
          </p>
        </div>
      </div>

      <div className="mt-8 max-w-3xl mx-auto">
        <div className="bg-white shadow sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="space-y-6">
              {/* Platform Seçimi */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Platform
                </label>
                <div className="mt-2 space-x-4">
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      value="cpanel"
                      checked={importType === 'cpanel'}
                      onChange={(e) => setImportType(e.target.value)}
                      className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">cPanel</span>
                  </label>
                  <label className="inline-flex items-center">
                    <input
                      type="radio"
                      value="plesk"
                      checked={importType === 'plesk'}
                      onChange={(e) => setImportType(e.target.value)}
                      className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300"
                    />
                    <span className="ml-2 text-sm text-gray-700">Plesk</span>
                  </label>
                </div>
              </div>

              {/* Dosya Yükleme */}
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Dışa Aktarma Dosyası
                </label>
                <div className="mt-2 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                  <div className="space-y-1 text-center">
                    <CloudUploadIcon className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-primary-600 hover:text-primary-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-primary-500"
                      >
                        <span>Dosya Seç</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          onChange={handleFileSelect}
                          accept={importType === 'cpanel' ? '.tar.gz,.zip' : '.xml,.zip'}
                        />
                      </label>
                      <p className="pl-1">veya sürükleyip bırakın</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      {importType === 'cpanel' 
                        ? 'TAR.GZ veya ZIP dosyası yükleyin'
                        : 'XML veya ZIP dosyası yükleyin'}
                    </p>
                  </div>
                </div>
                {selectedFile && (
                  <p className="mt-2 text-sm text-gray-500">
                    Seçilen dosya: {selectedFile.name}
                  </p>
                )}
              </div>

              {/* İlerleme Çubuğu */}
              {isImporting && (
                <div className="mt-4">
                  <div className="relative pt-1">
                    <div className="flex mb-2 items-center justify-between">
                      <div>
                        <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-primary-600 bg-primary-200">
                          İçe Aktarma
                        </span>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-semibold inline-block text-primary-600">
                          {importProgress}%
                        </span>
                      </div>
                    </div>
                    <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-primary-200">
                      <div
                        style={{ width: `${importProgress}%` }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-primary-500"
                      ></div>
                    </div>
                  </div>
                </div>
              )}

              {/* İçe Aktarma Logları */}
              {importLogs.length > 0 && (
                <div className="mt-4">
                  <h3 className="text-lg font-medium text-gray-900">İşlem Logları</h3>
                  <div className="mt-2 bg-gray-50 rounded-md p-4">
                    <ul className="space-y-2">
                      {importLogs.map((log, index) => (
                        <li key={index} className="text-sm text-gray-600">
                          {log}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* İçe Aktarma Butonu */}
              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleImport}
                  disabled={!selectedFile || isImporting}
                  className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white ${
                    !selectedFile || isImporting
                      ? 'bg-gray-400 cursor-not-allowed'
                      : 'bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500'
                  }`}
                >
                  {isImporting ? 'İçe Aktarılıyor...' : 'İçe Aktar'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Import; 