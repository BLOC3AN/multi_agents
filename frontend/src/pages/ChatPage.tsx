import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useChannel } from '@/contexts/ChannelContext';
import { useSocket } from '@/hooks/useSocket';
import { useTheme } from '@/contexts/ThemeContext';

const ChatPage: React.FC = () => {
  const { user, logout } = useAuth();
  const { sessions, currentSession, messages, setCurrentSession } = useChannel();
  const { connected, authenticated, error, sendMessage, createSession, joinSession } = useSocket();
  const { theme, toggleTheme } = useTheme();

  const [messageInput, setMessageInput] = useState('');
  const [newSessionName, setNewSessionName] = useState('');
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();

    if (!messageInput.trim() || !authenticated) {
      return;
    }

    sendMessage(messageInput.trim(), currentSession?.session_id);
    setMessageInput('');
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

  const handleJoinSession = (sessionId: string) => {
    if (sessionId !== currentSession?.session_id) {
      joinSession(sessionId);
    }
  };

  const getConnectionStatus = () => {
    if (!connected) return { text: 'Disconnected', color: 'bg-red-500' };
    if (!authenticated) return { text: 'Connecting...', color: 'bg-yellow-500' };
    return { text: 'Connected', color: 'bg-green-500' };
  };

  const connectionStatus = getConnectionStatus();

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <div className="w-1/4 bg-card border-r border-border flex flex-col">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">💬 Chat Sessions</h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md hover:bg-accent"
                title="Toggle theme"
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
              <button
                onClick={logout}
                className="p-2 rounded-md hover:bg-accent text-muted-foreground"
                title="Logout"
              >
                🚪
              </button>
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center space-x-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${connectionStatus.color}`}></div>
            <span className="text-muted-foreground">{connectionStatus.text}</span>
          </div>

          {error && (
            <div className="mt-2 text-xs text-destructive bg-destructive/10 p-2 rounded">
              {error}
            </div>
          )}
        </div>

        {/* New Session */}
        <div className="p-4 border-b border-border">
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="Session name..."
              className="input flex-1 text-sm"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreateSession()}
              disabled={!authenticated || isCreatingSession}
            />
            <button
              onClick={handleCreateSession}
              disabled={!authenticated || !newSessionName.trim() || isCreatingSession}
              className="btn-primary px-3 py-2 text-sm disabled:opacity-50"
            >
              ➕
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4">
          {sessions.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-8">
              <div className="mb-2">📝 No sessions yet</div>
              <div>Create a new session to start chatting</div>
            </div>
          ) : (
            <div className="space-y-2">
              {sessions.map((session) => (
                <div
                  key={session.session_id}
                  onClick={() => handleJoinSession(session.session_id)}
                  className={`p-3 rounded-lg cursor-pointer transition-colors ${
                    currentSession?.session_id === session.session_id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-accent hover:bg-accent/80'
                  }`}
                >
                  <div className="font-medium text-sm truncate">
                    {session.session_name}
                  </div>
                  <div className="text-xs opacity-75 truncate mt-1">
                    {session.last_message_preview || 'No messages yet'}
                  </div>
                  <div className="text-xs opacity-60 mt-1">
                    {session.message_count} messages
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border bg-card">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold">🤖 Multi-Agent System Chat</h1>
              {currentSession && (
                <p className="text-sm text-muted-foreground mt-1">
                  {currentSession.session_name}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.display_name || user?.user_id}
              </span>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-muted-foreground">{connectionStatus.text}</span>
                <div className={`w-2 h-2 rounded-full ${connectionStatus.color}`}></div>
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!currentSession ? (
            <div className="text-center text-muted-foreground py-8">
              <h3 className="text-lg font-medium mb-2">👋 Welcome to Multi-Agent System!</h3>
              <p className="mb-4">Create a new session or select an existing one to start chatting</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-md mx-auto">
                <div className="card p-4 text-center">
                  <div className="text-2xl mb-2">🧮</div>
                  <div className="font-medium">Math & Science</div>
                  <div className="text-sm opacity-75">Solve equations, explain concepts</div>
                </div>
                <div className="card p-4 text-center">
                  <div className="text-2xl mb-2">✍️</div>
                  <div className="font-medium">Writing & Analysis</div>
                  <div className="text-sm opacity-75">Create content, analyze text</div>
                </div>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              <h3 className="text-lg font-medium mb-2">💬 {currentSession.session_name}</h3>
              <p>Start typing to begin your conversation with the AI agents</p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.message_id} className="space-y-4">
                  {/* User Message */}
                  {message.user_input && (
                    <div className="flex justify-end">
                      <div className="max-w-[80%] bg-primary text-primary-foreground rounded-lg px-4 py-2">
                        <div className="whitespace-pre-wrap">{message.user_input}</div>
                        <div className="text-xs opacity-75 mt-1">
                          {new Date(message.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Agent Response */}
                  {message.agent_response && (
                    <div className="flex justify-start">
                      <div className="max-w-[85%] bg-card border border-border rounded-lg px-4 py-2">
                        <div className="whitespace-pre-wrap">{message.agent_response}</div>
                        <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
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
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        {currentSession && (
          <div className="p-4 border-t border-border bg-card">
            <form onSubmit={handleSendMessage} className="flex space-x-2">
              <input
                type="text"
                placeholder="Ask me anything! I can solve math, write poems, explain concepts..."
                className="input flex-1"
                value={messageInput}
                onChange={(e) => setMessageInput(e.target.value)}
                disabled={!authenticated}
              />
              <button
                type="submit"
                disabled={!authenticated || !messageInput.trim()}
                className="btn-primary px-6 disabled:opacity-50"
              >
                🚀 Send
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatPage;
