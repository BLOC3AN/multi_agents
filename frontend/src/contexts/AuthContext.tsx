import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { User, AuthState, LoginRequest } from '../types';
import { login as apiLogin, logout as apiLogout } from '../services/simple-api';

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_USER'; payload: User }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'LOGOUT' };

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    case 'SET_USER':
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        loading: false,
        error: null,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        loading: false,
      };
    case 'LOGOUT':
      return {
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      };
    default:
      return state;
  }
};

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  loading: true,
  error: null,
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check for existing session on mount
  useEffect(() => {
    const checkExistingSession = () => {
      try {
        const savedUser = localStorage.getItem('user');
        if (savedUser) {
          const user = JSON.parse(savedUser);
          dispatch({ type: 'SET_USER', payload: user });
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        console.error('Error checking existing session:', error);
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    checkExistingSession();
  }, []);

  const login = async (credentials: LoginRequest) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      // Validate required fields
      if (!credentials.user_id || !credentials.password) {
        throw new Error('User ID and password are required');
      }

      console.log('🔐 Attempting login with:', { user_id: credentials.user_id });

      // Call authentication API
      const response = await apiLogin(credentials);

      console.log('🔐 Login response:', response);

      if (!response.success || !response.data?.user) {
        throw new Error(response.error || 'Authentication failed');
      }

      const user = response.data.user;

      // Save to localStorage
      localStorage.setItem('user', JSON.stringify(user));
      localStorage.setItem('auth_token', 'authenticated'); // Simple token for now

      dispatch({ type: 'SET_USER', payload: user });
      console.log('✅ Login successful for user:', user.user_id);
    } catch (error) {
      console.error('❌ Login error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Call logout API
      await apiLogout();
    } catch (error) {
      console.error('Logout API error:', error);
    } finally {
      // Always clear local storage and state
      localStorage.removeItem('user');
      localStorage.removeItem('auth_token');
      dispatch({ type: 'LOGOUT' });
    }
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
