import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { ApiResponse, ProcessRequest, ProcessResponse, LoginRequest, LoginResponse } from '../types';

// Create simple axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service class
export class ApiService {
  private static instance: ApiService;
  private api: AxiosInstance;

  private constructor() {
    this.api = api;
  }

  public static getInstance(): ApiService {
    if (!ApiService.instance) {
      ApiService.instance = new ApiService();
    }
    return ApiService.instance;
  }

  // Generic request method
  private async request<T = any>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response: AxiosResponse<T> = await this.api(config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'An error occurred';
      return {
        success: false,
        error: errorMessage,
      };
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/health',
    });
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    console.log('🔐 API login called with:', { user_id: credentials.user_id });
    try {
      const result = await this.request<LoginResponse>({
        method: 'POST',
        url: '/auth/login',
        data: credentials,
      });
      console.log('🔐 API login result:', result);
      return result;
    } catch (error) {
      console.error('🔐 API login error:', error);
      throw error;
    }
  }

  async logout(): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/auth/logout',
    });
  }

  // Process message through multi-agent system
  async processMessage(request: ProcessRequest): Promise<ApiResponse<ProcessResponse>> {
    return this.request<ProcessResponse>({
      method: 'POST',
      url: '/process',
      data: request,
    });
  }

  // Get available agents and intents
  async getAgents(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/agents',
    });
  }

  // Get system metrics
  async getMetrics(): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: '/metrics',
    });
  }

  // Chat session management (these would be added to backend later)
  async getSessions(userId: string): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: `/api/chat/sessions?user_id=${userId}`,
    });
  }

  async createSession(sessionName: string): Promise<ApiResponse> {
    return this.request({
      method: 'POST',
      url: '/api/chat/sessions',
      data: { session_name: sessionName },
    });
  }

  async getSessionHistory(sessionId: string): Promise<ApiResponse> {
    return this.request({
      method: 'GET',
      url: `/api/chat/history/${sessionId}`,
    });
  }

  async updateSessionName(sessionId: string, name: string): Promise<ApiResponse> {
    return this.request({
      method: 'PUT',
      url: `/api/chat/sessions/${sessionId}/name`,
      data: { name },
    });
  }
}

// Create service instance
const apiService = ApiService.getInstance();

// Export singleton instance
export { apiService };

// Export individual methods for convenience
export const healthCheck = () => apiService.healthCheck();
export const login = (credentials: LoginRequest) => apiService.login(credentials);
export const logout = () => apiService.logout();
export const processMessage = (request: ProcessRequest) => apiService.processMessage(request);
export const getAgents = () => apiService.getAgents();
export const getMetrics = () => apiService.getMetrics();
export const getSessions = (userId: string) => apiService.getSessions(userId);
export const createSession = (userId: string, sessionName?: string) => apiService.createSession(userId, sessionName);
export const getSessionHistory = (sessionId: string) => apiService.getSessionHistory(sessionId);
export const updateSessionName = (sessionId: string, newName: string) => apiService.updateSessionName(sessionId, newName);
