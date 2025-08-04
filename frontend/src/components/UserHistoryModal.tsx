import React, { useState, useEffect } from 'react';
import type { AdminUser, AdminSession, ChatMessage } from '../types';
import { getUserSessionsAdmin, getUserMessagesAdmin } from '../services/simple-api';

interface UserHistoryModalProps {
  isOpen: boolean;
  user: AdminUser | null;
  onClose: () => void;
}

const UserHistoryModal: React.FC<UserHistoryModalProps> = ({
  isOpen,
  user,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'sessions' | 'messages'>('sessions');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Sessions data
  const [sessions, setSessions] = useState<AdminSession[]>([]);
  const [sessionsTotal, setSessionsTotal] = useState(0);
  const [sessionsPage, setSessionsPage] = useState(0);
  
  // Messages data
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [messagesTotal, setMessagesTotal] = useState(0);
  const [messagesPage, setMessagesPage] = useState(0);
  const [selectedSessionId, setSelectedSessionId] = useState<string | undefined>();

  const ITEMS_PER_PAGE = 20;

  const loadSessions = async (page: number = 0) => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUserSessionsAdmin(user.user_id, ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);
      
      if (response.success) {
        setSessions(response.sessions);
        setSessionsTotal(response.total);
        setSessionsPage(page);
      } else {
        setError(response.error || 'Failed to load sessions');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (page: number = 0, sessionId?: string) => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await getUserMessagesAdmin(user.user_id, ITEMS_PER_PAGE, page * ITEMS_PER_PAGE, sessionId);
      
      if (response.success) {
        setMessages(response.messages);
        setMessagesTotal(response.total);
        setMessagesPage(page);
        setSelectedSessionId(sessionId);
      } else {
        setError(response.error || 'Failed to load messages');
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && user) {
      if (activeTab === 'sessions') {
        loadSessions(0);
      } else {
        loadMessages(0, selectedSessionId);
      }
    }
  }, [isOpen, user, activeTab]);

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity dark:bg-gray-900 dark:bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl dark:bg-gray-800">
          {/* Header */}
          <div className="bg-white px-4 py-5 sm:px-6 dark:bg-gray-800">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/20">
                  <span className="text-xl text-blue-600 dark:text-blue-400">📊</span>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                    User History: {user.user_id}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    View sessions and messages for this user
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-gray-800 dark:text-gray-500 dark:hover:text-gray-400"
              >
                <span className="sr-only">Close</span>
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="px-4 sm:px-6 -mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('sessions')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'sessions'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                💬 Sessions ({sessionsTotal})
              </button>
              <button
                onClick={() => setActiveTab('messages')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'messages'
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                📝 Messages ({messagesTotal})
              </button>
            </nav>
          </div>

          {/* Content */}
          <div className="px-4 py-5 sm:p-6 max-h-96 overflow-y-auto">
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
                  onClick={() => activeTab === 'sessions' ? loadSessions(sessionsPage) : loadMessages(messagesPage, selectedSessionId)}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                >
                  🔄 Retry
                </button>
              </div>
            )}

            {!loading && !error && (
              <>
                {/* Sessions Tab */}
                {activeTab === 'sessions' && (
                  <div className="space-y-4">
                    {sessions.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        No sessions found for this user.
                      </div>
                    ) : (
                      sessions.map((session) => (
                        <div key={session.session_id} className="border border-gray-200 rounded-lg p-4 dark:border-gray-700">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mr-3 ${
                                session.is_active 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
                              }`}>
                                {session.is_active ? '🟢 Active' : '⚫ Inactive'}
                              </span>
                              <div>
                                <div className="text-sm font-medium text-gray-900 dark:text-white">
                                  {session.title || `Session ${session.session_id.slice(0, 8)}`}
                                </div>
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                  ID: {session.session_id} | Messages: {session.total_messages}
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
                              <button
                                onClick={() => {
                                  setActiveTab('messages');
                                  loadMessages(0, session.session_id);
                                }}
                                className="mt-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                              >
                                View Messages →
                              </button>
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}

                {/* Messages Tab */}
                {activeTab === 'messages' && (
                  <div className="space-y-4">
                    {/* Session Filter */}
                    <div className="flex items-center space-x-4 mb-4">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Filter by session:
                      </label>
                      <select
                        value={selectedSessionId || ''}
                        onChange={(e) => loadMessages(0, e.target.value || undefined)}
                        className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                      >
                        <option value="">All sessions</option>
                        {sessions.map((session) => (
                          <option key={session.session_id} value={session.session_id}>
                            {session.title || `Session ${session.session_id.slice(0, 8)}`}
                          </option>
                        ))}
                      </select>
                    </div>

                    {messages.length === 0 ? (
                      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                        No messages found for this user.
                      </div>
                    ) : (
                      messages.map((message) => (
                        <div key={message.message_id} className="border border-gray-200 rounded-lg p-4 dark:border-gray-700">
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                Session: {message.session_id.slice(0, 8)}... | {formatDate(message.created_at)}
                              </div>
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                message.success 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              }`}>
                                {message.success ? '✅ Success' : '❌ Error'}
                              </span>
                            </div>
                            <div>
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                User Input:
                              </div>
                              <div className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700 rounded p-2 mt-1">
                                {truncateText(message.user_input)}
                              </div>
                            </div>
                            {message.agent_response && (
                              <div>
                                <div className="text-sm font-medium text-gray-900 dark:text-white">
                                  Agent Response:
                                </div>
                                <div className="text-sm text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 rounded p-2 mt-1">
                                  {truncateText(message.agent_response)}
                                </div>
                              </div>
                            )}
                            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                              {message.primary_intent && (
                                <span>Intent: {message.primary_intent}</span>
                              )}
                              {message.processing_time && (
                                <span>Time: {message.processing_time}ms</span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Pagination */}
          {!loading && !error && (
            <div className="bg-gray-50 px-4 py-3 sm:px-6 dark:bg-gray-700">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-700 dark:text-gray-300">
                  {activeTab === 'sessions' ? (
                    <>Showing {sessionsPage * ITEMS_PER_PAGE + 1} to {Math.min((sessionsPage + 1) * ITEMS_PER_PAGE, sessionsTotal)} of {sessionsTotal} sessions</>
                  ) : (
                    <>Showing {messagesPage * ITEMS_PER_PAGE + 1} to {Math.min((messagesPage + 1) * ITEMS_PER_PAGE, messagesTotal)} of {messagesTotal} messages</>
                  )}
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => activeTab === 'sessions' ? loadSessions(sessionsPage - 1) : loadMessages(messagesPage - 1, selectedSessionId)}
                    disabled={activeTab === 'sessions' ? sessionsPage === 0 : messagesPage === 0}
                    className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-600 dark:border-gray-500 dark:text-white dark:hover:bg-gray-500"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => activeTab === 'sessions' ? loadSessions(sessionsPage + 1) : loadMessages(messagesPage + 1, selectedSessionId)}
                    disabled={activeTab === 'sessions' ? (sessionsPage + 1) * ITEMS_PER_PAGE >= sessionsTotal : (messagesPage + 1) * ITEMS_PER_PAGE >= messagesTotal}
                    className="px-3 py-1 text-sm bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-600 dark:border-gray-500 dark:text-white dark:hover:bg-gray-500"
                  >
                    Next
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserHistoryModal;
