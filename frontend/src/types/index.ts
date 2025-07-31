// User types
export interface User {
  user_id: string;
  display_name?: string;
  email?: string;
  created_at?: string;
  updated_at?: string;
  is_active: boolean;
  last_login?: string;
  preferences?: Record<string, any>;
}

// Authentication types
export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  error: string | null;
}

// Chat types
export interface ChatMessage {
  message_id: string;
  session_id: string;
  user_id: string;
  user_input: string;
  agent_response?: string;
  detected_intents?: IntentScore[];
  primary_intent?: string;
  processing_mode?: string;
  agent_results?: Record<string, any>;
  execution_summary?: Record<string, any>;
  created_at: string;
  processing_time?: number;
  errors?: string[];
  success: boolean;
  metadata?: Record<string, any>;
}

export interface ChatSession {
  session_id: string;
  user_id: string;
  session_name: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  last_message_preview: string;
  is_active: boolean;
}

export interface IntentScore {
  intent: string;
  confidence: number;
  reasoning?: string;
}

// Socket types
export interface SocketState {
  connected: boolean;
  authenticated: boolean;
  connecting: boolean;
  error: string | null;
}

// API types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface ProcessRequest {
  input: string;
  use_parallel?: boolean;
  session_id?: string;
}

export interface ProcessResponse {
  success: boolean;
  input: string;
  primary_intent?: string;
  processing_mode?: string;
  detected_intents?: IntentScore[];
  agent_results?: Record<string, any>;
  final_result?: string;
  execution_summary?: Record<string, any>;
  errors?: string[];
  processing_time: number;
}

// Theme types
export type Theme = 'light' | 'dark' | 'system';

export interface ThemeState {
  theme: Theme;
  systemTheme: 'light' | 'dark';
  resolvedTheme: 'light' | 'dark';
}

// Component props types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// Route types
export interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAuth?: boolean;
}
