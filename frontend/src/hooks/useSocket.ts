import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import type { SocketState, User, ChatMessage } from '../types';
import { useAuth } from '../contexts/AuthContext';
import { useChannel } from '../contexts/ChannelContext';

interface UseSocketReturn extends SocketState {
  sendMessage: (message: string, sessionId?: string) => void;
  createSession: (sessionName?: string) => void;
  joinSession: (sessionId: string) => void;
  disconnect: () => void;
  reconnect: () => void;
}

interface UseSocketProps {
  messagesCache?: React.MutableRefObject<Map<string, any[]>>;
}

export const useSocket = (props?: UseSocketProps): UseSocketReturn => {
  const { user, isAuthenticated } = useAuth();
  const { addMessage, setCurrentSession, addSession, setMessages, messages, currentSession } = useChannel();

  const socketRef = useRef<Socket | null>(null);
  // Use external cache if provided, otherwise create internal one
  const internalCache = useRef<Map<string, any[]>>(new Map());
  const messagesCache = props?.messagesCache || internalCache;

  const [socketState, setSocketState] = useState<SocketState>({
    connected: false,
    authenticated: false,
    connecting: false,
    error: null,
  });

  const updateSocketState = useCallback((updates: Partial<SocketState>) => {
    setSocketState(prev => ({ ...prev, ...updates }));
  }, []);

  // Initialize socket connection
  const initializeSocket = useCallback(() => {
    if (socketRef.current) {
      return; // Already initialized
    }

    const socketUrl = import.meta.env.VITE_SOCKETIO_URL || 'http://localhost:8001';
    
    updateSocketState({ connecting: true, error: null });
    
    const socket = io(socketUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    socketRef.current = socket;

    // Connection events
    socket.on('connect', () => {
      console.log('✅ Socket connected');
      updateSocketState({ connected: true, connecting: false, error: null });
      
      // Auto-authenticate if user is logged in
      if (user && isAuthenticated) {
        authenticateUser(user);
      }
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ Socket disconnected:', reason);
      updateSocketState({ 
        connected: false, 
        authenticated: false, 
        connecting: false,
        error: `Disconnected: ${reason}` 
      });
    });

    socket.on('connect_error', (error) => {
      console.error('❌ Socket connection error:', error);
      updateSocketState({ 
        connected: false, 
        connecting: false, 
        error: `Connection failed: ${error.message}` 
      });
    });

    // Authentication events
    socket.on('auth_success', (data) => {
      console.log('✅ Socket authentication successful', data);
      updateSocketState({ authenticated: true, error: null });
    });

    socket.on('auth_error', (data) => {
      console.error('❌ Socket authentication failed', data);
      updateSocketState({ authenticated: false, error: data.error });
    });

    // Session events
    socket.on('session_created', (data) => {
      console.log('✅ Session created', data);
      const session = {
        session_id: data.session_id,
        user_id: user?.user_id || '',
        session_name: data.session_name || data.title || `Chat ${data.session_id.substring(0, 8)}`,
        created_at: data.created_at || new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0,
        last_message_preview: '',
        is_active: true,
      };

      console.log('📝 Adding session with name:', session.session_name);
      addSession(session);
      setCurrentSession(session);
    });

    socket.on('session_joined', (data) => {
      console.log('✅ Session joined', data);
      const session = {
        session_id: data.session_id,
        user_id: user?.user_id || '',
        session_name: data.session_name || data.title || `Chat ${data.session_id.substring(0, 8)}`,
        created_at: data.created_at || new Date().toISOString(),
        updated_at: data.updated_at || new Date().toISOString(),
        message_count: data.message_count || 0,
        last_message_preview: data.last_message_preview || '',
        is_active: true,
      };

      console.log('🔗 Joined session with name:', session.session_name);
      setCurrentSession(session);
    });

    // Message events
    socket.on('message_response', (data) => {
      console.log('📨 Message response received', data);

      // Find the latest user message to update with AI response
      const currentMessages = messages || [];
      console.log('🔍 Looking for message to update in', currentMessages.length, 'messages');
      const latestUserMessage = [...currentMessages].reverse().find(msg =>
        msg.user_input && (!msg.agent_response || msg.agent_response.trim() === '') && msg.session_id === data.session_id
      );
      console.log('🎯 Found message to update:', latestUserMessage ? latestUserMessage.message_id : 'none');

      if (latestUserMessage) {
        // Update existing message with AI response
        const updatedMessage: ChatMessage = {
          ...latestUserMessage,
          agent_response: data.response,
          detected_intents: data.detected_intents,
          primary_intent: data.primary_intent,
          processing_mode: data.processing_mode,
          agent_results: data.agent_responses,
          execution_summary: data.execution_summary,
          processing_time: data.processing_time,
          errors: data.errors,
          success: data.status === 'success',
          metadata: data.metadata,
        };

        console.log('🔄 Updating existing message with AI response:', updatedMessage);

        // Update messages in state
        const updatedMessages = currentMessages.map(msg =>
          msg.message_id === latestUserMessage.message_id ? updatedMessage : msg
        );
        setMessages(updatedMessages);

        // Update cache using session_id from the message (not currentSession)
        messagesCache.current.set(data.session_id, updatedMessages);
        console.log('💾 Cache updated for session:', data.session_id, 'with', updatedMessages.length, 'messages');
      } else {
        // Fallback: create new complete message
        console.log('⚠️ No existing message found to update, creating new message');
        const message: ChatMessage = {
          message_id: data.message_id || `msg_${Date.now()}`,
          session_id: data.session_id,
          user_id: user?.user_id || '',
          user_input: data.user_input || '',
          agent_response: data.response,
          detected_intents: data.detected_intents,
          primary_intent: data.primary_intent,
          processing_mode: data.processing_mode,
          agent_results: data.agent_responses,
          execution_summary: data.execution_summary,
          created_at: data.timestamp || new Date().toISOString(),
          processing_time: data.processing_time,
          errors: data.errors,
          success: data.status === 'success',
          metadata: data.metadata,
        };

        console.log('➕ Adding new complete message:', message);
        addMessage(message);

        // Update cache for fallback case too
        const currentCachedMessages = messagesCache.current.get(data.session_id) || [];
        const updatedCachedMessages = [...currentCachedMessages, message];
        messagesCache.current.set(data.session_id, updatedCachedMessages);
        console.log('💾 Cache updated (fallback) for session:', data.session_id, 'with', updatedCachedMessages.length, 'messages');
      }
    });

    socket.on('processing_error', (data) => {
      console.error('❌ Processing error', data);
      updateSocketState({ error: data.error });
    });

    socket.on('error', (data) => {
      console.error('❌ Socket error', data);
      updateSocketState({ error: data.error });
    });

  }, [user, isAuthenticated, addMessage, setCurrentSession, addSession, updateSocketState]);

  // Authenticate user with socket
  const authenticateUser = useCallback((userData: User) => {
    if (!socketRef.current?.connected) {
      console.warn('Socket not connected, cannot authenticate');
      return;
    }

    console.log('🔐 Authenticating user with socket...', userData);
    socketRef.current.emit('authenticate', {
      user_id: userData.user_id,
      display_name: userData.display_name,
      email: userData.email,
    });
  }, []);

  // Send message
  const sendMessage = useCallback((message: string, sessionId?: string) => {
    if (!socketRef.current?.connected || !socketState.authenticated) {
      console.warn('Socket not connected or not authenticated');
      updateSocketState({ error: 'Not connected to server' });
      return;
    }

    const messageData: any = { message };
    if (sessionId) {
      messageData.session_id = sessionId;
    }

    console.log('📤 Sending message:', messageData);
    socketRef.current.emit('process_message', messageData);
  }, [socketState.authenticated, updateSocketState]);

  // Create session
  const createSession = useCallback((sessionName?: string) => {
    if (!socketRef.current?.connected || !socketState.authenticated) {
      console.warn('Socket not connected or not authenticated');
      return;
    }

    const sessionData: any = {};
    if (sessionName && sessionName.trim()) {
      sessionData.session_name = sessionName.trim();
      console.log('📝 Creating session with custom name:', sessionName.trim());
    } else {
      console.log('📝 Creating session with default name');
    }

    console.log('📝 Session data being sent:', sessionData);
    socketRef.current.emit('create_session', sessionData);
  }, [socketState.authenticated]);

  // Join session
  const joinSession = useCallback((sessionId: string) => {
    if (!socketRef.current?.connected || !socketState.authenticated) {
      console.warn('Socket not connected or not authenticated');
      return;
    }

    console.log('🔗 Joining session:', sessionId);
    socketRef.current.emit('join_session', { session_id: sessionId });
  }, [socketState.authenticated]);

  // Disconnect
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      updateSocketState({ 
        connected: false, 
        authenticated: false, 
        connecting: false, 
        error: null 
      });
    }
  }, [updateSocketState]);

  // Reconnect
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      initializeSocket();
    }, 1000);
  }, [disconnect, initializeSocket]);

  // Initialize socket when user is authenticated
  useEffect(() => {
    if (isAuthenticated && user) {
      initializeSocket();
    } else {
      disconnect();
    }

    return () => {
      // Cleanup on unmount
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    };
  }, [isAuthenticated, user, initializeSocket, disconnect]);

  // Authenticate when socket connects and user is available
  useEffect(() => {
    if (socketState.connected && user && isAuthenticated && !socketState.authenticated) {
      authenticateUser(user);
    }
  }, [socketState.connected, socketState.authenticated, user, isAuthenticated, authenticateUser]);

  return {
    ...socketState,
    sendMessage,
    createSession,
    joinSession,
    disconnect,
    reconnect,
  };
};
