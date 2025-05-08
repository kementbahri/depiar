import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/outline';

function SuspendedPage({ type, reason, date }) {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <div className="text-center">
            <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-yellow-400" />
            <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
              {type === 'domain' ? 'Domain Askıya Alındı' : 'Hesap Askıya Alındı'}
            </h2>
            <p className="mt-2 text-sm text-gray-600">
              {type === 'domain'
                ? 'Bu domain şu anda askıya alınmış durumda.'
                : 'Hesabınız şu anda askıya alınmış durumda.'}
            </p>
          </div>

          <div className="mt-6">
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-yellow-800">
                    Askıya Alma Detayları
                  </h3>
                  <div className="mt-2 text-sm text-yellow-700">
                    <p><strong>Sebep:</strong> {reason}</p>
                    <p><strong>Tarih:</strong> {new Date(date).toLocaleString()}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6">
            <div className="text-sm text-center text-gray-600">
              <p>
                {type === 'domain'
                  ? 'Bu domain ile ilgili sorularınız için lütfen destek ekibimizle iletişime geçin.'
                  : 'Hesabınızla ilgili sorularınız için lütfen destek ekibimizle iletişime geçin.'}
              </p>
              <p className="mt-2">
                <a href="mailto:support@example.com" className="font-medium text-primary-600 hover:text-primary-500">
                  support@example.com
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SuspendedPage; 