import React, { useState, useEffect } from 'react';
import { RefreshCw, AlertTriangle, CheckCircle, Database, HardDrive, Search } from 'lucide-react';

interface SyncStatus {
  user_id: string;
  total_files: number;
  synced: number;
  issues: number;
  files: Array<{
    file_name: string;
    file_key: string;
    sync_status: string;
    locations: {
      mongodb: boolean;
      s3: boolean;
      qdrant: boolean;
    };
    issues: string[];
  }>;
}

interface SyncStatusPanelProps {
  userId: string;
  className?: string;
}

const SyncStatusPanel: React.FC<SyncStatusPanelProps> = ({ userId, className = '' }) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchSyncStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/sync/status/${userId}`);
      const data = await response.json();
      
      if (data.success) {
        setSyncStatus(data.sync_status);
        setLastUpdated(new Date());
      } else {
        setError(data.error || 'Failed to fetch sync status');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sync status');
    } finally {
      setLoading(false);
    }
  };

  const analyzeSyncIssues = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/sync/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId }),
      });
      
      const data = await response.json();
      
      if (data.success) {
        // Refresh status after analysis
        await fetchSyncStatus();
      } else {
        setError(data.error || 'Failed to analyze sync issues');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze sync issues');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSyncStatus();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchSyncStatus, 30000);
    return () => clearInterval(interval);
  }, [userId]);

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case 'synced':
        return 'text-green-600 dark:text-green-400';
      case 'out_of_sync':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'missing':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getSyncStatusIcon = (status: string) => {
    switch (status) {
      case 'synced':
        return <CheckCircle className="w-4 h-4" />;
      case 'out_of_sync':
      case 'missing':
        return <AlertTriangle className="w-4 h-4" />;
      default:
        return <RefreshCw className="w-4 h-4" />;
    }
  };

  const getStorageIcon = (storage: string) => {
    switch (storage) {
      case 'mongodb':
        return <Database className="w-4 h-4" />;
      case 's3':
        return <HardDrive className="w-4 h-4" />;
      case 'qdrant':
        return <Search className="w-4 h-4" />;
      default:
        return null;
    }
  };

  if (error) {
    return (
      <div className={`bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 ${className}`}>
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
          <span className="text-red-800 dark:text-red-200 font-medium">Sync Status Error</span>
        </div>
        <p className="text-red-700 dark:text-red-300 text-sm mt-1">{error}</p>
        <button
          onClick={fetchSyncStatus}
          className="mt-2 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 text-sm underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Data Sync Status
          </h3>
          <div className="flex items-center space-x-2">
            {lastUpdated && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Updated {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <button
              onClick={fetchSyncStatus}
              disabled={loading}
              className="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
              title="Refresh sync status"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading && !syncStatus ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            <span className="ml-2 text-gray-600 dark:text-gray-400">Loading sync status...</span>
          </div>
        ) : syncStatus ? (
          <>
            {/* Summary */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {syncStatus.total_files}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Total Files</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {syncStatus.synced}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Synced</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600 dark:text-red-400">
                  {syncStatus.issues}
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Issues</div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-2 mb-4">
              <button
                onClick={analyzeSyncIssues}
                disabled={loading}
                className="px-3 py-1 text-sm bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-800 disabled:opacity-50"
              >
                Analyze Issues
              </button>
            </div>

            {/* Files List */}
            {syncStatus.files.length > 0 && (
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                  Files ({syncStatus.files.length})
                </h4>
                <div className="max-h-64 overflow-y-auto space-y-1">
                  {syncStatus.files.map((file, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded text-sm"
                    >
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-gray-900 dark:text-white truncate">
                          {file.file_name}
                        </div>
                        {file.issues.length > 0 && (
                          <div className="text-xs text-red-600 dark:text-red-400">
                            {file.issues.join(', ')}
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-2">
                        {/* Sync Status */}
                        <div className={`flex items-center space-x-1 ${getSyncStatusColor(file.sync_status)}`}>
                          {getSyncStatusIcon(file.sync_status)}
                          <span className="text-xs capitalize">{file.sync_status.replace('_', ' ')}</span>
                        </div>
                        
                        {/* Storage Locations */}
                        <div className="flex items-center space-x-1">
                          <div
                            className={`p-1 rounded ${
                              file.locations.mongodb
                                ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400'
                                : 'bg-gray-100 dark:bg-gray-600 text-gray-400 dark:text-gray-500'
                            }`}
                            title={`MongoDB: ${file.locations.mongodb ? 'Present' : 'Missing'}`}
                          >
                            {getStorageIcon('mongodb')}
                          </div>
                          <div
                            className={`p-1 rounded ${
                              file.locations.s3
                                ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400'
                                : 'bg-gray-100 dark:bg-gray-600 text-gray-400 dark:text-gray-500'
                            }`}
                            title={`S3: ${file.locations.s3 ? 'Present' : 'Missing'}`}
                          >
                            {getStorageIcon('s3')}
                          </div>
                          <div
                            className={`p-1 rounded ${
                              file.locations.qdrant
                                ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400'
                                : 'bg-gray-100 dark:bg-gray-600 text-gray-400 dark:text-gray-500'
                            }`}
                            title={`Qdrant: ${file.locations.qdrant ? 'Present' : 'Missing'}`}
                          >
                            {getStorageIcon('qdrant')}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            No sync status available
          </div>
        )}
      </div>
    </div>
  );
};

export default SyncStatusPanel;
