import React, { useState, useMemo, useEffect, useRef } from 'react';
import type { ChatSession } from '../types';

interface HistoryBlockProps {
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  onSessionSelect: (session: ChatSession, event?: React.MouseEvent) => void;
  onEditTitle: (sessionId: string, currentTitle: string) => void;
  onDeleteSession: (sessionId: string, event?: React.MouseEvent) => void;
  editingSessionId: string | null;
  editingTitle: string;
  setEditingTitle: (title: string) => void;
  onSaveTitle: (sessionId: string) => void;
  onCancelEdit: () => void;
  showDropdown: string | null;
  setShowDropdown: (sessionId: string | null) => void;
  deletingSessionId: string | null;
  isSelectingSession: boolean;
  collapsed?: boolean;
  onExpandSidebar?: () => void;
  sizes?: {
    padding: {
      small: string;
      medium: string;
      large: string;
      xlarge: string;
    };
    gap: {
      small: string;
      medium: string;
      large: string;
    };
    button: {
      small: string;
      medium: string;
      large: string;
      xlarge: string;
      xxlarge: string;
    };
    font: {
      small: string;
      medium: string;
    };
  };
}

const HistoryBlock: React.FC<HistoryBlockProps> = ({
  sessions,
  currentSession,
  onSessionSelect,
  onEditTitle,
  onDeleteSession,
  editingSessionId,
  editingTitle,
  setEditingTitle,
  onSaveTitle,
  onCancelEdit,
  showDropdown,
  setShowDropdown,
  deletingSessionId,
  isSelectingSession,
  collapsed = false,
  onExpandSidebar,
  sizes,
}) => {
  const [isDropdownHovered, setIsDropdownHovered] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const dropdownMenuRef = useRef<HTMLDivElement>(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });

  // Fallback sizes if not provided (for backward compatibility)
  const defaultSizes = {
    padding: {
      small: '2px',
      medium: '4px',
      large: '8px',
      xlarge: '10px',
    },
    gap: {
      small: '4px',
      medium: '5px',
      large: '6px',
    },
    button: {
      small: '8px',
      medium: '12px',
      large: '24px',
      xlarge: '30px',
      xxlarge: '50px',
    },
    font: {
      small: '8px',
      medium: '12px',
    },
  };

  const sizeValues = sizes || defaultSizes;

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      // Check if click is outside both the dropdown button and the dropdown menu
      if (
        dropdownRef.current && !dropdownRef.current.contains(target) &&
        dropdownMenuRef.current && !dropdownMenuRef.current.contains(target)
      ) {
        setShowDropdown(null);
      }
    };

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showDropdown, setShowDropdown]);

  // Auto-close dropdown after 5 seconds (unless hovered) - increased time to reduce jumping
  useEffect(() => {
    if (showDropdown && !isDropdownHovered) {
      const timer = setTimeout(() => {
        setShowDropdown(null);
      }, 5000);

      return () => clearTimeout(timer);
    }
  }, [showDropdown, isDropdownHovered, setShowDropdown]);

  // Sort sessions by creation time (newest first) and limit to 10 for preview
  const sortedSessions = useMemo(() => {
    return [...sessions].sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [sessions]);





  if (collapsed) {
    return (
      <div className="w-full flex flex-col items-center">
        {/* Collapsed History Icon Only */}
        <button
          onClick={() => onExpandSidebar && onExpandSidebar()}
          className="flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          style={{
            width: sizeValues.button.xxlarge,
            height: sizeValues.button.xxlarge,
            margin: `${sizeValues.padding.small} 0`
          }}
          title={`History (${sessions.length} sessions) - Click to expand`}
        >
          <svg
            style={{
              width: '80%',
              height: '80%'
            }}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="stroke-[2] text-gray-600 dark:text-gray-400"
          >
            <path
              d="M4.4999 3L4.4999 8H9.49988M4.4999 7.99645C5.93133 5.3205 8.75302 3.5 11.9999 3.5C16.6943 3.5 20.4999 7.30558 20.4999 12C20.4999 16.6944 16.6943 20.5 11.9999 20.5C7.6438 20.5 4.05303 17.2232 3.55811 13"
              stroke="currentColor"
            />
            <path
              d="M15 9L12 12V16"
              stroke="currentColor"
            />
          </svg>
        </button>
      </div>
    );
  }

  return (
    <div
      className="w-full flex flex-col bg-white dark:bg-gray-800 rounded-lg border border-transparent hover:border-gray-200 dark:hover:border-gray-600 transition-all duration-200"
      style={{
        minHeight: isCollapsed ? 'auto' : 'calc(100vh * 0.30)',
        maxHeight: isCollapsed ? 'auto' : 'calc(100vh * 0.3)'
      }}
    >
      {/* History Header */}
      <div
        className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 flex-shrink-0 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
        style={{ padding: sizeValues.padding.large }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div className="flex items-center" style={{ gap: sizeValues.padding.large }}>
          <svg
            style={{
              width: sizeValues.font.medium,
              height: sizeValues.font.medium
            }}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className="stroke-[2] text-gray-600 dark:text-gray-400"
          >
            <path
              d="M4.4999 3L4.4999 8H9.49988M4.4999 7.99645C5.93133 5.3205 8.75302 3.5 11.9999 3.5C16.6943 3.5 20.4999 7.30558 20.4999 12C20.4999 16.6944 16.6943 20.5 11.9999 20.5C7.6438 20.5 4.05303 17.2232 3.55811 13"
              stroke="currentColor"
            />
            <path
              d="M15 9L12 12V16"
              stroke="currentColor"
            />
          </svg>
          <h3
            className="font-medium text-gray-900 dark:text-gray-400"
            style={{ fontSize: sizeValues.font.medium }}
          >
            History
          </h3>
        </div>
        <div className="flex items-center" style={{ gap: sizeValues.gap.small }}>
          <div
            className="font-light text-gray-500 dark:text-gray-400"
            style={{ fontSize: sizeValues.font.small }}
          >
            ({sessions.length})
          </div>
          {/* Collapse/Expand Icon */}
          <svg
            style={{
              width: sizeValues.font.medium,
              height: sizeValues.font.medium
            }}
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            className={`stroke-[2] text-gray-400 transition-transform duration-200 ${
              isCollapsed ? 'rotate-180' : ''
            }`}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>

      {/* Sessions List Container - Collapsible and Scrollable */}
      {!isCollapsed && (
        <div
          className="overflow-y-auto overflow-x-visible history-sessions-scrollbar"
          style={{
            padding: '0.5px',
            height: 'calc(100vh * 0.25)', // Fixed height cho sessions list
            minHeight: 'calc(100vh * 0.25)'
          }}
        >
          {sessions.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center text-gray-500 dark:text-gray-400">
              <div>
                <div className="mb-2">📝 No sessions yet</div>
                <div
                  className="font-light"
                  style={{ fontSize: sizeValues.font.small }}
                >
                  Create a new session to start chatting
                </div>
              </div>
            </div>
          ) : (
            <div style={{ gap: sizeValues.padding.small }} className="flex flex-col">
              {sortedSessions.map((session) => (
                  <div
                    key={session.session_id}
                    className={`group rounded-lg transition-colors duration-150 ease-in-out border border-transparent px-3 py-2 ${
                      currentSession?.session_id === session.session_id
                        ? 'bg-gray-100/50 dark:bg-gray-700/50 text-gray-900 dark:text-white shadow-sm border-gray-200 dark:border-gray-600'
                        : 'hover:bg-gray-100/50 dark:hover:bg-gray-700/50 text-gray-900 dark:text-white hover:shadow-sm hover:border-gray-200 dark:hover:border-gray-600'
                    } ${isSelectingSession ? 'pointer-events-none opacity-75' : 'cursor-pointer'}`}
                    onClick={(e) => onSessionSelect(session, e)}
                  >
                  <div className="flex items-center justify-between w-full">
                    {editingSessionId === session.session_id ? (
                      <div className="flex-1 flex items-center">
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') onSaveTitle(session.session_id);
                            if (e.key === 'Escape') onCancelEdit();
                          }}
                          onBlur={() => onSaveTitle(session.session_id)}
                          className="flex-1 text-sm px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-normal"
                          autoFocus
                        />
                      </div>
                    ) : (
                      <>
                        <div className="truncate flex-1" title={session.title}>
                          <span className="text-sm font-normal" dir="auto">
                            {session.title}
                            {isSelectingSession && currentSession?.session_id === session.session_id && (
                              <div className="ml-2 inline-block animate-spin rounded-full h-3 w-3 border-b-2 border-current opacity-75"></div>
                            )}
                          </span>
                        </div>
                        <div className="relative session-item-container" ref={dropdownRef}>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              const rect = e.currentTarget.getBoundingClientRect();
                              setDropdownPosition({
                                top: rect.bottom + 4, // Xổ xuống, cách button 4px
                                left: rect.right + 4  // Kế bên button, cách 4px
                              });
                              setShowDropdown(showDropdown === session.session_id ? null : session.session_id);
                            }}
                            className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"
                            aria-label="Mở các tùy chọn session"
                          >
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" className="icon" aria-hidden="true">
                              <path d="M15.498 8.50159C16.3254 8.50159 16.9959 9.17228 16.9961 9.99963C16.9961 10.8271 16.3256 11.4987 15.498 11.4987C14.6705 11.4987 14 10.8271 14 9.99963C14.0002 9.17228 14.6706 8.50159 15.498 8.50159Z"></path>
                              <path d="M4.49805 8.50159C5.32544 8.50159 5.99689 9.17228 5.99707 9.99963C5.99707 10.8271 5.32555 11.4987 4.49805 11.4987C3.67069 11.4985 3 10.827 3 9.99963C3.00018 9.17239 3.6708 8.50176 4.49805 8.50159Z"></path>
                              <path d="M10.0003 8.50159C10.8276 8.50176 11.4982 9.17239 11.4984 9.99963C11.4984 10.827 10.8277 11.4985 10.0003 11.4987C9.17283 11.4987 8.50131 10.8271 8.50131 9.99963C8.50149 9.17228 9.17294 8.50159 10.0003 8.50159Z"></path>
                            </svg>
                          </button>

                          {showDropdown === session.session_id && (
                            <div
                              ref={dropdownMenuRef}
                              className="fixed bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-600 overflow-visible session-dropdown"
                              style={{
                                zIndex: 10001, // Higher than user-dropdown and sidebar
                                top: `${dropdownPosition.top}px`,
                                left: `${dropdownPosition.left}px`,
                                width: 'calc(100vw / 14)', // 1/2 sidebar width
                                minWidth: '120px' // Minimum width for readability
                              }}
                              onMouseEnter={() => setIsDropdownHovered(true)}
                              onMouseLeave={() => setIsDropdownHovered(false)}
                            >
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onEditTitle(session.session_id, session.title);
                                  setShowDropdown(null);
                                }}
                                className="w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-t-lg flex items-center space-x-3 transition-colors min-h-[44px]"
                              >
                                <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                </svg>
                                <span className="font-normal whitespace-nowrap">Edit Name</span>
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onDeleteSession(session.session_id, e);
                                }}
                                disabled={deletingSessionId === session.session_id}
                                className={`w-full px-4 py-3 text-left text-sm rounded-b-lg flex items-center space-x-3 transition-colors min-h-[44px] ${
                                  deletingSessionId === session.session_id
                                    ? 'text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-gray-800 cursor-not-allowed'
                                    : 'text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
                                }`}
                              >
                                {deletingSessionId === session.session_id ? (
                                  <>
                                    <div className="w-4 h-4 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600 flex-shrink-0"></div>
                                    <span className="font-normal whitespace-nowrap">Deleting...</span>
                                  </>
                                ) : (
                                  <>
                                    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                    </svg>
                                    <span className="font-normal whitespace-nowrap">Delete</span>
                                  </>
                                )}
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
      )}
    </div>
  );
};

export default HistoryBlock;
