/**
 * Simple API service for authentication and admin
 */
import axios from 'axios';
import type {
  LoginRequest,
  LoginResponse,
  AdminUser,
  AdminSession,
  AdminStats,
  ChatSession,
  ChatMessage,
  UserCreateRequest,
  UserUpdateRequest,
  PasswordChangeRequest,
  UserResponse,
  UserSessionsResponse,
  UserMessagesResponse
} from '../types';

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
      data: [],
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

// User Management API functions
export async function createUser(userData: UserCreateRequest): Promise<UserResponse> {
  try {
    console.log('👤 Creating user:', userData.user_id);

    const response = await axios.post(`${API_BASE_URL}/admin/users`, userData, {
      timeout: 10000,
    });

    console.log('👤 Create user response:', response.data);

    return {
      success: true,
      message: response.data.message,
      user: response.data.user,
    };

  } catch (error: any) {
    console.error('👤 Create user error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to create user',
    };
  }
}

export async function updateUser(userId: string, userData: UserUpdateRequest): Promise<UserResponse> {
  try {
    console.log('✏️ Updating user:', userId);

    const response = await axios.patch(`${API_BASE_URL}/admin/users/${userId}`, userData, {
      timeout: 10000,
    });

    console.log('✏️ Update user response:', response.data);

    return {
      success: true,
      message: response.data.message,
      user: response.data.user,
    };

  } catch (error: any) {
    console.error('✏️ Update user error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to update user',
    };
  }
}

export async function deleteUser(userId: string, force: boolean = false): Promise<UserResponse> {
  try {
    console.log('🗑️ Deleting user:', userId, 'force:', force);

    const response = await axios.delete(`${API_BASE_URL}/admin/users/${userId}`, {
      params: force ? { force: true } : {},
      timeout: 10000,
    });

    console.log('🗑️ Delete user response:', response.data);

    return {
      success: true,
      message: response.data.message,
    };

  } catch (error: any) {
    console.error('🗑️ Delete user error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete user',
    };
  }
}

export async function changeUserPassword(userId: string, passwordData: PasswordChangeRequest): Promise<UserResponse> {
  try {
    console.log('🔑 Changing password for user:', userId);

    const response = await axios.patch(`${API_BASE_URL}/admin/users/${userId}/password`, passwordData, {
      timeout: 10000,
    });

    console.log('🔑 Change password response:', response.data);

    return {
      success: true,
      message: response.data.message,
    };

  } catch (error: any) {
    console.error('🔑 Change password error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to change password',
    };
  }
}

export async function resetUserPassword(userId: string, newPassword: string): Promise<UserResponse> {
  try {
    console.log('🔑 Resetting password for user:', userId);

    const response = await axios.patch(`${API_BASE_URL}/admin/users/${userId}/reset-password`, {
      new_password: newPassword
    }, {
      timeout: 10000,
    });

    console.log('🔑 Reset password response:', response.data);

    return {
      success: true,
      message: response.data.message,
    };

  } catch (error: any) {
    console.error('🔑 Reset password error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to reset password',
    };
  }
}

export async function getUserSessionsAdmin(userId: string, limit: number = 50, offset: number = 0): Promise<UserSessionsResponse> {
  try {
    console.log('📋 Getting user sessions (admin):', userId);

    const response = await axios.get(`${API_BASE_URL}/admin/users/${userId}/sessions`, {
      params: { limit, offset },
      timeout: 10000,
    });

    console.log('📋 User sessions (admin) response:', response.data);

    return {
      success: true,
      sessions: response.data.sessions,
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
      user_id: response.data.user_id,
    };

  } catch (error: any) {
    console.error('📋 User sessions (admin) error:', error);
    return {
      success: false,
      sessions: [],
      total: 0,
      limit,
      offset,
      user_id: userId,
      error: error.response?.data?.detail || error.message || 'Failed to get user sessions',
    };
  }
}

export async function getUserMessagesAdmin(userId: string, limit: number = 50, offset: number = 0, sessionId?: string): Promise<UserMessagesResponse> {
  try {
    console.log('💬 Getting user messages (admin):', userId);

    const params: any = { limit, offset };
    if (sessionId) {
      params.session_id = sessionId;
    }

    const response = await axios.get(`${API_BASE_URL}/admin/users/${userId}/messages`, {
      params,
      timeout: 10000,
    });

    console.log('💬 User messages (admin) response:', response.data);

    return {
      success: true,
      messages: response.data.messages,
      total: response.data.total,
      limit: response.data.limit,
      offset: response.data.offset,
      user_id: response.data.user_id,
      session_id: response.data.session_id,
    };

  } catch (error: any) {
    console.error('💬 User messages (admin) error:', error);
    return {
      success: false,
      messages: [],
      total: 0,
      limit,
      offset,
      user_id: userId,
      session_id: sessionId,
      error: error.response?.data?.detail || error.message || 'Failed to get user messages',
    };
  }
}

export async function getUserCurrentPassword(userId: string): Promise<{ success: boolean; current_password?: string; has_password?: boolean; error?: string }> {
  try {
    console.log('🔍 Getting current password for user:', userId);

    const response = await axios.get(`${API_BASE_URL}/admin/users/${userId}/current-password`, {
      timeout: 10000,
    });

    console.log('🔍 Current password response:', response.data);

    return {
      success: true,
      current_password: response.data.current_password,
      has_password: response.data.has_password,
    };

  } catch (error: any) {
    console.error('🔍 Current password error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get current password',
    };
  }
}

// Admin Files API
export async function getAdminFiles(): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    console.log('📁 Getting all files (admin)');

    const response = await axios.get(`${API_BASE_URL}/admin/files`, {
      timeout: 10000,
    });

    console.log('📁 Admin files response:', response.data);

    return {
      success: true,
      data: response.data.files || [],
    };

  } catch (error: any) {
    console.error('📁 Admin files error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get files',
    };
  }
}

export async function deleteAdminFile(fileKey: string, userId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('🗑️ Deleting file (admin):', fileKey, 'for user:', userId);

    const response = await axios.delete(`${API_BASE_URL}/admin/files/${encodeURIComponent(fileKey)}`, {
      params: { user_id: userId },
      timeout: 10000,
    });

    console.log('🗑️ Admin delete file response:', response.data);

    return {
      success: true,
    };

  } catch (error: any) {
    console.error('🗑️ Admin delete file error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete file',
    };
  }
}

// Admin Messages API
export async function getAdminMessages(): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    console.log('💬 Getting all messages (admin)');

    const response = await axios.get(`${API_BASE_URL}/admin/messages`, {
      timeout: 10000,
    });

    console.log('💬 Admin messages response:', response.data);

    return {
      success: true,
      data: response.data.messages || [],
    };

  } catch (error: any) {
    console.error('💬 Admin messages error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to get messages',
    };
  }
}

export async function deleteAdminMessage(messageId: string): Promise<{ success: boolean; error?: string }> {
  try {
    console.log('🗑️ Deleting message (admin):', messageId);

    const response = await axios.delete(`${API_BASE_URL}/admin/messages/${messageId}`, {
      timeout: 10000,
    });

    console.log('🗑️ Admin delete message response:', response.data);

    return {
      success: true,
    };

  } catch (error: any) {
    console.error('🗑️ Admin delete message error:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message || 'Failed to delete message',
    };
  }
}
