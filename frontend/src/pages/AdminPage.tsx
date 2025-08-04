import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  getAdminUsers,
  getAdminSessions,
  getAdminStats,
  createUser,
  updateUser,
  deleteUser,
  changeUserPassword
} from '../services/simple-api';
import type { AdminUser, AdminSession, AdminStats, UserCreateRequest, UserUpdateRequest, PasswordChangeRequest } from '../types';
import AddUserModal from '../components/AddUserModal';
import EditUserModal from '../components/EditUserModal';
import ChangePasswordModal from '../components/ChangePasswordModal';
import UserHistoryModal from '../components/UserHistoryModal';
import ConfirmationDialog from '../components/ConfirmationDialog';
import Toast from '../components/Toast';

const AdminPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'sessions'>('stats');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [sessions, setSessions] = useState<AdminSession[]>([]);

  // Modal states
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showEditUserModal, setShowEditUserModal] = useState(false);
  const [showChangePasswordModal, setShowChangePasswordModal] = useState(false);
  const [showUserHistoryModal, setShowUserHistoryModal] = useState(false);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Check if user is admin
  const isAdmin = user?.role === 'admin';

  // Handle navigation back to chat
  const handleBackToChat = () => {
    navigate('/chat');
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin, activeTab]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      if (activeTab === 'stats') {
        const response = await getAdminStats();
        if (response.success && response.data) {
          setStats(response.data);
        } else {
          setError(response.error || 'Failed to load stats');
        }
      } else if (activeTab === 'users') {
        const response = await getAdminUsers();
        if (response.success && response.data) {
          setUsers(response.data);
        } else {
          setError(response.error || 'Failed to load users');
        }
      } else if (activeTab === 'sessions') {
        const response = await getAdminSessions();
        if (response.success && response.data) {
          setSessions(response.data);
        } else {
          setError(response.error || 'Failed to load sessions');
        }
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
      const response = await deleteUser(selectedUser.user_id);
      if (response.success) {
        showToast('User deleted successfully!', 'success');
        loadData(); // Refresh user list
        setShowDeleteConfirmation(false);
        setSelectedUser(null);
      } else {
        showToast(response.error || 'Failed to delete user', 'error');
      }
    } catch (error) {
      showToast('An unexpected error occurred', 'error');
    } finally {
      setActionLoading(false);
    }
  };

  const handleChangePassword = async (userId: string, passwordData: PasswordChangeRequest) => {
    setActionLoading(true);
    try {
      const response = await changeUserPassword(userId, passwordData);
      if (response.success) {
        showToast('Password changed successfully!', 'success');
      } else {
        showToast(response.error || 'Failed to change password', 'error');
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
            You need admin privileges to access this page.
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
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">👥</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Users</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.total_users}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">💬</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Sessions</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.total_sessions}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">📝</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Messages</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.total_messages}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                    <div className="p-5">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">🔥</span>
                        <div>
                          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Recent (24h)</p>
                          <p className="text-lg font-medium text-gray-900 dark:text-white">{stats.recent_sessions_24h}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Users Tab */}
              {activeTab === 'users' && (
                <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
                  <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Users ({users.length})
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
                                user.role === 'admin'
                                  ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                  : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                              }`}>
                                {user.role === 'admin' ? '👑 Admin' : '👤 User'}
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
                            {user.user_id !== 'admin' && (
                              <button
                                onClick={() => openDeleteConfirmation(user)}
                                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 dark:bg-red-900 dark:text-red-200 dark:hover:bg-red-800 transition-colors"
                                title="Delete User"
                              >
                                <span className="sm:hidden">🗑️</span>
                                <span className="hidden sm:inline">🗑️ Delete</span>
                              </button>
                            )}
                          </div>
                        </div>
                      </li>
                      ))}
                    </ul>
                  )}
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
    </div>
  );
};

export default AdminPage;
