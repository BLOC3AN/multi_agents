import React, { createContext, useContext, useReducer, useCallback } from 'react';
import { ChatSession, ChatMessage } from '@/types';

interface ChannelState {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
}

interface ChannelContextType extends ChannelState {
  setCurrentSession: (session: ChatSession | null) => void;
  addSession: (session: ChatSession) => void;
  updateSession: (sessionId: string, updates: Partial<ChatSession>) => void;
  removeSession: (sessionId: string) => void;
  addMessage: (message: ChatMessage) => void;
  setMessages: (messages: ChatMessage[]) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

const ChannelContext = createContext<ChannelContextType | undefined>(undefined);

type ChannelAction =
  | { type: 'SET_SESSIONS'; payload: ChatSession[] }
  | { type: 'SET_CURRENT_SESSION'; payload: ChatSession | null }
  | { type: 'ADD_SESSION'; payload: ChatSession }
  | { type: 'UPDATE_SESSION'; payload: { sessionId: string; updates: Partial<ChatSession> } }
  | { type: 'REMOVE_SESSION'; payload: string }
  | { type: 'SET_MESSAGES'; payload: ChatMessage[] }
  | { type: 'ADD_MESSAGE'; payload: ChatMessage }
  | { type: 'CLEAR_MESSAGES' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

const channelReducer = (state: ChannelState, action: ChannelAction): ChannelState => {
  switch (action.type) {
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    
    case 'ADD_SESSION':
      return {
        ...state,
        sessions: [action.payload, ...state.sessions],
      };
    
    case 'UPDATE_SESSION':
      return {
        ...state,
        sessions: state.sessions.map(session =>
          session.session_id === action.payload.sessionId
            ? { ...session, ...action.payload.updates }
            : session
        ),
        currentSession:
          state.currentSession?.session_id === action.payload.sessionId
            ? { ...state.currentSession, ...action.payload.updates }
            : state.currentSession,
      };
    
    case 'REMOVE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter(session => session.session_id !== action.payload),
        currentSession:
          state.currentSession?.session_id === action.payload ? null : state.currentSession,
      };
    
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    
    case 'ADD_MESSAGE':
      return {
        ...state,
        messages: [...state.messages, action.payload],
      };
    
    case 'CLEAR_MESSAGES':
      return { ...state, messages: [] };
    
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    default:
      return state;
  }
};

const initialState: ChannelState = {
  sessions: [],
  currentSession: null,
  messages: [],
  loading: false,
  error: null,
};

export const ChannelProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(channelReducer, initialState);

  const setCurrentSession = useCallback((session: ChatSession | null) => {
    dispatch({ type: 'SET_CURRENT_SESSION', payload: session });
  }, []);

  const addSession = useCallback((session: ChatSession) => {
    dispatch({ type: 'ADD_SESSION', payload: session });
  }, []);

  const updateSession = useCallback((sessionId: string, updates: Partial<ChatSession>) => {
    dispatch({ type: 'UPDATE_SESSION', payload: { sessionId, updates } });
  }, []);

  const removeSession = useCallback((sessionId: string) => {
    dispatch({ type: 'REMOVE_SESSION', payload: sessionId });
  }, []);

  const addMessage = useCallback((message: ChatMessage) => {
    dispatch({ type: 'ADD_MESSAGE', payload: message });
  }, []);

  const setMessages = useCallback((messages: ChatMessage[]) => {
    dispatch({ type: 'SET_MESSAGES', payload: messages });
  }, []);

  const clearMessages = useCallback(() => {
    dispatch({ type: 'CLEAR_MESSAGES' });
  }, []);

  const setLoading = useCallback((loading: boolean) => {
    dispatch({ type: 'SET_LOADING', payload: loading });
  }, []);

  const setError = useCallback((error: string | null) => {
    dispatch({ type: 'SET_ERROR', payload: error });
  }, []);

  const value: ChannelContextType = {
    ...state,
    setCurrentSession,
    addSession,
    updateSession,
    removeSession,
    addMessage,
    setMessages,
    clearMessages,
    setLoading,
    setError,
  };

  return (
    <ChannelContext.Provider value={value}>{children}</ChannelContext.Provider>
  );
};

export const useChannel = (): ChannelContextType => {
  const context = useContext(ChannelContext);
  if (context === undefined) {
    throw new Error('useChannel must be used within a ChannelProvider');
  }
  return context;
};
