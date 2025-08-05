import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface UserDropdownProps {
  onLogout: () => void;
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

const UserDropdown: React.FC<UserDropdownProps> = ({ onLogout, sidebarCollapsed = false, onToggleSidebar }) => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
        document.removeEventListener('keydown', handleKeyDown);
      };
    }
  }, [isOpen]);

  const handleThemeToggle = () => {
    toggleTheme();
    setIsOpen(false);
  };

  const handleAdminPanel = () => {
    navigate('/admin');
    setIsOpen(false);
  };

  const handleLogout = () => {
    setIsOpen(false);
    onLogout();
  };

  const getUserInitial = () => {
    return user?.display_name?.[0] || user?.user_id?.[0] || '?';
  };

  const getUserDisplayName = () => {
    return user?.display_name || user?.user_id || 'Unknown User';
  };

  return (
    <div className="relative user-dropdown-container" ref={dropdownRef}>
      {sidebarCollapsed ? (
        /* Collapsed View - Avatar and Toggle in same row */
        <div className="flex items-center justify-between" style={{ padding: '3px' }}>
          {/* Avatar Button */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            style={{
              width: 'calc(100vw / 7 * 0.15)',
              height: 'calc(100vw / 7 * 0.15)',
              padding: '2px'
            }}
            title={getUserDisplayName()}
          >
            <div
              className="bg-blue-600 rounded-full flex items-center justify-center text-white font-medium"
              style={{
                width: '100%',
                height: '100%',
                fontSize: 'calc(100vw / 7 * 0.1)'
              }}
            >
              {getUserInitial()}
            </div>
          </button>

          {/* Sidebar Toggle Button */}
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-600 dark:text-gray-400"
              style={{
                width: 'calc(100vw / 7 * 0.1)',
                height: 'calc(100vw / 7 * 0.1)'
              }}
              title="Expand Sidebar"
            >
              <svg
                style={{
                  width: '80%',
                  height: '80%'
                }}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          )}
        </div>
      ) : (
        /* Expanded View - Full User Info */
        <div style={{ padding: '3px' }}>
          {/* Avatar and Toggle in same row */}
          <div className="flex items-center justify-between mb-2">
            {/* Avatar Button */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="flex items-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors flex-1"
              style={{
                padding: '0.5px',
                gap: 'calc(100vw / 7 * 0.05)',
                marginRight: 'calc(100vw / 7 * 0.01)'
              }}
            >
              <div
                className="bg-blue-600 rounded-full flex items-center justify-center text-white font-medium"
                style={{
                  width: 'calc(100vw / 7 * 0.18)',
                  height: 'calc(100vw / 7 * 0.18)',
                  fontSize: 'calc(100vw / 7 * 0.12)'
                }}
              >
                {getUserInitial()}
              </div>
              <div className="flex-1 min-w-0 text-left">
                <div
                  className="font-semibold text-gray-900 dark:text-white truncate"
                  style={{ fontSize: 'calc(100vw / 7 * 0.065)' }}
                >
                  {getUserDisplayName()}
                </div>
                <div
                  className="text-gray-500 dark:text-gray-400"
                  style={{ fontSize: 'calc(100vw / 7 * 0.05)' }}
                >
                  {user?.role === 'editor' ? 'Editor' : user?.role === 'super_admin' ? 'Super Admin' : 'User'}
                </div>
              </div>
            </button>

            {/* Sidebar Toggle Button */}
            {onToggleSidebar && (
              <button
                onClick={onToggleSidebar}
                className="flex items-center justify-center hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-gray-600 dark:text-gray-400"
                style={{
                  width: 'calc(100vw / 7 * 0.18)',
                  height: 'calc(100vw / 7 * 0.18)',
                  padding: '4px'
                }}
                title="Collapse Sidebar"
              >
                <svg
                  style={{
                    width: '80%',
                    height: '80%'
                  }}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7M19 19l-7-7 7-7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="user-dropdown-menu bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-600 overflow-hidden animate-in slide-in-from-bottom-2 duration-200">
          {/* Theme Toggle */}
          <button
            onClick={handleThemeToggle}
            className="w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3 transition-colors"
          >
            <div className="w-5 h-5 flex items-center justify-center text-base">
              {theme === 'dark' ? '☀️' : '🌙'}
            </div>
            <div className="flex-1">
              <div className="font-medium">Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Change appearance
              </div>
            </div>
          </button>

          {/* Admin Panel - Only for editor and super_admin users */}
          {(user?.role === 'editor' || user?.role === 'super_admin') && (
            <button
              onClick={handleAdminPanel}
              className="w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 flex items-center space-x-3 transition-colors"
            >
              <div className="w-5 h-5 flex items-center justify-center text-base">
                🛠️
              </div>
              <div className="flex-1">
                <div className="font-medium">Admin Panel</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Manage system settings
                </div>
              </div>
            </button>
          )}

          {/* Divider */}
          <div className="border-t border-gray-200 dark:border-gray-600"></div>

          {/* Logout */}
          <button
            onClick={handleLogout}
            className="w-full px-4 py-3 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-3 transition-colors"
          >
            <div className="w-5 h-5 flex items-center justify-center text-base">
              🚪
            </div>
            <div className="flex-1">
              <div className="font-medium">Logout</div>
              <div className="text-xs text-red-500 dark:text-red-400 opacity-75">
                Sign out of your account
              </div>
            </div>
          </button>
        </div>
      )}
    </div>
  );
};

export default UserDropdown;
