import React, { useState, useEffect, useMemo, useCallback, lazy, Suspense } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

// Lazy load heavy components
const FilePreviewModal = lazy(() => import('../components/FilePreviewModal'));
import {
  getAdminUsers,
  getAdminSessions,
  getAdminStats,
  getAdminFiles,
  getAdminMessages,
  deleteAdminFile,
  deleteAdminMessage,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword
} from '../services/simple-api';
import type { AdminUser, AdminSession, AdminStats, UserCreateRequest, UserUpdateRequest, PasswordChangeRequest, User } from '../types';
import AddUserModal from '../components/AddUserModal';
import EditUserModal from '../components/EditUserModal';
import ChangePasswordModal from '../components/ChangePasswordModal';
import UserHistoryModal from '../components/UserHistoryModal';
import ConfirmationDialog from '../components/ConfirmationDialog';
import SyncStatusPanel from '../components/SyncStatusPanel';
import SyncStatusIndicator from '../components/SyncStatusIndicator';
import Toast from '../components/Toast';

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'sessions' | 'messages' | 'files' | 'sync'>('stats');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data states with caching
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [sessions, setSessions] = useState<AdminSession[]>([]);
  const [messages, setMessages] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);

  // Cache tracking - track which data has been loaded
  const [dataCache, setDataCache] = useState({
    stats: false,
    users: false,
    admins: false,
    sessions: false,
    messages: false,
    files: false
  });
  const [fileFilter, setFileFilter] = useState<string>('');
  const [fileSortBy, setFileSortBy] = useState<'name' | 'size' | 'date' | 'user'>('date');

  // Debounced search for better performance
  const [debouncedFileFilter, setDebouncedFileFilter] = useState<string>('');

  // Pagination states
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(20); // Show 20 items per page

  // Debounce file filter
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFileFilter(fileFilter);
      setCurrentPage(1); // Reset to first page when filter changes
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [fileFilter]);

  // Modal states
  const [previewModal, setPreviewModal] = useState<{isOpen: boolean, fileKey: string, fileName: string}>({
    isOpen: false,
    fileKey: '',
    fileName: ''
  });
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [showUserHistoryModal, setShowUserHistoryModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Check if user is admin (including super_admin)
  const isAdmin = user?.role === 'editor' || user?.role === 'super_admin';

  // Check if user is super admin (for admin management)
  const isSuperAdmin = user?.role === 'super_admin';

  // Handle navigation back to chat
  const handleBackToChat = () => {
    navigate('/chat');
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin, activeTab]);

  // Individual data loaders for lazy loading
  const loadStats = async () => {
    if (dataCache.stats) return; // Skip if already loaded

    try {
      const response = await getAdminStats();
      if (response.success && response.data) {
        setStats(response.data);
        setDataCache(prev => ({ ...prev, stats: true }));
      } else {
        setError(response.error || 'Failed to load statistics');
      }
    } catch (error) {
      setError('Failed to load statistics');
    }
  };

  const loadUsers = async () => {
    if (dataCache.users) return; // Skip if already loaded

    try {
      const response = await getAdminUsers();
      if (response.success && response.data) {
        setUsers(response.data);
        setDataCache(prev => ({ ...prev, users: true }));
      } else {
        setError(response.error || 'Failed to load users');
      }
    } catch (error) {
      setError('Failed to load users');
    }
  };

  const loadAdmins = async (force = false) => {
    if (dataCache.admins && !force) return; // Skip if already loaded

    try {
      // Get admins from admins collection (super_admin only)
      const response = await fetch(`http://localhost:8000/admin/users?collection=admins`);
      const data = await response.json();

      if (data.success) {
        setAdmins(data.users || []);
        setDataCache(prev => ({ ...prev, admins: true }));
      } else {
        setError(data.error || 'Failed to load admins');
      }
    } catch (error) {
      console.error('Error loading admins:', error);
      setError('Failed to load admins');
    }
  };

  const loadSessions = async () => {
    if (dataCache.sessions) return; // Skip if already loaded

    try {
      const response = await getAdminSessions();
      if (response.success && response.data) {
        setSessions(response.data);
        setDataCache(prev => ({ ...prev, sessions: true }));
      } else {
        setError(response.error || 'Failed to load sessions');
      }
    } catch (error) {
      setError('Failed to load sessions');
    }
  };

  const loadMessages = async () => {
    if (dataCache.messages) return; // Skip if already loaded

    try {
      const response = await getAdminMessages();
      if (response.success && response.data) {
        setMessages(response.data);
        setDataCache(prev => ({ ...prev, messages: true }));
      } else {
        setError(response.error || 'Failed to load messages');
      }
    } catch (error) {
      setError('Failed to load messages');
    }
  };

  const loadFiles = async () => {
    if (dataCache.files) return; // Skip if already loaded

    try {
      const response = await getAdminFiles();
      if (response.success && response.data) {
        setFiles(response.data);
        setDataCache(prev => ({ ...prev, files: true }));
      } else {
        setError(response.error || 'Failed to load files');
      }
    } catch (error) {
      setError('Failed to load files');
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'stats') {
        // For stats, only load stats data initially
        // Files and messages will be loaded when their cards are clicked
        await loadStats();
      } else if (activeTab === 'users') {
        await loadUsers();
        await loadAdmins(true); // Force reload admins
      } else if (activeTab === 'sessions') {
        await loadSessions();
      } else if (activeTab === 'messages') {
        await loadMessages();
      } else if (activeTab === 'files') {
        await loadFiles();
      } else if (activeTab === 'sync') {
        // Sync tab needs users data for per-user sync status
        await loadUsers();
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (contentType: string): string => {
    if (!contentType) return '📄';
    if (contentType.startsWith('image/')) return '🖼️';
    if (contentType.startsWith('video/')) return '🎥';
    if (contentType.startsWith('audio/')) return '🎵';
    if (contentType.includes('pdf')) return '📕';
    if (contentType.includes('word') || contentType.includes('document')) return '📝';
    if (contentType.includes('excel') || contentType.includes('spreadsheet')) return '📊';
    if (contentType.includes('powerpoint') || contentType.includes('presentation')) return '📽️';
    if (contentType.includes('zip') || contentType.includes('archive')) return '📦';
    if (contentType.includes('text')) return '📄';
    return '📁';
  };

  const getFileTypeLabel = (contentType: string): string => {
    if (!contentType) return 'File';
    if (contentType.startsWith('image/')) return 'Image';
    if (contentType.startsWith('video/')) return 'Video';
    if (contentType.startsWith('audio/')) return 'Audio';
    if (contentType.includes('pdf')) return 'PDF';
    if (contentType.includes('word') || contentType.includes('document')) return 'Document';
    if (contentType.includes('excel') || contentType.includes('spreadsheet')) return 'Spreadsheet';
    if (contentType.includes('powerpoint') || contentType.includes('presentation')) return 'Presentation';
    if (contentType.includes('zip') || contentType.includes('archive')) return 'Archive';
    if (contentType.includes('text')) return 'Text';
    return contentType.split('/')[0] || 'File';
  };

  const handleDeleteFile = async (file: any) => {
    if (!confirm(`Are you sure you want to delete "${file.file_name}" from user ${file.user_id}?`)) {
      return;
    }

    setActionLoading(true);
    try {
      const response = await deleteAdminFile(file.file_key, file.user_id);
      if (response.success) {
        showToast('File deleted successfully!', 'success');
        loadData(); // Refresh files list
      } else {
        showToast(response.error || 'Failed to delete file', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFilePreview = (file: any) => {
    setPreviewModal({
      isOpen: true,
      fileKey: file.file_key,
      fileName: file.file_name
    });
  };

  const closePreviewModal = () => {
    setPreviewModal({
      isOpen: false,
      fileKey: '',
      fileName: ''
    });
  };

  const handleDeleteMessage = async (message: any) => {
    if (!confirm(`Are you sure you want to delete this message from ${message.user_id}?`)) {
      return;
    }

    setActionLoading(true);
    try {
      const response = await deleteAdminMessage(message.message_id);
      if (response.success) {
        showToast('Message deleted successfully!', 'success');
        loadData(); // Refresh messages list
      } else {
        showToast(response.error || 'Failed to delete message', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Filter and sort files with debounced search and pagination
  const { filteredAndSortedFiles, paginatedFiles, totalPages } = useMemo(() => {
    let filtered = files;

    // Apply debounced filter
    if (debouncedFileFilter) {
      filtered = files.filter(file =>
        file.file_name.toLowerCase().includes(debouncedFileFilter.toLowerCase()) ||
        file.user_id.toLowerCase().includes(debouncedFileFilter.toLowerCase()) ||
        file.content_type.toLowerCase().includes(debouncedFileFilter.toLowerCase())
      );
    }

    // Apply sorting
    const sorted = filtered.sort((a, b) => {
      switch (fileSortBy) {
        case 'name':
          return a.file_name.localeCompare(b.file_name);
        case 'size':
          return b.file_size - a.file_size;
        case 'user':
          return a.user_id.localeCompare(b.user_id);
        case 'date':
        default:
          return new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime();
      }
    });

    // Apply pagination
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginated = sorted.slice(startIndex, endIndex);
    const totalPages = Math.ceil(sorted.length / itemsPerPage);

    return {
      filteredAndSortedFiles: sorted,
      paginatedFiles: paginated,
      totalPages
    };
  }, [files, debouncedFileFilter, fileSortBy, currentPage, itemsPerPage]);

  // Force refresh data (clear cache and reload)
  const refreshData = useCallback(async () => {
    setDataCache({
      stats: false,
      users: false,
      sessions: false,
      messages: false,
      files: false
    });
    await loadData();
  }, []);

  // Handle navigation from stats cards with lazy loading
  const handleStatsNavigation = async (tab: 'users' | 'sessions' | 'messages' | 'files') => {
    if (tab !== activeTab) {
      setActiveTab(tab);

      // Pre-load data for the target tab if not already loaded
      setLoading(true);
      try {
        switch (tab) {
          case 'users':
            await loadUsers();
            break;
          case 'sessions':
            await loadSessions();
            break;
          case 'messages':
            await loadMessages();
            break;
          case 'files':
            await loadFiles();
            break;
        }
      } catch (error) {
        console.error('Error pre-loading data:', error);
      } finally {
        setLoading(false);
      }
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // User management handlers
  const handleCreateUser = async (userData: UserCreateRequest) => {
    setActionLoading(true);
    try {
      const response = await createUser(userData);
      if (response.success) {
        showToast('User created successfully!', 'success');
        loadData(); // Refresh user list
      } else {
        showToast(response.error || 'Failed to create user', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateUser = async (userId: string, userData: UserUpdateRequest) => {
    setActionLoading(true);
    try {
      const response = await updateUser(userId, userData);
      if (response.success) {
        showToast('User updated successfully!', 'success');
        loadData(); // Refresh user list
      } else {
        showToast(response.error || 'Failed to update user', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteUser = async () => {
    if (!selectedUser) return;

    setActionLoading(true);
    try {
      const response = await deleteUser(selectedUser.user_id, false);
      if (response.success) {
        showToast('User deleted successfully!', 'success');
        loadData(); // Refresh user list
        setShowDeleteConfirmation(false);
        setSelectedUser(null);
      } else {
        showToast(response.error || 'Failed to delete user', 'error');
      }
    } catch (error: any) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleChangePassword = async (userId: string, passwordData: PasswordChangeRequest) => {
    setActionLoading(true);
    try {
      // Use reset password instead of change password (no current password needed)
      const response = await resetUserPassword(userId, passwordData.new_password);
      if (response.success) {
        showToast('Password reset successfully!', 'success');
      } else {
        showToast(response.error || 'Failed to reset password', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  // Modal handlers
  const openEditModal = (user: AdminUser) => {
    setSelectedUser(user);
    setShowEditUserModal(true);
  };

  const openChangePasswordModal = (user: AdminUser) => {
    setSelectedUser(user);
    setShowChangePasswordModal(true);
  };

  const openUserHistoryModal = (user: AdminUser) => {
    setSelectedUser(user);
    setShowUserHistoryModal(true);
  };

  const openDeleteConfirmation = (user: AdminUser) => {
    setSelectedUser(user);
    setShowDeleteConfirmation(true);
  };

  const closeAllModals = () => {
    setShowAddUserModal(false);
    setShowEditUserModal(false);
    setShowChangePasswordModal(false);
    setShowUserHistoryModal(false);
    setShowDeleteConfirmation(false);
    setSelectedUser(null);
  };

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-900">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 dark:text-red-400 mb-4">
            🚫 Access Denied
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            You need editor or super_admin privileges to access this page.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                🛠️ Admin Dashboard
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Manage users, sessions, and system statistics
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={handleBackToChat}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <span className="mr-2">💬</span>
                Quay về Chat
              </button>
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Welcome, {user?.display_name || user?.user_id}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {[
              { id: 'stats', label: '📊 Statistics' },
              { id: 'users', label: '👥 Users' },
              { id: 'sessions', label: '💬 Sessions' },
              { id: 'messages', label: '💬 Messages' },
              { id: 'files', label: '📁 Files' },
              { id: 'sync', label: '🔄 Sync' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="py-6">
          {loading && (
            <div className="flex flex-col justify-center items-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
              <span className="text-lg font-medium text-gray-600 dark:text-gray-400">Loading {activeTab}...</span>
              <span className="text-sm text-gray-500 dark:text-gray-500 mt-1">Please wait while we fetch the data</span>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6 dark:bg-red-900/20 dark:border-red-800">
              <div className="text-red-600 dark:text-red-400">❌ {error}</div>
              <button 
                onClick={loadData}
                className="mt-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
              >
                🔄 Retry
              </button>
            </div>
          )}

          {!loading && !error && (
            <>
              {/* Statistics Tab */}
              {activeTab === 'stats' && stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  <button
                    onClick={() => handleStatsNavigation('users')}
                    className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-left group ${
                      activeTab === 'users' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">👥</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Users</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.total_users}</p>
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Click to view →</p>
                        </div>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleStatsNavigation('sessions')}
                    className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-left group ${
                      activeTab === 'sessions' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">💬</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Sessions</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.total_sessions}</p>
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Click to view →</p>
                        </div>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => handleStatsNavigation('messages')}
                    className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-left group ${
                      activeTab === 'messages' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">💬</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Messages</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats?.total_messages || 0}</p>
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Click to view →</p>
                        </div>
                      </div>
                    </div>
                  </button>

                  <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg border-l-4 border-orange-500">
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">🔥</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Recent (24h)</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.recent_sessions_24h}</p>
                          <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">Live metric</p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleStatsNavigation('files')}
                    className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-left group ${
                      activeTab === 'files' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">📁</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Files</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats?.total_files || 0}</p>
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            {formatFileSize(files.reduce((sum, file) => sum + file.file_size, 0))}
                          </p>
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Click to view →</p>
                        </div>
                      </div>
                    </div>
                  </button>

                  <button
                    onClick={() => setActiveTab('sync')}
                    className={`bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg hover:shadow-lg transition-all duration-200 hover:scale-105 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 text-left group ${
                      activeTab === 'sync' ? 'ring-2 ring-blue-500 border-blue-500' : ''
                    }`}
                  >
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">🔄</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Data Sync</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">Monitor</p>
                          <p className="text-xs text-blue-600 dark:text-blue-400 mt-1 group-hover:text-blue-700 dark:group-hover:text-blue-300 transition-colors">Check status →</p>
                        </div>
                      </div>
                    </div>
                  </button>
                </div>
              )}

              {/* Users Tab - Split into Users and Admins */}
              {activeTab === 'users' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Users Management */}
                  <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                    <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        👥 Users ({users.length})
                      </h3>
                      <button
                        onClick={() => setShowAddUserModal(true)}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                      >
                        <span className="mr-2">👤</span>
                        Add User
                      </button>
                    </div>
                  {users.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">👥</div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No users found</h3>
                      <p className="text-gray-500 dark:text-gray-400 mb-4">Get started by creating your first user.</p>
                      <button
                        onClick={() => setShowAddUserModal(true)}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                      >
                        <span className="mr-2">👤</span>
                        Add First User
                      </button>
                    </div>
                  ) : (
                    <div className="max-h-96 overflow-y-auto admin-list-scroll pr-2">
                      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                        {users.map((user) => (
                      <li key={user.user_id} className="px-4 py-4 sm:px-6">
                        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
                          <div className="flex items-start sm:items-center space-x-3 flex-1">
                            <div className="flex flex-col space-y-1 flex-shrink-0">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                user.is_active
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {user.is_active ? '✅ Active' : '❌ Inactive'}
                              </span>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                user.role === 'super_admin'
                                  ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                  : user.role === 'admin'
                                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                              }`}>
                                {user.role === 'super_admin' ? '👑 Super Admin' : user.role === 'admin' ? '👑 Admin' : '👤 User'}
                              </span>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                {user.display_name || user.user_id}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                ID: {user.user_id}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                Email: {user.email || 'N/A'}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                                Created: {formatDate(user.created_at)}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400 hidden sm:block">
                                Last Login: {formatDate(user.last_login)}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1 sm:space-x-2">
                            <button
                              onClick={() => openEditModal(user)}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 transition-colors"
                              title="Edit User"
                            >
                              <span className="sm:hidden" >✏️</span>
                              <span className="hidden sm:inline">✏️ Edit</span>
                            </button>
                            <button
                              onClick={() => openChangePasswordModal(user)}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-yellow-700 bg-yellow-100 hover:bg-yellow-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500 dark:bg-yellow-900 dark:text-yellow-200 dark:hover:bg-yellow-800 transition-colors"
                              title="Change Password"
                            >
                              <span className="sm:hidden">🔑</span>
                              <span className="hidden sm:inline">🔑 Password</span>
                            </button>
                            <button
                              onClick={() => openUserHistoryModal(user)}
                              className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 dark:bg-green-900 dark:text-green-200 dark:hover:bg-green-800 transition-colors"
                              title="View History"
                            >
                              <span className="sm:hidden">📊</span>
                              <span className="hidden sm:inline">📊 History</span>
                            </button>
                            {user.role !== 'admin' && user.role !== 'super_admin' ? (
                              <button
                                onClick={() => openDeleteConfirmation(user)}
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition-colors"
                                title="Delete User"
                              >
                                <span className="sm:hidden">🗑️</span>
                                <span className="hidden sm:inline">🗑️ Delete</span>
                              </button>
                            ) : (
                              <button
                                disabled
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-gray-400 bg-gray-100 cursor-not-allowed dark:bg-gray-800 dark:text-gray-500"
                                title="Admin users cannot be deleted"
                              >
                                <span className="sm:hidden">🔒</span>
                                <span className="hidden sm:inline">🔒 Protected</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  </div>

                  {/* Admins Management */}
                  <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                    <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        👑 Admins ({admins.length})
                      </h3>
                      <button
                        onClick={() => setShowAddUserModal(true)}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
                      >
                        <span className="mr-2">👑</span>
                        Add Admin
                      </button>
                    </div>
                    {admins.length === 0 ? (
                      <div className="text-center py-12">
                        <div className="text-6xl mb-4">👑</div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No admins found</h3>
                        <p className="text-gray-500 dark:text-gray-400 mb-4">Get started by creating your first admin.</p>
                        <button
                          onClick={() => setShowAddUserModal(true)}
                          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-colors"
                        >
                          <span className="mr-2">👑</span>
                          Add First Admin
                        </button>
                      </div>
                    ) : (
                      <div className="max-h-96 overflow-y-auto admin-list-scroll pr-2">
                        <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                          {admins.map((admin) => (
                            <li key={admin.user_id} className="px-4 py-4 sm:px-6">
                              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
                                <div className="flex items-start sm:items-center space-x-3 flex-1">
                                  <div className="flex flex-col space-y-1 flex-shrink-0">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                      admin.is_active
                                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                        : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                                    }`}>
                                      {admin.is_active ? '✅ Active' : '❌ Inactive'}
                                    </span>
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                                      👑 Admin
                                    </span>
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                                      {admin.username}
                                    </p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
                                      {admin.email}
                                    </p>
                                    <p className="text-xs text-gray-400 dark:text-gray-500">
                                      Created: {new Date(admin.created_at).toLocaleDateString()}
                                    </p>
                                  </div>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {isSuperAdmin ? (
                                    <button
                                      onClick={() => openEditModal(admin)}
                                      className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 transition-colors"
                                      title="Edit Admin"
                                    >
                                      <span className="sm:hidden">✏️</span>
                                      <span className="hidden sm:inline">✏️ Edit</span>
                                    </button>
                                  ) : (
                                    <button
                                      disabled
                                      className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-gray-400 bg-gray-100 cursor-not-allowed dark:bg-gray-800 dark:text-gray-500"
                                      title="Only super admin can edit admin accounts"
                                    >
                                      <span className="sm:hidden">🔒</span>
                                      <span className="hidden sm:inline">🔒 Restricted</span>
                                    </button>
                                  )}

                                </div>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Sessions Tab */}
              {activeTab === 'sessions' && (
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Chat Sessions ({sessions.length})
                    </h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto admin-list-scroll pr-2">
                    <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                      {sessions.map((session) => (
                      <li key={session.session_id} className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-3 ${
                              session.is_active 
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                            }`}>
                              {session.is_active ? '🟢 Active' : '⚫ Inactive'}
                            </span>
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {session.title || `Session ${session.session_id.slice(0, 8)}`}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                User: {session.user_id} | Messages: {session.total_messages}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Created: {formatDate(session.created_at)}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Updated: {formatDate(session.updated_at)}
                            </div>
                          </div>
                        </div>
                      </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Files Tab */}
              {activeTab === 'files' && (
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <div className="px-4 py-5 sm:px-6">
                    <div className="flex justify-between items-center mb-4">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        Files ({filteredAndSortedFiles.length} of {files.length})
                      </h3>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        Total Size: {formatFileSize(files.reduce((sum, file) => sum + file.file_size, 0))}
                      </div>
                    </div>

                    {/* Filter and Sort Controls */}
                    <div className="flex flex-col sm:flex-row gap-4">
                      <div className="flex-1">
                        <input
                          type="text"
                          placeholder="Search files, users, or types..."
                          value={fileFilter}
                          onChange={(e) => setFileFilter(e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white dark:placeholder-gray-400"
                        />
                      </div>
                      <div>
                        <select
                          value={fileSortBy}
                          onChange={(e) => setFileSortBy(e.target.value as 'name' | 'size' | 'date' | 'user')}
                          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                        >
                          <option value="date">Sort by Date</option>
                          <option value="name">Sort by Name</option>
                          <option value="size">Sort by Size</option>
                          <option value="user">Sort by User</option>
                        </select>
                      </div>
                    </div>
                  </div>
                  {files.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">📁</div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No files found</h3>
                      <p className="text-gray-500 dark:text-gray-400">Files uploaded by users will appear here.</p>
                    </div>
                  ) : (
                    <div className="max-h-96 overflow-y-auto admin-list-scroll pr-2">
                      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                        {files.map((file) => (
                        <li key={file.file_id} className="px-4 py-4 sm:px-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className="flex-shrink-0">
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                                  {getFileIcon(file.content_type)} {getFileTypeLabel(file.content_type)}
                                </span>
                              </div>
                              <div className="flex-1 min-w-0">
                                <button
                                  onClick={() => handleFilePreview(file)}
                                  className="text-sm font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 truncate text-left transition-colors"
                                  title="Click to preview file"
                                >
                                  {file.file_name}
                                </button>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  User: <span className="font-medium">{file.user_id}</span> | Size: {formatFileSize(file.file_size)}
                                </div>
                                <div className="text-xs text-gray-400 dark:text-gray-500">
                                  Uploaded: {formatDate(file.upload_date)} | Type: {file.content_type}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <button
                                onClick={() => handleFilePreview(file)}
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 dark:bg-blue-900 dark:text-blue-200 dark:hover:bg-blue-800 transition-colors"
                                title="Preview File"
                              >
                                <span className="sm:hidden">👁️</span>
                                <span className="hidden sm:inline">Preview</span>
                              </button>
                              <button
                                onClick={() => handleDeleteFile(file)}
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition-colors"
                                title="Delete File"
                              >
                                <span className="sm:hidden">🗑️</span>
                                <span className="hidden sm:inline">Delete</span>
                              </button>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  )}
                </div>
              )}

              {/* Messages Tab */}
              {activeTab === 'messages' && (
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Messages ({messages.length})
                    </h3>
                  </div>
                  {messages.length === 0 ? (
                    <div className="text-center py-12">
                      <div className="text-6xl mb-4">💬</div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No messages found</h3>
                      <p className="text-gray-500 dark:text-gray-400">Messages from chat sessions will appear here.</p>
                    </div>
                  ) : (
                    <div className="max-h-96 overflow-y-auto admin-list-scroll pr-2">
                      <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                        {messages.map((message) => (
                          <li key={message.message_id} className="px-4 py-4 sm:px-6">
                            <div className="flex items-start justify-between">
                              <div className="flex items-start space-x-4 flex-1">
                                <div className="flex-shrink-0">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                    message.role === 'user'
                                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                      : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  }`}>
                                    {message.role === 'user' ? '👤 User' : '🤖 Assistant'}
                                  </span>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="text-sm text-gray-900 dark:text-white">
                                    <div className="line-clamp-3 mb-2">
                                      {message.content}
                                    </div>
                                  </div>
                                  <div className="text-sm text-gray-500 dark:text-gray-400">
                                    Session: <span className="font-medium">{message.session_id}</span> |
                                    User: <span className="font-medium">{message.user_id}</span>
                                  </div>
                                  <div className="text-xs text-gray-400 dark:text-gray-500">
                                    {formatDate(message.timestamp)}
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => handleDeleteMessage(message)}
                                  className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition-colors"
                                  title="Delete Message"
                                >
                                  <span className="sm:hidden">🗑️</span>
                                  <span className="hidden sm:inline">Delete</span>
                                </button>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Sync Tab */}
              {activeTab === 'sync' && (
                <div className="space-y-6">
                  <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                    <div className="px-4 py-5 sm:px-6">
                      <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                        Data Synchronization Status
                      </h3>
                      <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
                        Monitor and manage data consistency across MongoDB, S3, and Qdrant.
                      </p>
                    </div>
                  </div>

                  {/* Global Sync Status */}
                  <SyncStatusPanel userId="global" className="mb-6" />


                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Modals */}
      <AddUserModal
        isOpen={showAddUserModal}
        onClose={closeAllModals}
        onSubmit={handleCreateUser}
        loading={actionLoading}
      />

      <EditUserModal
        isOpen={showEditUserModal}
        user={selectedUser}
        onClose={closeAllModals}
        onSubmit={handleUpdateUser}
        loading={actionLoading}
      />

      <ChangePasswordModal
        isOpen={showChangePasswordModal}
        user={selectedUser}
        onClose={closeAllModals}
        onSubmit={handleChangePassword}
        loading={actionLoading}
      />

      <UserHistoryModal
        isOpen={showUserHistoryModal}
        user={selectedUser}
        onClose={closeAllModals}
      />

      <ConfirmationDialog
        isOpen={showDeleteConfirmation}
        title="Delete User"
        message={`Are you sure you want to delete user "${selectedUser?.user_id}"? This action cannot be undone and will also delete all associated sessions and messages.`}
        confirmText="Delete"
        cancelText="Cancel"
        onConfirm={handleDeleteUser}
        onCancel={closeAllModals}
        type="danger"
        loading={actionLoading}
      />

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* File Preview Modal - Lazy Loaded */}
      {previewModal.isOpen && (
        <Suspense fallback={
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2 text-gray-600 dark:text-gray-400">Loading preview...</p>
            </div>
          </div>
        }>
          <FilePreviewModal
            isOpen={previewModal.isOpen}
            onClose={closePreviewModal}
            fileKey={previewModal.fileKey}
            fileName={previewModal.fileName}
          />
        </Suspense>
      )}
    </div>
  );
};

export default AdminPage;
