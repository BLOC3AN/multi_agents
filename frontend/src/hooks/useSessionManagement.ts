import { useState, useCallback, useRef } from 'react';
import type { ChatSession, ChatMessage } from '../types';
import { deleteSession as deleteSessionAPI, getSessionMessages, getUserSessions } from '../services/simple-api';

interface UseSessionManagementProps {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  setCurrentSession: (session: ChatSession | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  removeSession: (sessionId: string) => void;
  messagesCache: React.MutableRefObject<Map<string, ChatMessage[]>>;
  userId?: string;
}

export const useSessionManagement = ({
  sessions,
  currentSession,
  setCurrentSession,
  setMessages,
  removeSession,
  messagesCache,
  userId,
}: UseSessionManagementProps) => {
  const [deletingSessionId, setDeletingSessionId] = useState<string | null>(null);
  const [operationInProgress, setOperationInProgress] = useState(false);

  const deleteSession = useCallback(async (sessionId: string, event?: React.MouseEvent) => {
    // Prevent event bubbling
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }

    // Prevent multiple operations
    if (deletingSessionId === sessionId || operationInProgress) return;

    setDeletingSessionId(sessionId);
    setOperationInProgress(true);

    try {
      // Find session to delete
      const sessionToDelete = sessions.find(s => s.session_id === sessionId);
      if (!sessionToDelete) {
        console.warn('Session not found in local state');
        return;
      }

      // Optimistic update: Remove from UI immediately
      removeSession(sessionId);
      messagesCache.current.delete(sessionId);

      // Handle current session change
      if (currentSession?.session_id === sessionId) {
        const remainingSessions = sessions.filter(s => s.session_id !== sessionId);
        
        if (remainingSessions.length > 0) {
          // Select the next best session (first in list)
          const nextSession = remainingSessions[0];
          setCurrentSession(nextSession);
          
          // Load messages for next session
          const cached = messagesCache.current.get(nextSession.session_id);
          if (cached) {
            setMessages(cached);
          } else {
            setMessages([]);
            // Load messages in background
            try {
              const response = await getSessionMessages(nextSession.session_id);
              if (response.success && response.data) {
                setMessages(response.data);
                messagesCache.current.set(nextSession.session_id, response.data);
              }
            } catch (error) {
              console.error('Failed to load next session messages:', error);
            }
          }
        } else {
          // No sessions left
          setCurrentSession(null);
          setMessages([]);
        }
      }

      // Call API to delete from backend
      const response = await deleteSessionAPI(sessionId);
      
      if (!response.success) {
        console.error('Failed to delete session from backend:', response.error);
        
        // Revert optimistic update by reloading sessions
        if (userId) {
          const sessionsResponse = await getUserSessions(userId);
          if (sessionsResponse.success && sessionsResponse.data) {
            // Note: This would need proper context integration
            console.log('Should reload sessions from server');
          }
        }
        
        throw new Error(response.error || 'Failed to delete session');
      }

      console.log('✅ Session deleted successfully');
      
    } catch (error) {
      console.error('❌ Failed to delete session:', error);
      
      // Show user-friendly error
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete session';
      
      // In a real app, you might want to use a toast notification instead of alert
      if (typeof window !== 'undefined') {
        alert(`Error: ${errorMessage}. Please refresh the page if needed.`);
      }
      
    } finally {
      setDeletingSessionId(null);
      setOperationInProgress(false);
    }
  }, [
    sessions,
    currentSession,
    deletingSessionId,
    operationInProgress,
    removeSession,
    setCurrentSession,
    setMessages,
    messagesCache,
    userId,
  ]);

  const isDeleting = useCallback((sessionId: string) => {
    return deletingSessionId === sessionId;
  }, [deletingSessionId]);

  const cleanup = useCallback(() => {
    setDeletingSessionId(null);
    setOperationInProgress(false);
  }, []);

  return {
    deleteSession,
    isDeleting,
    deletingSessionId,
    operationInProgress,
    cleanup,
  };
};
