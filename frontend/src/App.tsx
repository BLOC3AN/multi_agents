import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { ChannelProvider } from './contexts/ChannelContext';
import ProtectedRoute from './components/ProtectedRoute';

// Lazy load pages for code splitting
const LoginPage = lazy(() => import('./pages/LoginPage'));
const ChatPage = lazy(() => import('./pages/ChatPage'));
const AdminPage = lazy(() => import('./pages/AdminPage'));
const SyntaxTest = lazy(() => import('./components/SyntaxTest'));
const LaTeXTest = lazy(() => import('./components/LaTeXTest'));



// Loading component
const LoadingSpinner: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ChannelProvider>
          <Router>
            <div className="h-screen max-h-screen overflow-hidden bg-background text-foreground">
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  {/* Public routes */}
                  <Route
                    path="/login"
                    element={
                      <ProtectedRoute requireAuth={false}>
                        <LoginPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Protected routes */}
                  <Route
                    path="/chat"
                    element={
                      <ProtectedRoute>
                        <ChatPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="/admin"
                    element={
                      <ProtectedRoute requireAdmin={true}>
                        <AdminPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Test routes */}
                  <Route
                    path="/syntax-test"
                    element={<SyntaxTest />}
                  />
                  <Route
                    path="/latex-test"
                    element={<LaTeXTest />}
                  />





                  {/* Default redirect */}
                  <Route path="/" element={<Navigate to="/chat" replace />} />

                  {/* Catch all route */}
                  <Route path="*" element={<Navigate to="/chat" replace />} />
                </Routes>
              </Suspense>
            </div>
          </Router>
        </ChannelProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
