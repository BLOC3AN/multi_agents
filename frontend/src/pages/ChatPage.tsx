import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useChannel } from '../contexts/ChannelContext';
import { useSocket } from '../hooks/useSocket';
import { getUserSessions, getSessionMessages, updateSessionTitle, deleteSession } from '../services/simple-api';
import MessageRenderer from '../components/MessageRenderer';
import TypingAnimation from '../components/TypingAnimation';
import UserDropdown from '../components/UserDropdown';

const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { sessions, currentSession, messages, setCurrentSession, ensureActiveSession, addSession, setMessages, updateSession, clearAll } = useChannel();
  const { authenticated, error, sendMessage, createSession } = useSocket();

  const [messageInput, setMessageInput] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [showDropdown, setShowDropdown] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesCache = useRef<Map<string, any[]>>(new Map());
  const previousUserIdRef = useRef<string | null>(null);

  // Load user sessions when user is authenticated
  useEffect(() => {
    const loadUserSessions = async () => {
      if (user?.user_id && authenticated && sessions.length === 0) {
        console.log('👤 Loading sessions for user:', user.user_id);
        setIsLoadingSessions(true);
        try {
          const response = await getUserSessions(user.user_id);
          if (response.success && response.data) {
            console.log('📋 Loaded sessions:', response.data.length);
            response.data.forEach(session => addSession(session));
          }
        } catch (error) {
          console.error('Failed to load user sessions:', error);
        } finally {
          setIsLoadingSessions(false);
        }
      }
    };

    loadUserSessions();
  }, [user?.user_id, authenticated, sessions.length, addSession, setIsLoadingSessions]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Clear typing animation when new message arrives
  useEffect(() => {
    if (messages.length > 0 && (pendingMessage || isTyping)) {
      console.log('📨 New message received, clearing pending state');
      setIsTyping(false);
      setPendingMessage(null);
    }
  }, [messages.length, pendingMessage, isTyping]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setShowDropdown(null);
    };

    if (showDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showDropdown]);

  // Clear all state when user changes (login/logout)
  useEffect(() => {
    const currentUserId = user?.user_id || null;
    const previousUserId = previousUserIdRef.current;

    // If user changed (different user ID or logout)
    if (previousUserId !== currentUserId) {
      console.log('👤 User changed:', { from: previousUserId, to: currentUserId });

      // Clear everything when user changes
      clearAll();
      messagesCache.current.clear();
      setPendingMessage(null);
      setIsTyping(false);
      setEditingSessionId(null);
      setEditingTitle('');
      setShowDropdown(null);

      if (!currentUserId) {
        console.log('🧹 User logged out - cleared all state');
      } else if (previousUserId) {
        console.log('🔄 User switched - cleared previous user state');
      }

      // Update ref
      previousUserIdRef.current = currentUserId;
    }
  }, [user?.user_id, clearAll]);

  const handleSessionSelect = async (session: any) => {
    // Don't reload if already selected
    if (currentSession?.session_id === session.session_id) return;

    // Set session immediately for instant UI feedback
    setCurrentSession(session);

    // Check cache first
    const cached = messagesCache.current.get(session.session_id);
    if (cached) {
      setMessages(cached);
      return;
    }

    // Show loading only for uncached sessions
    setLoadingMessages(true);

    try {
      // Load from API in background
      const response = await getSessionMessages(session.session_id);
      if (response.success && response.data) {
        setMessages(response.data);
        // Cache the messages
        messagesCache.current.set(session.session_id, response.data);
      }
    } catch (error) {
      console.error('Failed to load session messages:', error);
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleEditTitle = (sessionId: string, currentTitle: string) => {
    setEditingSessionId(sessionId);
    setEditingTitle(currentTitle);
  };

  const handleSaveTitle = async (sessionId: string) => {
    if (!editingTitle.trim()) return;

    try {
      const response = await updateSessionTitle(sessionId, editingTitle.trim());
      if (response.success) {
        updateSession(sessionId, { session_name: editingTitle.trim() });
        setEditingSessionId(null);
        setEditingTitle('');
      }
    } catch (error) {
      console.error('Failed to update session title:', error);
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle('');
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this session? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await deleteSession(sessionId);
      if (response.success) {
        // Clear cache
        messagesCache.current.delete(sessionId);

        // If this was the current session, clear it
        if (currentSession?.session_id === sessionId) {
          setCurrentSession(null);
          setMessages([]);
        }

        // Update sessions list (this would need to be handled by context)
        console.log('Session deleted successfully');
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    } finally {
      setShowDropdown(null);
    }
  };

  const handleLogout = () => {
    // Clear all channel state and cache
    clearAll();
    messagesCache.current.clear();

    // Clear pending states
    setPendingMessage(null);
    setIsTyping(false);
    setEditingSessionId(null);
    setEditingTitle('');
    setShowDropdown(null);

    console.log('🧹 Cleared all cache and state before logout');

    // Call logout
    logout();
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();

    if (!messageInput.trim() || !authenticated) {
      return;
    }

    const messageText = messageInput.trim();

    // Clear input immediately
    setMessageInput('');

    // Ensure we have an active session
    const activeSession = currentSession || ensureActiveSession();

    // Show pending message and typing animation immediately
    setPendingMessage(messageText);
    setIsTyping(true);

    console.log('🚀 Showing pending message:', messageText);
    console.log('🤖 Starting typing animation');

    // Force scroll to bottom after state update
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    // Send message
    sendMessage(messageText, activeSession.session_id);
  };

  const handleCreateSession = () => {
    if (!newSessionName.trim()) {
      return;
    }

    setIsCreatingSession(true);
    createSession(newSessionName.trim());
    setNewSessionName('');
    setIsCreatingSession(false);
  };





  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div
        className="border-token-border-light relative z-21 h-full shrink-0 overflow-hidden border-e max-md:hidden flex flex-col transition-all duration-300 ease-in-out"
        id="stage-slideover-sidebar"
        style={{
          width: 'var(--sidebar-width, 320px)',
          backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
        }}
      >
        {/* Sidebar Header */}
        <div className="p-4">
          <div className="flex items-center justify-center mb-4">
            <h2 className="text-lg font-semibold">💬 Chat Sessions</h2>
          </div>

          {error && (
            <div className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
              {error}
            </div>
          )}
        </div>

        {/* New Session */}
        <div className="p-4">
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="Session name..."
              className="flex-1 text-universal-14 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSession()}
              disabled={!authenticated || isCreatingSession}
            />
            <button
              onClick={handleCreateSession}
              disabled={!authenticated || !newSessionName.trim() || isCreatingSession}
              className="px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ➕
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4">
          {isLoadingSessions ? (
            <div className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <div>Loading sessions...</div>
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
              <div className="mb-2">📝 No sessions yet</div>
              <div>Create a new session to start chatting</div>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`group p-3 rounded-xl transition-all duration-200 ease-in-out cursor-pointer border border-transparent ${
                    currentSession?.session_id === session.session_id
                      ? 'bg-blue-600 text-white shadow-md border-blue-500'
                      : 'hover:bg-gray-100/50 dark:hover:bg-gray-700/50 text-gray-900 dark:text-white hover:shadow-sm hover:border-gray-200 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    {editingSessionId === session.session_id ? (
                      <div className="flex-1 flex items-center space-x-2">
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveTitle(session.session_id);
                            if (e.key === 'Escape') handleCancelEdit();
                          }}
                          onBlur={() => handleSaveTitle(session.session_id)}
                          className="flex-1 text-universal-14 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-medium"
                          autoFocus
                        />
                      </div>
                    ) : (
                      <>
                        <span
                          className="flex-1 select-none text-nowrap max-w-full overflow-hidden inline-block cursor-pointer session-title mask-fade-right"
                          onClick={() => handleSessionSelect(session)}
                        >
                          {session.session_name}
                        </span>
                        <div className="relative">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setShowDropdown(showDropdown === session.session_id ? null : session.session_id);
                            }}
                            className="ml-2 p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                            </svg>
                          </button>

                          {showDropdown === session.session_id && (
                            <div className="absolute right-0 top-8 w-32 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 z-50">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleEditTitle(session.session_id, session.session_name);
                                  setShowDropdown(null);
                                }}
                                className="w-full px-3 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg flex items-center space-x-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span>Edit Name</span>
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteSession(session.session_id);
                                }}
                                className="w-full px-3 py-2 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-b-lg flex items-center space-x-2"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                                <span>Delete</span>
                              </button>
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User Dropdown - Bottom of Sidebar */}
        <div className="mt-auto border-t border-gray-200 dark:border-gray-700 p-2">
          <UserDropdown onLogout={handleLogout} />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex justify-center bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-[786px] flex flex-col">
          {/* Header */}
          <div className="p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm mx-4 mt-4 border border-gray-200 dark:border-gray-700">
          <div className="text-center">
            <h1 className="text-xl font-semibold">🤖 Multi-Agent System Chat</h1>
            {currentSession && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {currentSession.session_name}
              </p>
            )}
          </div>
        </div>

          {/* Messages */}
          <div
            className="flex-1 overflow-y-auto p-4 mx-4 rounded-lg"
            style={{
              backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
            }}
          >
            <div className="space-y-4">
          {loadingMessages ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p className="text-universal-14">Loading messages...</p>
            </div>
          ) : !currentSession ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8">
              <h3 className="text-lg font-universal font-semibold mb-2 text-gray-900 dark:text-white">👋 Welcome to Multi-Agent System!</h3>
              <p className="mb-6 text-universal-14">Create a new session or select an existing one to start chatting</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md mx-auto">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-4 rounded-xl border border-blue-200 dark:border-blue-700 text-center hover:shadow-md transition-shadow">
                  <div className="text-2xl mb-2">🧮</div>
                  <div className="font-universal font-medium text-gray-900 dark:text-white">Math & Science</div>
                  <div className="text-universal-12 text-gray-600 dark:text-gray-400">Solve equations, explain concepts</div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-4 rounded-xl border border-purple-200 dark:border-purple-700 text-center hover:shadow-md transition-shadow">
                  <div className="text-2xl mb-2">✍️</div>
                  <div className="font-universal font-medium text-gray-900 dark:text-white">Writing & Analysis</div>
                  <div className="text-universal-12 text-gray-600 dark:text-gray-400">Create content, analyze text</div>
                </div>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8">
              <h3 className="text-lg font-universal font-semibold mb-2 text-gray-900 dark:text-white">💬 {currentSession.session_name}</h3>
              <p className="text-universal-14">Start typing to begin your conversation with the AI agents</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.message_id} className="space-y-4">
                  {/* User Message */}
                  {message.user_input && (
                    <div className="flex justify-end mb-4">
                      <div className="max-w-[80%] bg-white text-gray-900 rounded-2xl rounded-br-md px-4 py-3 shadow-sm border border-gray-200">
                        <MessageRenderer
                          content={message.user_input}
                          className="text-gray-900 text-base [&_p]:text-base [&_*]:text-gray-900"
                        />
                        <div className="text-xs opacity-75 mt-2 font-universal text-gray-600">
                          {new Date(message.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Agent Response */}
                  {message.agent_response && (
                    <div className="mb-4">
                      <div
                        className="w-full text-gray-900 dark:text-white rounded-2xl px-4 py-3 shadow-sm"
                        style={{
                          backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
                        }}
                      >
                        <MessageRenderer
                          content={message.agent_response}
                          className="text-gray-900 dark:text-white text-base [&_p]:text-base"
                        />
                        <div className="flex items-center justify-between mt-3 text-xs text-gray-500 dark:text-gray-400 font-universal">
                          <div className="flex items-center space-x-2">
                            {message.processing_time && (
                              <span>⚡ {message.processing_time}ms</span>
                            )}
                            {message.primary_intent && (
                              <span>🎯 {message.primary_intent}</span>
                            )}
                            {message.processing_mode && (
                              <span>🔄 {message.processing_mode}</span>
                            )}
                          </div>
                          <span>{new Date(message.created_at).toLocaleTimeString()}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Pending User Message */}
              {pendingMessage && (
                <div className="flex justify-end mb-4">
                  <div className="max-w-[80%] bg-white text-gray-900 rounded-2xl rounded-br-md px-4 py-3 shadow-sm border border-gray-200 opacity-80">
                    <MessageRenderer
                      content={pendingMessage}
                      className="text-gray-900 text-base [&_p]:text-base [&_*]:text-gray-900"
                    />
                    <div className="text-xs opacity-75 mt-2 font-universal text-gray-600 flex items-center space-x-1">
                      <span>{new Date().toLocaleTimeString()}</span>
                      <span className="text-blue-500">• Sending...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Typing Animation */}
              {isTyping && (
                <div className="mb-4">
                  <TypingAnimation />
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
            </div>
          </div>

          {/* Input - Always visible */}
          {true && (
            <div
              className="p-4 mx-4 mb-4 rounded-lg shadow-sm"
              style={{
                backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
              }}
            >
              <form onSubmit={handleSendMessage} className="flex space-x-3">
                <input
                  type="text"
                  placeholder="Ask me anything! I can solve math, write poems, explain concepts..."
                  className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-universal-14"
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  disabled={!authenticated}
                />
                <button
                  type="submit"
                  disabled={!authenticated || !messageInput.trim()}
                  className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  🚀 Send
                </button>
            </form>
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
