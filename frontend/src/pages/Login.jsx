import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Code2, Loader2, ArrowRight } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export function Login() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if coming back from OAuth with token
    const token = searchParams.get('token');
    const isNew = searchParams.get('new_user') === 'true';
    
    if (token) {
      login(token, isNew);
    }
  }, [searchParams, login]);

  const handleGoogleLogin = () => {
    setLoading(true);
    // Redirect to backend OAuth flow
    window.location.href = `${import.meta.env.VITE_API_BASE || '/api/'}auth/google/`;
  };

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4 relative overflow-hidden">
      {/* Decorative ambient background glows */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-primary-container/5 rounded-full blur-[100px] pointer-events-none"></div>

      <div className="glass-panel max-w-md w-full p-8 rounded-lg relative z-10">
        <div className="flex justify-center mb-8">
          <div className="p-3 bg-surface-container relative rounded-xl border border-outline-variant/15 shadow-glow">
            <Code2 className="h-10 w-10 text-primary" />
          </div>
        </div>
        
        <h1 className="font-display text-2xl font-bold text-center text-on-surface mb-2">
          PIEMR Assignment AI Agent
        </h1>
        <p className="text-center text-on-surface-variant text-sm mb-10">
          Your assignments. Done automatically.
        </p>

        <button
          onClick={handleGoogleLogin}
          disabled={loading}
          className="w-full relative group overflow-hidden rounded-md gradient-primary text-on-primary-container p-0.5 transition-all duration-300 hover:shadow-bloom"
        >
          <div className="bg-surface-container/20 group-hover:bg-transparent transition-colors px-4 py-3 flex items-center justify-center gap-2">
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <>
                <svg className="w-5 h-5 bg-white rounded-full p-0.5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span className="font-medium text-sm">Continue with Google</span>
                <ArrowRight className="h-4 w-4 ml-2 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all" />
              </>
            )}
          </div>
        </button>
      </div>

      <div className="absolute bottom-8 text-on-surface-variant/40 text-xs font-mono">
        SYSTEM VER. 1.0.0 — INITIALIZING
      </div>
    </div>
  );
}
