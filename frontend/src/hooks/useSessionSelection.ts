import { useRef, useState, useCallback } from 'react';
import type { ChatSession, ChatMessage } from '../types';

interface UseSessionSelectionProps {
  currentSession: ChatSession | null;
  setCurrentSession: (session: ChatSession | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setLoadingMessages: (loading: boolean) => void;
  messagesCache: React.MutableRefObject<Map<string, ChatMessage[]>>;
  getSessionMessages: (sessionId: string) => Promise<{ success: boolean; data?: ChatMessage[] }>;
}

export const useSessionSelection = ({
  currentSession,
  setCurrentSession,
  setMessages,
  setLoadingMessages,
  messagesCache,
  getSessionMessages,
}: UseSessionSelectionProps) => {
  const sessionSelectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [isSelectingSession, setIsSelectingSession] = useState(false);
  const lastSelectedRef = useRef<string | null>(null);

  const handleSessionSelect = useCallback(async (session: ChatSession, event?: React.MouseEvent) => {
    // Prevent event bubbling
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Don't reload if already selected or currently selecting
    if (currentSession?.session_id === session.session_id || isSelectingSession) {
      return;
    }

    // Prevent rapid successive clicks on different sessions
    if (lastSelectedRef.current === session.session_id) {
      return;
    }

    // Clear any pending selection
    if (sessionSelectTimeoutRef.current) {
      clearTimeout(sessionSelectTimeoutRef.current);
    }

    // Set selecting state to prevent multiple clicks
    setIsSelectingSession(true);
    lastSelectedRef.current = session.session_id;

    // Set session immediately for instant UI feedback
    setCurrentSession(session);

    // Check cache first
    const cached = messagesCache.current.get(session.session_id);
    if (cached) {
      console.log('📋 Loading from cache for session:', session.session_id, 'messages:', cached.length);
      setMessages(cached);
      setIsSelectingSession(false);

      // Reset last selected after a short delay
      sessionSelectTimeoutRef.current = setTimeout(() => {
        lastSelectedRef.current = null;
      }, 300);
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
      
      // Reset last selected after a short delay
      sessionSelectTimeoutRef.current = setTimeout(() => {
        lastSelectedRef.current = null;
      }, 300);
    }
  }, [
    currentSession?.session_id,
    isSelectingSession,
    setCurrentSession,
    setMessages,
    setLoadingMessages,
    messagesCache,
    getSessionMessages,
  ]);

  const cleanup = useCallback(() => {
    if (sessionSelectTimeoutRef.current) {
      clearTimeout(sessionSelectTimeoutRef.current);
      sessionSelectTimeoutRef.current = null;
    }
    setIsSelectingSession(false);
    lastSelectedRef.current = null;
  }, []);

  return {
    handleSessionSelect,
    isSelectingSession,
    cleanup,
  };
};
