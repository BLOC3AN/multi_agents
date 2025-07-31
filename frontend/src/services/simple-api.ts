/**
 * Simple API service for authentication and admin
 */
import axios from 'axios';
import type { LoginRequest, LoginResponse, AdminUser, AdminSession, AdminStats, ChatSession, ChatMessage } from '../types';

const API_BASE_URL = 'http://localhost:8000';

// Simple login function
export async function login(credentials: LoginRequest): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    console.log('🔐 Simple API login called with:', { user_id: credentials.user_id });
    
    const response = await axios.post(`${API_BASE_URL}/auth/login`, credentials, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });
    
    console.log('🔐 Simple API login response:', response.data);
    
    return {
      success: true,
      data: response.data,
    };
    
  } catch (error: any) {
    console.error('🔐 Simple API login error:', error);
    
    const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'Login failed';
    
    return {
      success: false,
      error: errorMessage,
    };
  }
}

// Simple logout function
export async function logout(): Promise<{ success: boolean; error?: string }> {
  try {
    await axios.post(`${API_BASE_URL}/auth/logout`, {}, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 5000,
    });
    
    return { success: true };
    
  } catch (error: any) {
    console.error('🔐 Simple API logout error:', error);
    return {
      success: false,
      error: error.message || 'Logout failed',
    };
  }
}

// Health check function
export async function healthCheck(): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, {
      timeout: 5000,
    });

    return {
      success: true,
      data: response.data,
    };

  } catch (error: any) {
    console.error('🔐 Simple API health check error:', error);
    return {
      success: false,
      error: error.message || 'Health check failed',
    };
  }
}

// Admin API functions
export async function getAdminUsers(): Promise<{ success: boolean; data?: AdminUser[]; error?: string }> {
  try {
    console.log('👥 Getting admin users...');

    const response = await axios.get(`${API_BASE_URL}/admin/users`, {
      timeout: 10000,
    });

    console.log('👥 Admin users response:', response.data);

    return {
      success: true,
      data: response.data.users,
    };

  } catch (error: any) {
    console.error('👥 Admin users error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get users',
    };
  }
}

export async function getAdminSessions(): Promise<{ success: boolean; data?: AdminSession[]; error?: string }> {
  try {
    console.log('💬 Getting admin sessions...');

    const response = await axios.get(`${API_BASE_URL}/admin/sessions`, {
      timeout: 10000,
    });

    console.log('💬 Admin sessions response:', response.data);

    return {
      success: true,
      data: response.data.sessions,
    };

  } catch (error: any) {
    console.error('💬 Admin sessions error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get sessions',
    };
  }
}

export async function getAdminStats(): Promise<{ success: boolean; data?: AdminStats; error?: string }> {
  try {
    console.log('📊 Getting admin stats...');

    const response = await axios.get(`${API_BASE_URL}/admin/stats`, {
      timeout: 10000,
    });

    console.log('📊 Admin stats response:', response.data);

    return {
      success: true,
      data: response.data.stats,
    };

  } catch (error: any) {
    console.error('📊 Admin stats error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get stats',
    };
  }
}

// User sessions API
export async function getUserSessions(userId: string): Promise<{ success: boolean; data?: ChatSession[]; error?: string }> {
  try {
    console.log('📋 Getting user sessions for:', userId);

    const response = await axios.get(`${API_BASE_URL}/user/${userId}/sessions`, {
      timeout: 10000,
    });

    console.log('📋 User sessions response:', response.data);

    return {
      success: true,
      data: response.data.sessions || [],
    };

  } catch (error: any) {
    console.error('📋 User sessions error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get sessions',
    };
  }
}

// Session messages API
export async function getSessionMessages(sessionId: string): Promise<{ success: boolean; data?: ChatMessage[]; error?: string }> {
  try {
    console.log('💬 Getting session messages for:', sessionId);

    const response = await axios.get(`${API_BASE_URL}/session/${sessionId}/messages`, {
      timeout: 10000,
    });

    console.log('💬 Session messages response:', response.data);

    return {
      success: true,
      data: response.data.messages || [],
    };

  } catch (error: any) {
    console.error('💬 Session messages error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get messages',
    };
  }
}

// Update session title API
export async function updateSessionTitle(sessionId: string, title: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('✏️ Updating session title:', sessionId, title);

    const response = await axios.put(`${API_BASE_URL}/session/${sessionId}/title`, {
      title: title
    }, {
      timeout: 5000,
    });

    console.log('✏️ Update title response:', response.data);

    return {
      success: true,
    };

  } catch (error: any) {
    console.error('✏️ Update title error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to update title',
    };
  }
}

// Delete session API
export async function deleteSession(sessionId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('🗑️ Deleting session:', sessionId);

    const response = await axios.delete(`${API_BASE_URL}/session/${sessionId}`, {
      timeout: 5000,
    });

    console.log('🗑️ Delete session response:', response.data);

    return {
      success: true,
    };

  } catch (error: any) {
    console.error('🗑️ Delete session error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete session',
    };
  }
}
