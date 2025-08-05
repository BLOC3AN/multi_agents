import React, { useState } from 'react';
import type { AdminUser, PasswordChangeRequest } from '../types';

interface ChangePasswordModalProps {
  isOpen: boolean;
  user: AdminUser | null;
  onClose: () => void;
  onSubmit: (userId: string, passwordData: PasswordChangeRequest) => Promise<void>;
  loading?: boolean;
}

const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({
  isOpen,
  user,
  onClose,
  onSubmit,
  loading = false,
}) => {
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [showPasswords, setShowPasswords] = useState({
    new_password: false,
    confirm_password: false,
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.new_password) {
      newErrors.new_password = 'New password is required';
    } else if (formData.new_password.length < 6) {
      newErrors.new_password = 'Password must be at least 6 characters long';
    }

    // No current password validation needed for admin reset

    if (!formData.confirm_password) {
      newErrors.confirm_password = 'Please confirm the password';
    } else if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!user || !validateForm()) {
      return;
    }

    try {
      await onSubmit(user.user_id, {
        current_password: '',
        new_password: formData.new_password
      });
      // Reset form on success
      setFormData({
        new_password: '',
        confirm_password: '',
      });
      setErrors({});
      onClose();
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const togglePasswordVisibility = (field: 'new_password' | 'confirm_password') => {
    setShowPasswords(prev => ({ ...prev, [field]: !prev[field] }));
  };

  if (!isOpen || !user) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        {/* Backdrop */}
        <div 
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity dark:bg-gray-900 dark:bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6 dark:bg-gray-800">
          <div className="absolute right-0 top-0 pr-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:bg-gray-800 dark:text-gray-500 dark:hover:text-gray-400"
            >
              <span className="sr-only">Close</span>
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="sm:flex sm:items-start">
            <div className="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-yellow-100 sm:mx-0 sm:h-10 sm:w-10 dark:bg-yellow-900/20">
              <span className="text-xl text-yellow-600 dark:text-yellow-400">🔑</span>
            </div>
            <div className="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left w-full">
              <h3 className="text-base font-semibold leading-6 text-gray-900 dark:text-white">
                Reset Password: {user.user_id}
              </h3>
              <div className="mt-2">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Set a new password for this user account. No current password required.
                </p>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">

            {/* New Password */}
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Password *
              </label>
              <div className="relative mt-1">
                <input
                  type={showPasswords.new_password ? 'text' : 'password'}
                  id="new_password"
                  value={formData.new_password}
                  onChange={(e) => handleInputChange('new_password', e.target.value)}
                  className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                    errors.new_password ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                  placeholder="Enter password"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('new_password')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm leading-5"
                >
                  <span className="text-gray-500 dark:text-gray-400">
                    {showPasswords.new_password ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              {errors.new_password && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.new_password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Confirm Password *
              </label>
              <div className="relative mt-1">
                <input
                  type={showPasswords.confirm_password ? 'text' : 'password'}
                  id="confirm_password"
                  value={formData.confirm_password}
                  onChange={(e) => handleInputChange('confirm_password', e.target.value)}
                  className={`block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white ${
                    errors.confirm_password ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''
                  }`}
                  placeholder="Confirm password"
                />
                <button
                  type="button"
                  onClick={() => togglePasswordVisibility('confirm_password')}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm leading-5"
                >
                  <span className="text-gray-500 dark:text-gray-400">
                    {showPasswords.confirm_password ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              {errors.confirm_password && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.confirm_password}</p>
              )}
            </div>

            {/* Password Requirements */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-md p-3">
              <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">Password Requirements</h4>
              <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
                <li className="flex items-center">
                  <span className={`mr-2 ${formData.new_password.length >= 6 ? 'text-green-500' : 'text-gray-400'}`}>
                    {formData.new_password.length >= 6 ? '✅' : '⭕'}
                  </span>
                  At least 6 characters long
                </li>
                <li className="flex items-center">
                  <span className={`mr-2 ${formData.new_password ? 'text-green-500' : 'text-gray-400'}`}>
                    {formData.new_password ? '✅' : '⭕'}
                  </span>
                  New password provided
                </li>
                <li className="flex items-center">
                  <span className={`mr-2 ${formData.new_password === formData.confirm_password && formData.confirm_password ? 'text-green-500' : 'text-gray-400'}`}>
                    {formData.new_password === formData.confirm_password && formData.confirm_password ? '✅' : '⭕'}
                  </span>
                  Passwords match
                </li>
              </ul>
            </div>

            {/* Actions */}
            <div className="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex w-full justify-center rounded-md bg-yellow-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-yellow-500 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2 sm:ml-3 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Resetting...
                  </>
                ) : (
                  'Reset Password'
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={loading}
                className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed dark:bg-gray-700 dark:text-white dark:ring-gray-600 dark:hover:bg-gray-600"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChangePasswordModal;
