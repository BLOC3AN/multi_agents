import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface UserDropdownProps {
  onLogout: () => void;
}

const UserDropdown: React.FC<UserDropdownProps> = ({ onLogout }) => {
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
    <div className="relative" ref={dropdownRef}>
      {/* Avatar Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-3 p-3 w-full hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
      >
        <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-medium">
          {getUserInitial()}
        </div>
        <div className="flex-1 min-w-0 text-left">
          <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {getUserDisplayName()}
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">
            {user?.user_id === 'admin' ? 'Administrator' : 'User'}
          </div>
        </div>
        <svg 
          className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-600 z-50 overflow-hidden animate-in slide-in-from-bottom-2 duration-200">
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

          {/* Admin Panel - Only for admin users */}
          {user?.user_id === 'admin' && (
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
