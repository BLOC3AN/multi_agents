import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const LoginPage: React.FC = () => {
  const { login, loading, error } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    user_id: '',
    display_name: '',
    email: '',
  });
  const [formError, setFormError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setFormError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.user_id.trim()) {
      setFormError('User ID is required');
      return;
    }

    try {
      await login({
        user_id: formData.user_id.trim(),
        display_name: formData.display_name.trim() || undefined,
        email: formData.email.trim() || undefined,
      });

      navigate('/chat');
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-gray-900">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
            🤖 Multi-Agent System
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            Sign in to access the AI chat system
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {(error || formError) && (
            <div className="rounded-md bg-red-50 border border-red-200 p-4 dark:bg-red-900/20 dark:border-red-800">
              <div className="text-sm text-red-600 dark:text-red-400">
                {formError || error}
              </div>
            </div>
          )}

          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="user_id" className="sr-only">
                User ID
              </label>
              <input
                id="user_id"
                name="user_id"
                type="text"
                required
                className="input rounded-t-md"
                placeholder="User ID"
                value={formData.user_id}
                onChange={handleInputChange}
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="display_name" className="sr-only">
                Display Name
              </label>
              <input
                id="display_name"
                name="display_name"
                type="text"
                className="input rounded-none"
                placeholder="Display Name (optional)"
                value={formData.display_name}
                onChange={handleInputChange}
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="email" className="sr-only">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                className="input rounded-b-md"
                placeholder="Email (optional)"
                value={formData.email}
                onChange={handleInputChange}
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-2 px-4 text-sm font-medium disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2 inline-block"></div>
                  Connecting...
                </>
              ) : (
                '🚀 Connect to Multi-Agent System'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
