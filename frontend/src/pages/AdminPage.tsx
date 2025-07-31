import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAdminUsers, getAdminSessions, getAdminStats } from '../services/simple-api';
import type { AdminUser, AdminSession, AdminStats } from '../types';

const AdminPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'stats' | 'users' | 'sessions'>('stats');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Data states
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [sessions, setSessions] = useState<AdminSession[]>([]);

  // Check if user is admin
  const isAdmin = user?.user_id === 'admin';

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
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Welcome, {user?.display_name || user?.user_id}
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
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
              <span className="ml-2 text-gray-600 dark:text-gray-400">Loading...</span>
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
                  <div className="px-4 py-5 sm:px-6">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                      Users ({users.length})
                    </h3>
                  </div>
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {users.map((user) => (
                      <li key={user.user_id} className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-3 ${
                              user.is_active 
                                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                            }`}>
                              {user.is_active ? '✅ Active' : '❌ Inactive'}
                            </span>
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {user.display_name || user.user_id}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                ID: {user.user_id} | Email: {user.email || 'N/A'}
                              </div>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Created: {formatDate(user.created_at)}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              Last Login: {formatDate(user.last_login)}
                            </div>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
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
    </div>
  );
};

export default AdminPage;
