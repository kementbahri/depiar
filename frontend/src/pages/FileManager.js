import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import {
  FolderIcon,
  DocumentIcon,
  PhotographIcon,
  MusicNoteIcon,
  FilmIcon,
  CodeIcon,
  ArchiveIcon,
  PlusIcon,
  UploadIcon,
  DownloadIcon,
  TrashIcon,
  PencilIcon,
  SearchIcon,
  SortAscendingIcon,
  RefreshIcon,
  FolderAddIcon,
  DocumentAddIcon,
} from '@heroicons/react/outline';

function FileManager() {
  const [files, setFiles] = useState([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [loading, setLoading] = useState(true);
  const [showNewFolderModal, setShowNewFolderModal] = useState(false);
  const [showNewFileModal, setShowNewFileModal] = useState(false);
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [formData, setFormData] = useState({
    name: '',
    content: '',
  });
  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    fetchFiles();
  }, [currentPath]);

  const fetchFiles = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/files?path=${encodeURIComponent(currentPath)}`);
      setFiles(response.data);
    } catch (error) {
      toast.error('Dosyalar yüklenirken bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateFolder = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/files/folder', {
        path: currentPath,
        name: formData.name,
      });
      toast.success('Klasör başarıyla oluşturuldu');
      setShowNewFolderModal(false);
      fetchFiles();
      resetForm();
    } catch (error) {
      toast.error('Klasör oluşturulurken bir hata oluştu');
    }
  };

  const handleCreateFile = async (e) => {
    e.preventDefault();
    try {
      await axios.post('/api/files', {
        path: currentPath,
        name: formData.name,
        content: formData.content,
      });
      toast.success('Dosya başarıyla oluşturuldu');
      setShowNewFileModal(false);
      fetchFiles();
      resetForm();
    } catch (error) {
      toast.error('Dosya oluşturulurken bir hata oluştu');
    }
  };

  const handleRename = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`/api/files/${selectedFile.id}`, {
        name: formData.name,
      });
      toast.success('Dosya başarıyla yeniden adlandırıldı');
      setShowRenameModal(false);
      fetchFiles();
      resetForm();
    } catch (error) {
      toast.error('Dosya yeniden adlandırılırken bir hata oluştu');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Bu dosyayı silmek istediğinizden emin misiniz?')) {
      try {
        await axios.delete(`/api/files/${id}`);
        toast.success('Dosya başarıyla silindi');
        fetchFiles();
      } catch (error) {
        toast.error('Dosya silinirken bir hata oluştu');
      }
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('path', currentPath);

    try {
      await axios.post('/api/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      toast.success('Dosya başarıyla yüklendi');
      setShowUploadModal(false);
      setUploadFile(null);
      fetchFiles();
    } catch (error) {
      toast.error('Dosya yüklenirken bir hata oluştu');
    }
  };

  const handleDownload = async (file) => {
    try {
      const response = await axios.get(`/api/files/${file.id}/download`, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Dosya indirilirken bir hata oluştu');
    }
  };

  const handleNavigate = (path) => {
    setCurrentPath(path);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      content: '',
    });
  };

  const getFileIcon = (file) => {
    if (file.type === 'directory') {
      return <FolderIcon className="h-10 w-10 text-yellow-400" />;
    }

    const extension = file.name.split('.').pop().toLowerCase();
    switch (extension) {
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return <PhotographIcon className="h-10 w-10 text-blue-400" />;
      case 'mp3':
      case 'wav':
      case 'ogg':
        return <MusicNoteIcon className="h-10 w-10 text-purple-400" />;
      case 'mp4':
      case 'avi':
      case 'mov':
        return <FilmIcon className="h-10 w-10 text-red-400" />;
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
      case 'html':
      case 'css':
      case 'php':
      case 'py':
      case 'java':
        return <CodeIcon className="h-10 w-10 text-green-400" />;
      case 'zip':
      case 'rar':
      case '7z':
      case 'tar':
      case 'gz':
        return <ArchiveIcon className="h-10 w-10 text-orange-400" />;
      default:
        return <DocumentIcon className="h-10 w-10 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredFiles = files
    .filter(file => 
      file.name.toLowerCase().includes(searchTerm.toLowerCase())
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
          <h1 className="text-2xl font-semibold text-gray-900">Dosya Yöneticisi</h1>
          <p className="mt-2 text-sm text-gray-700">
            Dosya ve klasörlerinizi yönetin
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none space-x-4">
          <button
            type="button"
            onClick={() => setShowNewFolderModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <FolderAddIcon className="-ml-1 mr-2 h-5 w-5" />
            Yeni Klasör
          </button>
          <button
            type="button"
            onClick={() => setShowNewFileModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <DocumentAddIcon className="-ml-1 mr-2 h-5 w-5" />
            Yeni Dosya
          </button>
          <button
            type="button"
            onClick={() => setShowUploadModal(true)}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 sm:w-auto"
          >
            <UploadIcon className="-ml-1 mr-2 h-5 w-5" />
            Dosya Yükle
          </button>
        </div>
      </div>

      {/* Dosya Yolu */}
      <div className="mt-4 flex items-center space-x-2 text-sm text-gray-500">
        <button
          onClick={() => handleNavigate('/')}
          className="hover:text-gray-700"
        >
          Ana Dizin
        </button>
        {currentPath.split('/').filter(Boolean).map((dir, index, array) => (
          <React.Fragment key={index}>
            <span>/</span>
            <button
              onClick={() => handleNavigate('/' + array.slice(0, index + 1).join('/'))}
              className="hover:text-gray-700"
            >
              {dir}
            </button>
          </React.Fragment>
        ))}
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
              placeholder="Dosya ara..."
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
            onClick={fetchFiles}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <RefreshIcon className="h-5 w-5 mr-2" />
            Yenile
          </button>
        </div>
      </div>

      {/* Dosya Listesi */}
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
                      Ad
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('type')}
                    >
                      Tür
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('size')}
                    >
                      Boyut
                    </th>
                    <th 
                      scope="col" 
                      className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 cursor-pointer"
                      onClick={() => setSortBy('modified_at')}
                    >
                      Son Değişiklik
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
                  ) : filteredFiles.length === 0 ? (
                    <tr>
                      <td colSpan="5" className="px-3 py-4 text-center text-sm text-gray-500">
                        Dosya bulunamadı
                      </td>
                    </tr>
                  ) : (
                    filteredFiles.map((file) => (
                      <tr key={file.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <div className="flex items-center">
                            <div className="h-10 w-10 flex-shrink-0">
                              {getFileIcon(file)}
                            </div>
                            <div className="ml-4">
                              <div className="font-medium text-gray-900">
                                {file.type === 'directory' ? (
                                  <button
                                    onClick={() => handleNavigate(currentPath + '/' + file.name)}
                                    className="hover:text-primary-600"
                                  >
                                    {file.name}
                                  </button>
                                ) : (
                                  file.name
                                )}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {file.type === 'directory' ? 'Klasör' : file.name.split('.').pop().toUpperCase()}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {file.type === 'directory' ? '-' : formatFileSize(file.size)}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {new Date(file.modified_at).toLocaleString('tr-TR')}
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <div className="flex justify-end space-x-2">
                            {file.type !== 'directory' && (
                              <button
                                onClick={() => handleDownload(file)}
                                className="text-primary-600 hover:text-primary-900"
                                title="İndir"
                              >
                                <DownloadIcon className="h-5 w-5" />
                              </button>
                            )}
                            <button
                              onClick={() => {
                                setSelectedFile(file);
                                setFormData({ name: file.name });
                                setShowRenameModal(true);
                              }}
                              className="text-primary-600 hover:text-primary-900"
                              title="Yeniden Adlandır"
                            >
                              <PencilIcon className="h-5 w-5" />
                            </button>
                            <button
                              onClick={() => handleDelete(file.id)}
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

      {/* Yeni Klasör Modal */}
      {showNewFolderModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleCreateFolder}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Yeni Klasör
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Klasör Adı
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Oluştur
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowNewFolderModal(false)}
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

      {/* Yeni Dosya Modal */}
      {showNewFileModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleCreateFile}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Yeni Dosya
                  </h3>
                  <div className="mt-4 grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-6">
                    <div className="sm:col-span-3">
                      <label className="block text-sm font-medium text-gray-700">
                        Dosya Adı
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      />
                    </div>

                    <div className="sm:col-span-6">
                      <label className="block text-sm font-medium text-gray-700">
                        İçerik
                      </label>
                      <textarea
                        rows={10}
                        value={formData.content}
                        onChange={(e) => setFormData({ ...formData, content: e.target.value })}
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
                    Oluştur
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowNewFileModal(false)}
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

      {/* Yeniden Adlandırma Modal */}
      {showRenameModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleRename}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Yeniden Adlandır
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Yeni Ad
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Yeniden Adlandır
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowRenameModal(false)}
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

      {/* Dosya Yükleme Modal */}
      {showUploadModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <form onSubmit={handleUpload}>
                <div>
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    Dosya Yükle
                  </h3>
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700">
                      Dosya Seç
                    </label>
                    <input
                      type="file"
                      required
                      onChange={(e) => setUploadFile(e.target.files[0])}
                      className="mt-1 block w-full"
                    />
                  </div>
                </div>
                <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                  <button
                    type="submit"
                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:col-start-2 sm:text-sm"
                  >
                    Yükle
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowUploadModal(false)}
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

export default FileManager; 