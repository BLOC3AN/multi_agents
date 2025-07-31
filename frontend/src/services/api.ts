import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, ProcessRequest, ProcessResponse } from '@/types';

// Create axios instance with default config
const createApiInstance = (): AxiosInstance => {
  const instance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  instance.interceptors.request.use(
    (config) => {
      // Add auth token if available
      const user = localStorage.getItem('user');
      if (user) {
        try {
          const userData = JSON.parse(user);
          config.headers['X-User-ID'] = userData.user_id;
        } catch (error) {
          console.warn('Failed to parse user data from localStorage');
        }
      }

      console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
      return config;
    },
    (error) => {
      console.error('❌ Request interceptor error:', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  instance.interceptors.response.use(
    (response: AxiosResponse) => {
      console.log(`✅ API Response: ${response.status} ${response.config.url}`);
      return response;
    },
    (error) => {
      console.error('❌ API Error:', error.response?.status, error.response?.data || error.message);
      
      // Handle specific error cases
      if (error.response?.status === 401) {
        // Unauthorized - clear user data and redirect to login
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      
      return Promise.reject(error);
    }
  );

  return instance;
};

// Create API instance
const api = createApiInstance();

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
      const response = await this.api.request<T>(config);
      return {
        success: true,
        data: response.data,
      };
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || 'An error occurred';
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

// Export singleton instance
export const apiService = ApiService.getInstance();

// Export individual methods for convenience
export const {
  healthCheck,
  processMessage,
  getAgents,
  getMetrics,
  getSessions,
  createSession,
  getSessionHistory,
  updateSessionName,
} = apiService;
