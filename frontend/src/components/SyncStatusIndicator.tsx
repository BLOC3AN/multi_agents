import React, { useState, useEffect } from 'react';
import { CheckCircle, AlertTriangle, RefreshCw, Database } from 'lucide-react';

interface SyncStatus {
  user_id: string;
  total_files: number;
  synced: number;
  issues: number;
}

const SyncStatusIndicator: React.FC = () => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSyncStatus = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/sync/status/global');
      const data = await response.json();
      
      if (data.success) {
        setSyncStatus(data.sync_status);
      } else {
        setError('Failed to fetch');
      }
    } catch (err) {
      setError('Network error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSyncStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSyncStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const getSyncStatusColor = () => {
    if (!syncStatus) return 'text-gray-400';
    if (syncStatus.issues > 0) return 'text-red-500';
    if (syncStatus.total_files === 0) return 'text-gray-400';
    if (syncStatus.synced === syncStatus.total_files) return 'text-green-500';
    return 'text-yellow-500';
  };

  const getSyncStatusIcon = () => {
    if (loading) return <RefreshCw className="w-4 h-4 animate-spin" />;
    if (error) return <AlertTriangle className="w-4 h-4" />;
    if (!syncStatus) return <Database className="w-4 h-4" />;
    if (syncStatus.issues > 0) return <AlertTriangle className="w-4 h-4" />;
    if (syncStatus.total_files === 0) return <Database className="w-4 h-4" />;
    if (syncStatus.synced === syncStatus.total_files) return <CheckCircle className="w-4 h-4" />;
    return <RefreshCw className="w-4 h-4" />;
  };

  const getSyncStatusText = () => {
    if (loading) return 'Checking...';
    if (error) return 'Error';
    if (!syncStatus) return 'Unknown';
    if (syncStatus.total_files === 0) return 'No files';
    if (syncStatus.issues > 0) return `${syncStatus.issues} issues`;
    if (syncStatus.synced === syncStatus.total_files) return 'All synced';
    return `${syncStatus.synced}/${syncStatus.total_files}`;
  };

  return (
    <div 
      className={`flex items-center space-x-2 px-3 py-1 rounded-full bg-gray-100 dark:bg-gray-700 cursor-pointer hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors ${getSyncStatusColor()}`}
      onClick={fetchSyncStatus}
      title={`Data Sync Status: ${getSyncStatusText()}${syncStatus ? ` (${syncStatus.total_files} total files)` : ''}`}
    >
      {getSyncStatusIcon()}
      <span className="text-xs font-medium">
        {getSyncStatusText()}
      </span>
    </div>
  );
};

export default SyncStatusIndicator;
