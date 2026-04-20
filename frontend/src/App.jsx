import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuth } from './hooks/useAuth';

// Pages
import { Login } from './pages/Login';
import { Setup } from './pages/Setup';
import { Dashboard } from './pages/Dashboard';
import { RunDetail } from './pages/RunDetail';

// Protected Route Wrapper
function AuthGuard({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="min-h-screen bg-background flex items-center justify-center text-primary-fixed">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      {/* Toast Notification Provider */}
      <Toaster position="top-right" toastOptions={{
        className: 'font-sans text-sm',
        style: {
          background: '#171f33',
          color: '#dae2fd',
          border: '1px solid #444656',
        },
      }} />
      
      <Routes>
        <Route path="/" element={<Login />} />
        
        <Route path="/setup" element={
          <AuthGuard>
            <Setup />
          </AuthGuard>
        } />
        
        <Route path="/dashboard" element={
          <AuthGuard>
            <Dashboard />
          </AuthGuard>
        } />
        
        <Route path="/runs/:id" element={
          <AuthGuard>
            <RunDetail />
          </AuthGuard>
        } />
        
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
