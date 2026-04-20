import React from 'react';
import { Link } from 'react-router-dom';
import { Settings, LogOut, Code2 } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export function Navbar() {
  const { logout } = useAuth();

  return (
    <nav className="border-b border-outline-variant/15 bg-surface-container-low/50 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center gap-2">
            <Code2 className="h-6 w-6 text-primary" />
            <span className="font-display font-semibold text-lg tracking-tight">PIEMR Agent</span>
          </div>
          
          <div className="hidden md:flex flex-1 justify-center">
            <div className="flex space-x-1 font-mono text-xs tracking-wider">
              <Link to="/dashboard" className="px-4 py-2 rounded-md hover:bg-surface-bright/20 text-on-surface-variant hover:text-on-surface transition-colors">
                HOME / DASHBOARD
              </Link>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Link to="/setup" className="p-2 rounded-full hover:bg-surface-bright/20 text-on-surface-variant hover:text-primary transition-colors">
              <Settings className="h-5 w-5" />
            </Link>
            <button onClick={logout} className="p-2 rounded-full hover:bg-surface-bright/20 text-on-surface-variant hover:text-error transition-colors">
              <LogOut className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
