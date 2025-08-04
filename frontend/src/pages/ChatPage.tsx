import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useChannel } from '../contexts/ChannelContext';
import { useSocket } from '../hooks/useSocket';
import { useSidebarWidth } from '../hooks/useSidebarWidth';
import { getUserSessions, getSessionMessages, updateSessionTitle, deleteSession } from '../services/simple-api';
import MessageRenderer from '../components/MessageRenderer';
import TypingAnimation from '../components/TypingAnimation';
import UserDropdown from '../components/UserDropdown';
import HistoryBlock from '../components/HistoryBlock';
import FilesBlock from '../components/FilesBlock';
import Logo from '../components/Logo';

const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { sessions, currentSession, messages, setCurrentSession, ensureActiveSession, addSession, addMessage, setMessages, updateSession, removeSession, clearAll } = useChannel();
  const { expandedWidthPx, collapsedWidthPx, sizes } = useSidebarWidth();

  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const messagesCache = useRef<Map<string, any[]>>(new Map());
  const { authenticated, error, sendMessage, createSession } = useSocket({ messagesCache });

  const [messageInput, setMessageInput] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoadingSessions, setIsLoadingSessions] = useState(false);

  // Manual reload sessions function for debugging
  const reloadSessions = async () => {
    if (user?.user_id && authenticated) {
      console.log('🔄 Manually reloading sessions for user:', user.user_id);
      setIsLoadingSessions(true);
      try {
        const response = await getUserSessions(user.user_id);
        console.log('📋 Manual reload API Response:', response);
        if (response.success && response.data) {
          console.log('📋 Manual reload - Loaded sessions:', response.data.length, response.data);
          // Clear existing sessions first
          clearAll();
          response.data.forEach(session => {
            console.log('➕ Manual reload - Adding session:', session);
            addSession(session);
          });
        } else {
          console.log('⚠️ Manual reload - No sessions data or API error:', response);
        }
      } catch (error) {
        console.error('Manual reload - Failed to load user sessions:', error);
      } finally {
        setIsLoadingSessions(false);
      }
    }
  };
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);

  const [isTyping, setIsTyping] = useState(false);
  const [showDropdown, setShowDropdown] = useState<string | null>(null);
  const [showMobileSidebar, setShowMobileSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
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

  // Clear typing animation when AI response arrives
  useEffect(() => {
    // Check if the latest message has an agent_response
    const latestMessage = messages[messages.length - 1];
    if (latestMessage && latestMessage.agent_response && isTyping) {
      console.log('📨 AI response received, clearing typing animation');
      setIsTyping(false);
    }
  }, [messages, isTyping]);

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

      setIsTyping(false);
      setEditingSessionId(null);
      setEditingTitle('');
      setShowDropdown(null);
      setIsSelectingSession(false);
      setDeletingSessionId(null);

      // Clear any pending session selection
      if (sessionSelectTimeoutRef.current) {
        clearTimeout(sessionSelectTimeoutRef.current);
        sessionSelectTimeoutRef.current = null;
      }

      if (!currentUserId) {
        console.log('🧹 User logged out - cleared all state');
      } else if (previousUserId) {
        console.log('🔄 User switched - cleared previous user state');
      }

      // Update ref
      previousUserIdRef.current = currentUserId;
    }
  }, [user?.user_id, clearAll]);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (sessionSelectTimeoutRef.current) {
        clearTimeout(sessionSelectTimeoutRef.current);
      }
    };
  }, []);

  // Debounce session selection to prevent rapid clicks
  const sessionSelectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isSelectingSession, setIsSelectingSession] = useState(false);

  const handleSessionSelect = async (session: any, event?: React.MouseEvent) => {
    // Prevent event bubbling
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Don't reload if already selected or currently selecting
    if (currentSession?.session_id === session.session_id || isSelectingSession) return;

    // Clear any pending selection
    if (sessionSelectTimeoutRef.current) {
      clearTimeout(sessionSelectTimeoutRef.current);
    }

    // Set selecting state to prevent multiple clicks
    setIsSelectingSession(true);

    // Set session immediately for instant UI feedback
    setCurrentSession(session);

    // Close mobile sidebar when session is selected
    setShowMobileSidebar(false);

    // Check cache first
    const cached = messagesCache.current.get(session.session_id);
    if (cached) {
      setMessages(cached);
      setIsSelectingSession(false);
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
      setIsSelectingSession(false);
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

  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);

  const handleDeleteSession = async (sessionId: string, event?: React.MouseEvent) => {
    // Prevent event bubbling
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Prevent multiple delete attempts
    if (deletingSessionId === sessionId) return;

    // Set deleting state for visual feedback
    setDeletingSessionId(sessionId);
    setShowDropdown(null);

    try {
      // Optimistic update: Remove from UI immediately
      const sessionToDelete = sessions.find(s => s.session_id === sessionId);
      if (sessionToDelete) {
        // Remove from sessions list immediately
        removeSession(sessionId);

        // Clear cache
        messagesCache.current.delete(sessionId);

        // If this was the current session, select another one or clear
        if (currentSession?.session_id === sessionId) {
          const remainingSessions = sessions.filter(s => s.session_id !== sessionId);
          if (remainingSessions.length > 0) {
            // Select the first remaining session
            const nextSession = remainingSessions[0];
            setCurrentSession(nextSession);

            // Load messages for next session
            const cached = messagesCache.current.get(nextSession.session_id);
            if (cached) {
              setMessages(cached);
            } else {
              setMessages([]);
              // Optionally load messages in background
              getSessionMessages(nextSession.session_id).then(response => {
                if (response.success && response.data) {
                  setMessages(response.data);
                  messagesCache.current.set(nextSession.session_id, response.data);
                }
              });
            }
          } else {
            // No sessions left
            setCurrentSession(null);
            setMessages([]);
          }
        }
      }

      // Call API to delete from backend
      const response = await deleteSession(sessionId);

      if (!response.success) {
        // If API call failed, revert the optimistic update
        console.error('Failed to delete session from backend:', response.error);

        // Reload sessions to restore state
        if (user?.user_id) {
          const sessionsResponse = await getUserSessions(user.user_id);
          if (sessionsResponse.success && sessionsResponse.data) {
            // This would need to be handled by updating the sessions in context
            // For now, we'll show an error
            alert('Failed to delete session. Please refresh the page.');
          }
        }
      } else {
        console.log('✅ Session deleted successfully');
      }

    } catch (error) {
      console.error('❌ Failed to delete session:', error);
      alert('Failed to delete session. Please try again.');

      // Optionally reload sessions to restore correct state
      if (user?.user_id) {
        const sessionsResponse = await getUserSessions(user.user_id);
        if (sessionsResponse.success && sessionsResponse.data) {
          // This would need proper context update
          console.log('Reloaded sessions after error');
        }
      }
    } finally {
      setDeletingSessionId(null);
    }
  };

  const handleLogout = () => {
    // Clear all channel state and cache
    clearAll();
    messagesCache.current.clear();

    // Clear pending states
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

    // Create user message immediately and add to messages
    const userMessage = {
      message_id: `user_msg_${Date.now()}`,
      session_id: activeSession.session_id,
      user_id: user?.user_id || '',
      user_input: messageText,
      agent_response: '', // Will be filled when response comes
      processing_time: 0,
      success: false,
      metadata: {},
      created_at: new Date().toISOString(),
    };

    console.log('💬 Adding user message immediately:', userMessage);

    // Add user message to state immediately
    addMessage(userMessage);

    // Update cache
    const currentMessages = messagesCache.current.get(activeSession.session_id) || [];
    messagesCache.current.set(activeSession.session_id, [...currentMessages, userMessage]);

    // Show typing animation for AI response
    setIsTyping(true);

    console.log('🚀 User message added, starting AI typing animation');

    // Force scroll to bottom after state update
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    // Send message to backend
    sendMessage(messageText, activeSession.session_id);
  };

  const handleCreateSession = () => {
    const trimmedName = newSessionName.trim();
    if (!trimmedName) {
      console.warn('Session name is empty');
      return;
    }

    console.log('🎯 Creating session with name:', trimmedName);
    setIsCreatingSession(true);

    // Create session with the custom name
    createSession(trimmedName);

    // Clear the input
    setNewSessionName('');

    // Reset creating state after a short delay to prevent rapid clicks
    setTimeout(() => {
      setIsCreatingSession(false);
    }, 1000);
  };
  const copyMessageContent = (content: string, messageId: string) => {
    navigator.clipboard.writeText(content).then(() => {
      setCopiedMessageId(messageId);
      setTimeout(() => {
        setCopiedMessageId(null);
      }, 2000);
    });
  };







  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Mobile Sidebar Overlay */}
      {showMobileSidebar && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 sm:hidden"
          onClick={() => setShowMobileSidebar(false)}
        />
      )}

      {/* Sidebar - Dynamic width based on collapsed state */}
      <div className={`sidebar-scrollbar relative h-full shrink-0 overflow-y-auto overflow-x-hidden border-r border-gray-200 dark:border-gray-700 flex flex-col bg-white dark:bg-gray-800 max-sm:w-full max-sm:fixed max-sm:z-50 max-sm:shadow-xl transition-all duration-300 ${
        showMobileSidebar ? 'max-sm:translate-x-0' : 'max-sm:-translate-x-full'
      }`}
      style={{
        width: sidebarCollapsed ? collapsedWidthPx : expandedWidthPx,
        minWidth: sidebarCollapsed ? collapsedWidthPx : expandedWidthPx
      }}
      >
        {/* Logo Section */}
        <div className="border-b border-gray-200 dark:border-gray-700" style={{ padding: sizes.padding.large }}>
          <div className="flex items-center justify-center">
            <Logo
              size={sidebarCollapsed ? 'large' : 'medium'}
              showText={!sidebarCollapsed}
              style={{ gap: sidebarCollapsed ? '0' : sizes.gap.small }}
              onClick={sidebarCollapsed ? () => setSidebarCollapsed(false) : undefined}
            />
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="m-4 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded">
            {error}
          </div>
        )}

        {/* New Session */}
        <div className="border-b border-gray-200 dark:border-gray-700" style={{ padding: sidebarCollapsed ? sizes.padding.medium : sizes.padding.xlarge }}>
          {sidebarCollapsed ? (
            /* Collapsed New Session - Just Icon */
            <div className="flex items-center justify-center">
              <button
                onClick={() => {
                  setSidebarCollapsed(false);
                  setTimeout(() => handleCreateSession(), 100);
                }}
                disabled={!authenticated || isCreatingSession}
                className="flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50"
                style={{
                  width: sizes.button.xxlarge,
                  height: sizes.button.xxlarge
                }}
                title="Create new session - Click to expand"
              >
                {isCreatingSession ? (
                  <div
                    className="animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
                    style={{
                      width: '60%',
                      height: '60%'
                    }}
                  ></div>
                ) : (
                  <svg
                    style={{
                      width: '70%',
                      height: '70%'
                    }}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    className="text-gray-600 dark:text-gray-400"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                )}
              </button>
            </div>
          ) : (
            /* Expanded New Session - Full Input */
          <div className="flex" style={{ gap: sizes.gap.small }}>
            <input
              type="text"
              placeholder="New session..."
              className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              style={{
                padding: `${sizes.gap.medium} ${sizes.gap.large}`,
                fontSize: sizes.font.small,
                minHeight: sizes.button.large
              }}
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSession()}
              disabled={!authenticated || isCreatingSession}
            />
            <button
              onClick={handleCreateSession}
              disabled={!authenticated || !newSessionName.trim() || isCreatingSession}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              style={{
                padding: sizes.gap.medium,
                fontSize: sizes.font.medium,
                minWidth: sizes.button.xlarge,
                minHeight: sizes.button.xlarge
              }}
            >
              {isCreatingSession ? (
                <div
                  className="animate-spin rounded-full border-2 border-white border-t-transparent"
                  style={{
                    width: sizes.button.small,
                    height: sizes.button.small
                  }}
                ></div>
              ) : (
                '➕'
              )}
            </button>
          </div>
          )}
        </div>

        {/* Files Block - Directly above History Block */}
        <div style={{ padding: sidebarCollapsed ? sizes.padding.small : `${sizes.padding.medium} ${sizes.padding.xlarge}` }}>
          <FilesBlock
            userId={user?.user_id || ''}
            collapsed={sidebarCollapsed}
            onExpandSidebar={() => setSidebarCollapsed(false)}
            sizes={sizes}
          />
        </div>

        {/* History Block - Directly below Files Block */}
        <div className="history-block-container" style={{
          padding: sidebarCollapsed ? sizes.padding.small : `${sizes.padding.medium} ${sizes.padding.xlarge}`,
          position: 'relative'
        }}>
          {isLoadingSessions ? (
            <div className="flex items-center justify-center h-32 text-center text-gray-500 dark:text-gray-400">
              <div>
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mx-auto mb-2"></div>
                <div className="text-sm">Loading sessions...</div>
              </div>
            </div>
          ) : (
            <HistoryBlock
              sessions={sessions}
              currentSession={currentSession}
              onSessionSelect={handleSessionSelect}
              onEditTitle={handleEditTitle}
              onDeleteSession={handleDeleteSession}
              editingSessionId={editingSessionId}
              editingTitle={editingTitle}
              setEditingTitle={setEditingTitle}
              onSaveTitle={handleSaveTitle}
              onCancelEdit={handleCancelEdit}
              showDropdown={showDropdown}
              setShowDropdown={setShowDropdown}
              deletingSessionId={deletingSessionId}
              isSelectingSession={isSelectingSession}
              collapsed={sidebarCollapsed}
              onExpandSidebar={() => setSidebarCollapsed(false)}
              sizes={sizes}
            />
          )}
        </div>

        {/* Spacer to push blocks above User Block */}
        <div className="flex-1"></div>

        {/* User Dropdown - Bottom of Sidebar - Fixed Position */}
        <div className="user-block border-t border-gray-200 dark:border-gray-700 relative z-50 bg-white dark:bg-gray-800 flex-shrink-0 mt-auto" style={{ padding: '0.5px' }}>
          <UserDropdown
            onLogout={handleLogout}
            sidebarCollapsed={sidebarCollapsed}
            onToggleSidebar={() => setSidebarCollapsed(!sidebarCollapsed)}
          />
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900 overflow-hidden h-full min-w-0">
        {/* Mobile Header */}
        <div className="sm:hidden flex items-center justify-between p-4 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setShowMobileSidebar(true)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-lg font-semibold truncate">
            {currentSession?.session_name || 'Multi-Agent Chat'}
          </h1>
          <div className="w-10" /> {/* Spacer for centering */}
        </div>

        {/* Chat Content */}
        <div className="flex-1 flex justify-center overflow-hidden">
          <div className="w-full max-w-[900px] xl:max-w-[1000px] flex flex-col min-w-0 h-full px-3 lg:px-4 xl:px-6">


            {/* Messages */}
            <div
              className="flex-1 overflow-y-auto overflow-x-hidden p-4 lg:p-6 mx-0 lg:mx-4 rounded-none lg:rounded-lg mt-3 lg:mt-4"
              style={{
                backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
              }}
            >
            <div className="space-y-4 lg:space-y-6 min-w-0">
          {loadingMessages ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
              <p className="text-sm font-light">Loading messages...</p>
            </div>
          ) : !currentSession ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8 lg:py-12">
              <h3 className="text-xl lg:text-2xl font-bold mb-3 lg:mb-4 text-gray-900 dark:text-white">👋 Welcome!</h3>
              <p className="mb-6 lg:mb-8 text-base lg:text-lg font-light">Create a new session or select an existing one to start chatting</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 lg:gap-6 max-w-lg lg:max-w-xl mx-auto">
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-5 lg:p-6 rounded-xl border border-blue-200 dark:border-blue-700 text-center hover:shadow-lg transition-all duration-200 hover:scale-105">
                  <div className="text-3xl lg:text-4xl mb-3 lg:mb-4">🧮</div>
                  <div className="font-semibold text-lg lg:text-xl text-gray-900 dark:text-white mb-2">Math & Science</div>
                  <div className="text-sm lg:text-base font-light text-gray-600 dark:text-gray-400">Solve equations, explain concepts</div>
                </div>
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-5 lg:p-6 rounded-xl border border-purple-200 dark:border-purple-700 text-center hover:shadow-lg transition-all duration-200 hover:scale-105">
                  <div className="text-3xl lg:text-4xl mb-3 lg:mb-4">✍️</div>
                  <div className="font-semibold text-lg lg:text-xl text-gray-900 dark:text-white mb-2">Writing & Analysis</div>
                  <div className="text-sm lg:text-base font-light text-gray-600 dark:text-gray-400">Create content, analyze text</div>
                </div>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-gray-600 dark:text-gray-400 py-8 lg:py-12">
              <h3 className="text-xl lg:text-2xl font-bold mb-3 lg:mb-4 text-gray-900 dark:text-white">💬 {currentSession.session_name}</h3>
              <p className="text-base lg:text-lg font-light">Start typing to begin your conversation with the AI agents</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.message_id} className="space-y-4">
                  {/* User Message */}
                  {message.user_input && (
                    <div className="flex justify-end mb-4 lg:mb-6">
                      <div className="max-w-[85%] lg:max-w-[75%] xl:max-w-[70%] bg-gray-100/50 dark:bg-gray-700/50 text-gray-900 dark:text-white rounded-2xl rounded-br-md px-4 lg:px-5 py-3 lg:py-4 shadow-sm border border-gray-200 dark:border-gray-600 overflow-hidden">
                        <MessageRenderer
                          content={message.user_input}
                          className="text-gray-900 dark:text-white text-base lg:text-lg font-light [&_p]:text-base lg:[&_p]:text-lg [&_p]:font-light [&_*]:text-gray-900 dark:[&_*]:text-white [&_strong]:font-semibold [&_b]:font-semibold [&_h1]:font-bold [&_h2]:font-bold [&_h3]:font-bold [&_h4]:font-bold [&_h5]:font-bold [&_h6]:font-bold"
                        />
                      </div>
                    </div>
                  )}

                  {/* Agent Response */}
                  {message.agent_response && (
                    <div className="mb-4 lg:mb-6">
                      <div
                        className="w-full text-gray-900 dark:text-white rounded-2xl px-4 lg:px-5 py-3 lg:py-4 shadow-sm overflow-hidden"
                        style={{
                          backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
                        }}
                      >
                        <MessageRenderer
                          content={message.agent_response}
                          className="text-gray-900 dark:text-white text-base lg:text-lg font-light [&_p]:text-base lg:[&_p]:text-lg [&_p]:font-light [&_strong]:font-semibold [&_b]:font-semibold [&_h1]:font-bold [&_h2]:font-bold [&_h3]:font-bold [&_h4]:font-bold [&_h5]:font-bold [&_h6]:font-bold"
                        />
                      </div>
                      {/* Copy Message Button and Processing Time */}
                      <div className="flex items-center justify-between mt-3 lg:mt-4">
                        <div className="flex items-center space-x-3 lg:space-x-4 text-sm lg:text-base text-gray-500 dark:text-gray-400">
                          {message.processing_time && (
                            <span>⚡ {(message.processing_time / 1000).toFixed(1)}s</span>
                          )}
                          {message.primary_intent && (
                            <span>🎯 {message.primary_intent}</span>
                          )}
                          {message.processing_mode && (
                            <span>🔄 {message.processing_mode}</span>
                          )}
                        </div>
                        <button
                          onClick={() => copyMessageContent(message.agent_response || '', message.message_id)}
                          className="p-2 lg:p-2.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors group"
                          title={copiedMessageId === message.message_id ? "Copied!" : "Copy message"}
                        >
                          {copiedMessageId === message.message_id ? (
                            <svg className="w-5 h-5 lg:w-6 lg:h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                            </svg>
                          ) : (
                            <svg className="w-5 h-5 lg:w-6 lg:h-6 text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                          )}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}



              {/* Typing Animation */}
              {isTyping && (
                <div className="mb-4 lg:mb-6">
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
                className="p-4 lg:p-6 mx-0 lg:mx-4 mb-4 lg:mb-6 rounded-none lg:rounded-lg shadow-sm"
                style={{
                  backgroundColor: 'var(--bg-elevated-secondary, #f8f9fa)'
                }}
              >
                <form onSubmit={handleSendMessage} className="flex space-x-3 lg:space-x-4">
                  <input
                    type="text"
                    placeholder="Ask me anything! I can solve math, write poems, explain concepts..."
                    className="flex-1 px-4 lg:px-5 py-3 lg:py-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-base lg:text-lg"
                    value={messageInput}
                    onChange={(e) => setMessageInput(e.target.value)}
                    disabled={!authenticated}
                  />
                  <button
                    type="submit"
                    disabled={!authenticated || !messageInput.trim()}
                    className="px-6 lg:px-8 py-3 lg:py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-base lg:text-lg"
                  >
                    🚀 Send
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
